"""
Unit Tests for Mini Knowledge Base & RAG Evaluation
Tests Chunking, Metadata Extraction, Version Conflict Resolution, Indexing, Retrieval, and Benchmark Evaluation.
"""

import pytest
from pathlib import Path
import json

from kb.src.chunker import MarkdownChunker
from kb.src.indexer import KnowledgeIndexer
from kb.src.retriever import KnowledgeRetriever
from kb.src.evaluator import KnowledgeEvaluator


@pytest.fixture
def docs_dir():
    return Path("data/docs")


@pytest.fixture
def eval_questions_path():
    return Path("kb/eval/eval_questions.json")


def test_chunker_structure_and_metadata(docs_dir):
    chunker = MarkdownChunker(docs_dir)
    chunks = chunker.parse_all_documents()

    assert len(chunks) >= 25, "Must generate at least 25 knowledge chunks"

    # Check for header summary chunks
    header_chunks = [c for c in chunks if c.chunk_type == "HEADER_SUMMARY"]
    assert len(header_chunks) == 8, "Each of the 8 docs must have a header summary chunk"

    # Check required metadata fields
    for c in chunks:
        assert c.chunk_id != ""
        assert c.doc_id != ""
        assert c.doc_title != ""
        assert c.version != ""
        assert c.effective_date != ""
        assert c.status in ["ACTIVE", "DEPRECATED"]
        assert len(c.content) > 10


def test_version_conflict_resolution(docs_dir):
    chunker = MarkdownChunker(docs_dir)
    chunks = chunker.parse_all_documents()

    v1_chunks = [c for c in chunks if c.doc_id == "POL-01" and c.version == "1.0"]
    v2_chunks = [c for c in chunks if c.doc_id == "POL-01" and c.version == "2.0"]

    assert len(v1_chunks) > 0, "POL-01 v1 chunks must exist"
    assert len(v2_chunks) > 0, "POL-01 v2 chunks must exist"

    # All v1 chunks must be marked DEPRECATED
    for c in v1_chunks:
        assert c.status == "DEPRECATED"

    # All v2 chunks must be marked ACTIVE
    for c in v2_chunks:
        assert c.status == "ACTIVE"


