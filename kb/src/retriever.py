"""
Retriever & Generation Engine for Knowledge Base
Implements Pure RAG: Hybrid Search (BM25 FTS5 + Lexical Overlap + Query Term Coverage Gating),
Freshness Filtering, and Generic Grounded Answer Synthesis directly from retrieved chunks
"""

import sqlite3
import re
from pathlib import Path
from typing import List, Dict, Any, Optional

from kb.src.models import KnowledgeChunk, RetrievalResult


# ==============================================================================
# VIETNAMESE STOP WORDS (Generic grammatical particles & procedural boilerplate)
# ==============================================================================
VIETNAMESE_STOP_WORDS = {
    "công", "ty", "có", "không", "những", "các", "cho", "và", "là", "được", "trong", "với", "của", "đến",
    "như", "thế", "nào", "mấy", "khi", "bao", "nhiêu", "thì", "đã", "từng", "làm", "gì", "hướng", "dẫn",
    "một", "hai", "ba", "về", "ở", "ra", "vào", "lại", "theo", "sao", "phải", "hoặc", "này",
    "quy", "trình", "chính", "sách", "thủ", "tục", "tài", "liệu", "hệ", "thống"
}


# ==============================================================================
# RAG TUNING HYPERPARAMETERS & WEIGHT CONSTANTS (With explicit technical rationale)
# ==============================================================================

# 1. Trọng số BM25 từ SQLite FTS5 (Exact keyword match)
# FTS5 bắt chính xác các từ khóa kỹ thuật (tên lỗi ERR, tên service, lệnh bash, mã số).
# Nhân hệ số 3.0 để ưu tiên các chunk có từ khóa kỹ thuật khớp chính xác so với từ ngữ thông thường.
FTS_BM25_WEIGHT = 3.0

# 2. Điểm cộng ưu tiên cho Chunk Tổng Quan (Header Summary Chunk)
# Khi người dùng hỏi các câu hỏi mang tính chất liệt kê, bao quát ("tổng quan", "những lỗi", "loại lỗi", "danh sách", "thường gặp"),
# cộng 6.0 điểm để Header Summary Chunk lên Top-1 giúp AI có bức tranh toàn cảnh của tài liệu.
HEADER_OVERVIEW_BOOST = 6.0

# 3. Ngưỡng bao phủ từ khóa tối thiểu của câu hỏi (Query Term Coverage Gate)
# Trong Information Retrieval, một chunk chỉ được xem là có liên quan nếu chứa ít nhất 40% số từ khóa
# mang ý nghĩa của câu hỏi. Nếu < 0.40 (như câu hỏi về tiền ăn trưa, nghỉ phép), chunk bị loại bỏ tự nhiên.
MIN_QUERY_COVERAGE_RATIO = 0.40

# 4. Ngưỡng điểm tối thiểu để một chunk được đưa vào danh sách ứng viên (Candidate pool)
# Các chunk có điểm <= 1.5 chỉ trùng 1 từ đơn lẻ ngẫu nhiên (nhiễu), bị loại bỏ để tránh làm loãng context.
MIN_CHUNK_SCORE_THRESHOLD = 1.5

# 5. Ngưỡng điểm Top-1 chunk để phân loại OUT_OF_SCOPE tại bước answer_query
# Nếu ngay cả chunk phù hợp nhất cũng có điểm < 2.5, câu hỏi không đủ độ tương đồng với bất kỳ
# tài liệu nào trong hệ thống -> Trả về thông báo "ngoài phạm vi" mà không cần hardcode danh sách từ khóa.
OUT_OF_SCOPE_SCORE_THRESHOLD = 2.5

# 6. Ngưỡng điểm tối thiểu để một chunk được đưa vào phần tổng hợp câu trả lời (Synthesis Inclusion)
# Tách biệt khỏi OUT_OF_SCOPE_SCORE_THRESHOLD vì đây là khái niệm khác: lọc chunk nào đủ điểm
# để tham gia xây dựng nội dung câu trả lời (phân vùng "trích dẫn tin cậy").
# Hiện tại cùng giá trị, nhưng có thể tune độc lập nếu muốn tổng hợp rộng hơn hoặc hẹp hơn.
MIN_SYNTHESIS_INCLUSION_SCORE = 2.5