def test_indexer_persistence(tmp_path, docs_dir):
    chunker = MarkdownChunker(docs_dir)
    chunks = chunker.parse_all_documents()

    indexer = KnowledgeIndexer(tmp_path)
    json_path, db_path = indexer.index_chunks(chunks)

    assert json_path.exists()
    assert db_path.exists()

    with open(json_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert len(data) == len(chunks)


def test_retriever_hybrid_search(tmp_path, docs_dir):
    chunker = MarkdownChunker(docs_dir)
    chunks = chunker.parse_all_documents()
    indexer = KnowledgeIndexer(tmp_path)
    _, db_path = indexer.index_chunks(chunks)

    retriever = KnowledgeRetriever(db_path, chunks=chunks)
    results = retriever.search("ERR ConnTimeout db-primary", top_k=3)

    assert len(results) > 0
    assert results[0].chunk.doc_id == "FAQ-01"
    assert "ConnTimeout" in results[0].chunk.section_title


def test_retriever_freshness_filter(tmp_path, docs_dir):
    chunker = MarkdownChunker(docs_dir)
    chunks = chunker.parse_all_documents()
    indexer = KnowledgeIndexer(tmp_path)
    _, db_path = indexer.index_chunks(chunks)

    retriever = KnowledgeRetriever(db_path, chunks=chunks)
    
    # Active search must NOT return any DEPRECATED v1 chunks
    results_active = retriever.search("chính sách sao lưu backup dữ liệu", top_k=5, active_only=True)
    for r in results_active:
        assert r.chunk.status != "DEPRECATED"
        if r.chunk.doc_id == "POL-01":
            assert r.chunk.version == "2.0"

    # Answer query test
    answer = retriever.answer_query("Chính sách sao lưu cơ sở dữ liệu quy định thế nào?", active_only=True)
    assert "23:30" in answer["answer"]
    assert "30 ngày" in answer["answer"]
    assert "22:00" not in answer["answer"]


def test_retriever_out_of_scope(tmp_path, docs_dir):
    chunker = MarkdownChunker(docs_dir)
    chunks = chunker.parse_all_documents()
    indexer = KnowledgeIndexer(tmp_path)
    _, db_path = indexer.index_chunks(chunks)

    retriever = KnowledgeRetriever(db_path, chunks=chunks)
    answer = retriever.answer_query("Công ty có phụ cấp tiền ăn trưa không?")

    assert answer["is_out_of_scope"] is True
    assert "không có thông tin" in answer["answer"].lower()


def test_evaluator_benchmark(tmp_path, docs_dir, eval_questions_path):
    chunker = MarkdownChunker(docs_dir)
    chunks = chunker.parse_all_documents()
    indexer = KnowledgeIndexer(tmp_path)
    _, db_path = indexer.index_chunks(chunks)

    retriever = KnowledgeRetriever(db_path, chunks=chunks)
    evaluator = KnowledgeEvaluator(eval_questions_path, retriever)
    summary = evaluator.run_evaluation(top_k=5)

    assert summary.total_questions == 10
    assert summary.retrieval_hit_rate_pct == 100.0
    assert summary.groundedness_pass_rate_pct == 100.0
    assert summary.version_conflict_resolution_rate_pct == 100.0
    assert summary.out_of_scope_rejection_rate_pct == 100.0
    assert summary.overall_pass_rate_pct == 100.0


def test_dynamic_conflict_resolution_and_hierarchy_preservation(tmp_path):
    """Tests dynamic conflict resolution and H2 > H3 parent context preservation on synthetic docs."""
    doc_v1 = tmp_path / "SEC-99_an_toan_v1.md"
    doc_v1.write_text("""# SEC-99 — Chính sách Bảo mật Mạng
**Công ty Tài chính Sao Đỏ** · Phiên bản 1.0 · Ban hành: 01/2025

## 1. Quy định Firewall
Mở cổng 80 và 443.
""", encoding="utf-8")

    doc_v2 = tmp_path / "SEC-99_an_toan_v2.md"
    doc_v2.write_text("""# SEC-99 — Chính sách Bảo mật Mạng
**Công ty Tài chính Sao Đỏ** · Phiên bản 2.0 · Ban hành: 08/2026 · Thay thế phiên bản trước

## 1. Cấu hình Hạ tầng

### 1.1 payment-gateway
Chỉ mở cổng 443 mã hoá TLS 1.3, đóng hoàn toàn cổng 80.

### 1.2 auth-cluster
Yêu cầu xác thực 2FA.
""", encoding="utf-8")

    chunker = MarkdownChunker(tmp_path)
    chunks = chunker.parse_all_documents()

    v1_chunks = [c for c in chunks if c.doc_id == "SEC-99" and c.version == "1.0"]
    v2_chunks = [c for c in chunks if c.doc_id == "SEC-99" and c.version == "2.0"]

    # Dynamic conflict resolution
    assert len(v1_chunks) > 0
    assert len(v2_chunks) > 0
    assert all(c.status == "DEPRECATED" for c in v1_chunks)
    assert all(c.status == "ACTIVE" for c in v2_chunks)

    # Hierarchical H2 > H3 check
    h3_chunk = next(c for c in v2_chunks if "1.1 payment-gateway" in c.section_title)
    assert "1. Cấu hình Hạ tầng > 1.1 payment-gateway" in h3_chunk.section_title
    assert "**Mục lớn:** 1. Cấu hình Hạ tầng" in h3_chunk.content
    assert "**Mục chi tiết:** 1.1 payment-gateway" in h3_chunk.content
    assert "payment-gateway" in h3_chunk.keywords


def test_dynamic_regex_entity_extraction():
    """Tests regex entity extractor across error codes, services, thresholds, and backtick terms."""
    chunker = MarkdownChunker(Path("data/docs"))
    sample_text = "Dịch vụ `payment-api` gặp lỗi `ERR ConnTimeout db-primary` với tỷ lệ > 5% kích hoạt cảnh báo CRITICAL theo SLA P1."
    kws = chunker._extract_keywords_dynamic(sample_text)

    assert "payment-api" in kws
    assert "db-primary" in kws
    assert "err conntimeout" in kws or "err conntimeout db-primary" in kws
    assert "critical" in kws
    assert "p1" in kws
    assert "sla" in kws