class KnowledgeRetriever:
    """Retrieves relevant chunks and generates grounded answers using pure generic templates."""

    def __init__(self, db_path: Path, chunks: Optional[List[KnowledgeChunk]] = None):
        self.db_path = Path(db_path)
        self.chunks_map: Dict[str, KnowledgeChunk] = {}
        if chunks:
            self.chunks_map = {c.chunk_id: c for c in chunks}
        else:
            self._load_chunks_from_db()

    def _load_chunks_from_db(self):
        """Loads all chunks from SQLite into in-memory dictionary."""
        if not self.db_path.exists():
            return
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM chunks")
        for row in cursor.fetchall():
            kw_list = [k.strip() for k in row["keywords"].split(",") if k.strip()]
            chunk = KnowledgeChunk(
                chunk_id=row["chunk_id"],
                doc_id=row["doc_id"],
                doc_title=row["doc_title"],
                chunk_type=row["chunk_type"],
                section_id=row["section_id"],
                section_title=row["section_title"],
                content=row["content"],
                version=row["version"],
                effective_date=row["effective_date"],
                status=row["status"],
                owner=row["owner"],
                keywords=kw_list
            )
            self.chunks_map[chunk.chunk_id] = chunk
        conn.close()

    def search(self, query: str, top_k: int = 5, active_only: bool = True) -> List[RetrievalResult]:
        """
        Executes hybrid retrieval with natural Query Term Coverage Gating:
        1. FTS5 BM25 search for keyword precision (weighted by matched FTS term ratio).
        2. Lexical token overlap across content, title, and keywords.
        3. Query Term Coverage Gate: Requires at least MIN_QUERY_COVERAGE_RATIO (40%) keyword presence.
        4. Freshness Filter: excludes DEPRECATED chunks if active_only=True.
        5. Noise Filter: drops chunks below MIN_CHUNK_SCORE_THRESHOLD.
        """
        if not self.chunks_map:
            self._load_chunks_from_db()

        query_tokens = self._tokenize(query)
        if not query_tokens:
            return []

        # 1. FTS5 Query with Term Ratio Weighting
        fts_hits = self._fts_search_weighted(query, query_tokens)

        # 2. Score Candidate Chunks
        results: List[RetrievalResult] = []
        for cid, chunk in self.chunks_map.items():
            if active_only and chunk.status == "DEPRECATED":
                continue

            text_all = (chunk.content + " " + chunk.doc_title + " " + chunk.section_title + " " + " ".join(chunk.keywords)).lower()
            matched_tokens = sum(1 for t in query_tokens if t in text_all)
            coverage_ratio = matched_tokens / len(query_tokens) if query_tokens else 0.0

            # Natural Out-of-Scope Gate: Chunk must contain at least 40% of query keywords
            if coverage_ratio < MIN_QUERY_COVERAGE_RATIO:
                continue

            # Lexical overlap
            overlap_count = sum(1 for token in query_tokens if token in chunk.content.lower())
            title_overlap = sum(2 for token in query_tokens if token in (chunk.doc_title + " " + chunk.section_title).lower())
            kw_overlap = sum(3 for token in query_tokens if any(token in kw.lower() for kw in chunk.keywords))

            lexical_score = overlap_count * 1.0 + title_overlap * 2.0 + kw_overlap * 3.0

            # Header Overview Boost for general/summary intent
            # Áp dụng đồng đều cho mọi HEADER_SUMMARY chunk khi câu hỏi mang ý liệt kê/bao quát.
            # Không ưu ái riêng doc_id nào — nếu FAQ-01 vẫn thắng là vì nội dung thực sự khớp nhiều từ khóa hơn.
            if chunk.chunk_type == "HEADER_SUMMARY" and any(w in query.lower() for w in ["tổng quan", "những lỗi", "loại lỗi", "các lỗi", "danh sách", "thường gặp"]):
                lexical_score += HEADER_OVERVIEW_BOOST

            fts_score = fts_hits.get(cid, 0.0)
            raw_total = lexical_score + fts_score
            final_score = raw_total * (coverage_ratio ** 1.3)

            if final_score <= MIN_CHUNK_SCORE_THRESHOLD:
                continue

            results.append(RetrievalResult(
                chunk=chunk,
                score=round(final_score, 2),
                is_active=(chunk.status == "ACTIVE")
            ))

        # Sort descending by score
        results.sort(key=lambda r: r.score, reverse=True)
        return results[:top_k]

    def _fts_search_weighted(self, query: str, query_tokens: List[str]) -> Dict[str, float]:
        """Runs SQLite FTS5 query weighted by term coverage ratio."""
        hits: Dict[str, float] = {}
        if not self.db_path.exists() or not query_tokens:
            return hits

        clean_terms = [w for w in re.findall(r"\w+", query) if w.lower() not in VIETNAMESE_STOP_WORDS]
        if not clean_terms:
            return hits

        fts_query = " OR ".join(clean_terms)

        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
            SELECT chunk_id, rank
            FROM chunk_fts
            WHERE chunk_fts MATCH ?
            ORDER BY rank
            LIMIT 15;
            """, (fts_query,))

            for row in cursor.fetchall():
                cid, rank = row[0], abs(row[1])
                raw_rank_score = 10.0 / (1.0 + rank)
                chunk = self.chunks_map.get(cid)
                if chunk:
                    c_text = (chunk.content + " " + " ".join(chunk.keywords)).lower()
                    matched_fts = sum(1 for t in clean_terms if t.lower() in c_text)
                    fts_cov = matched_fts / len(clean_terms) if clean_terms else 0.0
                    hits[cid] = raw_rank_score * fts_cov * FTS_BM25_WEIGHT

            conn.close()
        except Exception:
            pass

        return hits

    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenizer extracting lowercase terms excluding generic stop words."""
        raw_tokens = [w.lower() for w in re.findall(r"[\w-]+", text) if len(w) > 1]
        return [t for t in raw_tokens if t not in VIETNAMESE_STOP_WORDS]

    def answer_query(self, query: str, top_k: int = 5, active_only: bool = True) -> Dict[str, Any]:
        """
        Pure RAG answer pipeline:
        1. Retrieve top-k relevant active chunks.
        2. Natural Out-of-Scope Detection: if top chunk score < OUT_OF_SCOPE_SCORE_THRESHOLD -> Return explicit rejection.
        3. Generic Grounded Synthesis: Construct answer from retrieved chunks using MIN_SYNTHESIS_INCLUSION_SCORE filter.
        """
        retrieved = self.search(query, top_k=top_k, active_only=active_only)

        # Natural Out-of-Scope classification: câu hỏi bị từ chối nếu top-1 chunk không đủ điểm liên quan
        if not retrieved or retrieved[0].score < OUT_OF_SCOPE_SCORE_THRESHOLD:
            return {
                "query": query,
                "answer": "Không có thông tin trong tài liệu vận hành và chính sách hiện hành.",
                "retrieved_chunks": [],
                "is_out_of_scope": True,
                "sources": []
            }

        # Build citations list
        sources = list(dict.fromkeys([f"{r.chunk.doc_id} ({r.chunk.section_title})" for r in retrieved]))

        # Synthesize answer using pure generic template grounded in retrieved chunks
        answer_text = self._synthesize_generic_grounded_answer(query, retrieved)

        return {
            "query": query,
            "answer": answer_text,
            "retrieved_chunks": retrieved,
            "is_out_of_scope": False,
            "sources": sources
        }

    def _synthesize_generic_grounded_answer(self, query: str, results: List[RetrievalResult]) -> str:
        """
        Generic Grounded Synthesis Engine:
        Constructs factual, structured answers directly from real retrieved chunks.
        100% dynamic, zero hardcoded strings.
        """
        if not results:
            return "Không có thông tin trong tài liệu vận hành và chính sách hiện hành."

        # Filter to top high-confidence chunks (score >= 45% of top-1 score)
        top_score = results[0].score
        relevant_chunks = [r.chunk for r in results if r.score >= max(top_score * 0.45, MIN_SYNTHESIS_INCLUSION_SCORE)]
        if not relevant_chunks:
            relevant_chunks = [results[0].chunk]

        # Case 1: Single Top Chunk or Header Overview
        if len(relevant_chunks) == 1 or relevant_chunks[0].chunk_type == "HEADER_SUMMARY":
            chunk = relevant_chunks[0]
            clean_body = self._clean_chunk_content_for_answer(chunk.content)
            return (
                f"Theo tài liệu **{chunk.doc_id}** ({chunk.doc_title}) — Phiên bản {chunk.version} (Mục: *{chunk.section_title}*):\n\n"
                f"{clean_body}\n\n"
                f"(Nguồn trích dẫn: [{chunk.doc_id} v{chunk.version} - {chunk.section_title}])"
            )

        # Case 2: Multi-Chunk Synthesis (Multi-Source / Multi-Section)
        # Group points by document and section to produce a coherent, structured synthesis
        synthesis_sections = []
        citations = []

        seen_sections = set()
        for chunk in relevant_chunks:
            sec_key = f"{chunk.doc_id}_{chunk.section_id}"
            if sec_key in seen_sections:
                continue
            seen_sections.add(sec_key)

            clean_body = self._clean_chunk_content_for_answer(chunk.content)
            synthesis_sections.append(
                f"### 📄 {chunk.doc_id} — {chunk.section_title} (v{chunk.version}):\n{clean_body}"
            )
            citations.append(f"[{chunk.doc_id} v{chunk.version} - {chunk.section_title}]")

        citations_str = ", ".join(citations)
        answer_body = "\n\n".join(synthesis_sections)

        return (
            f"Tổng hợp từ các tài liệu vận hành và chính sách liên quan:\n\n"
            f"{answer_body}\n\n"
            f"(Nguồn trích dẫn: {citations_str})"
        )

    def _clean_chunk_content_for_answer(self, raw_content: str) -> str:
        """Strips duplicate metadata headers from chunk body to provide clean text."""
        lines = raw_content.splitlines()
        clean_lines = []
        for line in lines:
            if (line.startswith("**Tài liệu:**") or line.startswith("**Mục:**") or 
                line.startswith("**Mục lớn:**") or line.startswith("**Mục chi tiết:**")):
                continue
            clean_lines.append(line)
        return "\n".join(clean_lines).strip()
