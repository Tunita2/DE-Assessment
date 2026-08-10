"""
Document Chunker for Mini Knowledge Base
Implements:
1. Dynamic Document Identity & Metadata Extraction (Generic Regex, zero hardcoded filenames).
2. Dynamic Multi-Version Conflict Resolution (Automatic semver/date comparison for status ACTIVE vs DEPRECATED).
3. Hierarchical Markdown Chunking preserving Parent-Child context (H2 > H3 nesting).
4. Dynamic Entity & Keyword Extraction using comprehensive Regex Patterns.
"""

import re
from pathlib import Path
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict

from kb.src.models import KnowledgeChunk


class MarkdownChunker:
    """Parses operational markdown documents into structured knowledge chunks with metadata."""

    def __init__(self, docs_dir: Path):
        self.docs_dir = Path(docs_dir)

    def parse_all_documents(self) -> List[KnowledgeChunk]:
        """
        Two-pass document processing:
        Pass 1: Inspect all files to discover doc identities, versions, and resolve version conflicts dynamically.
        Pass 2: Parse sections, maintain H2 > H3 hierarchy, extract dynamic keywords, and generate chunks.
        """
        doc_files = sorted(self.docs_dir.glob("*.md"))
        if not doc_files:
            return []

        # Pass 1: Discover documents and resolve version conflicts dynamically
        doc_manifests = []
        for file_path in doc_files:
            manifest = self._inspect_file_metadata(file_path)
            doc_manifests.append(manifest)

        # Resolve conflict: Group by doc_id and find the latest version
        resolved_statuses = self._resolve_version_conflicts(doc_manifests)

        # Pass 2: Chunk documents with resolved status and hierarchical context
        all_chunks: List[KnowledgeChunk] = []
        for manifest in doc_manifests:
            file_path = manifest["file_path"]
            doc_id = manifest["doc_id"]
            status = resolved_statuses.get(file_path, "ACTIVE")
            manifest["status"] = status

            file_chunks = self._chunk_single_document(manifest)
            all_chunks.extend(file_chunks)

        return all_chunks

    def _inspect_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """Dynamically extracts document metadata using generic regex patterns without hardcoding."""
        with open(file_path, "r", encoding="utf-8") as f:
            raw_text = f.read()

        file_name = file_path.name
        lines = raw_text.splitlines()
        first_line = lines[0] if lines else ""

        # 1. Dynamic Doc ID (e.g., POL-01, FAQ-01, SOP-02, RUN-01, SEC-03)
        doc_id_match = re.match(r"^([A-Z]+-\d+)", file_name)
        if not doc_id_match:
            doc_id_match = re.search(r"\b([A-Z]+-\d+)\b", first_line)
        doc_id = doc_id_match.group(1) if doc_id_match else file_path.stem.split("_")[0]

        # 2. Dynamic Doc Title
        doc_title = first_line.lstrip("# ").strip() if first_line else file_path.stem

        # 3. Dynamic Version Extraction (e.g., "Phiên bản 2.0", "v1.1", "Version 1.0")
        ver_match = re.search(r"(?:Phiên bản|Version|v)\s*[:\.]?\s*(\d+(?:\.\d+)?)", raw_text[:500], re.IGNORECASE)
        if not ver_match:
            ver_match = re.search(r"_v(\d+(?:\.\d+)?)", file_name, re.IGNORECASE)
        version_str = ver_match.group(1) if ver_match else "1.0"
        
        # Parse version to tuple for semver comparison, e.g. "2.0" -> (2, 0)
        version_tuple = tuple(int(p) for p in version_str.split(".") if p.isdigit()) if version_str else (1, 0)

        # 4. Dynamic Effective Date Extraction (e.g., "Ban hành: 05/2026", "Cập nhật: 07/2026")
        date_match = re.search(r"(?:Ban hành|Cập nhật|Hiệu lực|Date):\s*(\d{2}/\d{4}|\d{4}-\d{2}-\d{2})", raw_text[:500], re.IGNORECASE)
        effective_date = date_match.group(1) if date_match else "01/2026"

        # 5. Dynamic Supersedes / Replacement Indicator
        has_supersedes = bool(re.search(r"(?:Thay thế phiên bản|supersedes|obsoletes|thay thế)", raw_text[:500], re.IGNORECASE))

        # 6. Dynamic Owner Extraction (e.g., "**Công ty Tài chính Sao Đỏ — Phòng CNTT**")
        owner_match = re.search(r"\*\*([^*]+)\*\*", raw_text[:500])
        owner = owner_match.group(1).strip() if owner_match else "Phòng CNTT"

        return {
            "file_path": file_path,
            "raw_text": raw_text,
            "lines": lines,
            "doc_id": doc_id,
            "doc_title": doc_title,
            "version": version_str,
            "version_tuple": version_tuple,
            "effective_date": effective_date,
            "has_supersedes": has_supersedes,
            "owner": owner
        }

    def _resolve_version_conflicts(self, manifests: List[Dict[str, Any]]) -> Dict[Path, str]:
        """
        Dynamically detects multi-version conflicts for any doc_id and marks the newest as ACTIVE,
        and older superseded versions as DEPRECATED.
        """
        docs_by_id = defaultdict(list)
        for m in manifests:
            docs_by_id[m["doc_id"]].append(m)

        resolved_statuses: Dict[Path, str] = {}

        for doc_id, group in docs_by_id.items():
            if len(group) == 1:
                resolved_statuses[group[0]["file_path"]] = "ACTIVE"
            else:
                # Multiple versions found for same doc_id!
                # Sort descending: (1) has_supersedes flag, (2) version tuple, (3) effective_date
                def sort_key(item):
                    return (
                        1 if item["has_supersedes"] else 0,
                        item["version_tuple"],
                        self._parse_date_sortable(item["effective_date"])
                    )

                sorted_group = sorted(group, key=sort_key, reverse=True)
                # Newest/superseding document is ACTIVE
                resolved_statuses[sorted_group[0]["file_path"]] = "ACTIVE"
                # All older versions are DEPRECATED
                for older in sorted_group[1:]:
                    resolved_statuses[older["file_path"]] = "DEPRECATED"

        return resolved_statuses

    def _parse_date_sortable(self, date_str: str) -> str:
        """Converts MM/YYYY to YYYY-MM for chronological sorting."""
        if "/" in date_str:
            parts = date_str.split("/")
            if len(parts) == 2 and len(parts[1]) == 4:
                return f"{parts[1]}-{parts[0]}"
        return date_str

    def _chunk_single_document(self, manifest: Dict[str, Any]) -> List[KnowledgeChunk]:
        """
        Splits a single document into Header Summary + Hierarchical Section Chunks.
        Preserves H2 parent context when creating H3 child chunks (e.g. section_title = 'H2 > H3').
        """
        doc_id = manifest["doc_id"]
        doc_title = manifest["doc_title"]
        version = manifest["version"]
        effective_date = manifest["effective_date"]
        status = manifest["status"]
        owner = manifest["owner"]
        lines = manifest["lines"]

        # 1. Separate Header intro lines from body sections
        header_intro_lines = []
        idx = 0
        while idx < len(lines):
            line = lines[idx]
            if idx > 0 and (line.startswith("## ") or line.startswith("### ")):
                break
            if idx > 0:
                header_intro_lines.append(line)
            idx += 1

        # 2. Parse Hierarchical Sections (Preserving Parent H2 for child H3)
        sections = self._split_hierarchical_sections(lines[idx:])

        doc_chunks: List[KnowledgeChunk] = []
        ver_tag = f"v{version.replace('.', '_')}"

        # 3. Create Header Summary Chunk (Method 2)
        summary_lines = [
            f"# {doc_title}",
            f"**Tài liệu:** {doc_id} | **Phiên bản:** {version} | **Hiệu lực:** {effective_date} | **Trạng thái:** {status} | **Đơn vị:** {owner}",
            "\n".join(header_intro_lines).strip(),
            "\n**Mục lục & Các nội dung chính trong tài liệu:**"
        ]
        for sec in sections:
            summary_lines.append(f"- {sec['display_title']}")

        header_content = "\n\n".join([s for s in summary_lines if s.strip()])
        header_keywords = self._extract_keywords_dynamic(doc_title + " " + header_content)

        header_chunk = KnowledgeChunk(
            chunk_id=f"{doc_id}_{ver_tag}_header",
            doc_id=doc_id,
            doc_title=doc_title,
            chunk_type="HEADER_SUMMARY",
            section_id="header",
            section_title="Tổng quan & Mục lục tài liệu",
            content=header_content,
            version=version,
            effective_date=effective_date,
            status=status,
            owner=owner,
            keywords=header_keywords
        )
        doc_chunks.append(header_chunk)

        # 4. Create Section Chunks with Parent Context Prepend
        for sec in sections:
            sec_id = f"sec_{sec['sec_num']:02d}"
            display_title = sec["display_title"]
            parent_h2 = sec.get("parent_h2")
            h3_title = sec.get("h3_title")

            # Context-rich header in content
            if parent_h2 and h3_title:
                context_prefix = (
                    f"**Tài liệu:** {doc_id} ({doc_title}) - Phiên bản {version}\n"
                    f"**Mục lớn:** {parent_h2}\n"
                    f"**Mục chi tiết:** {h3_title}\n\n"
                )
            else:
                context_prefix = f"**Tài liệu:** {doc_id} ({doc_title}) - Phiên bản {version}\n**Mục:** {display_title}\n\n"

            full_sec_content = (context_prefix + sec["content"]).strip()
            sec_keywords = self._extract_keywords_dynamic(
                f"{doc_title} {display_title} {parent_h2 or ''} {sec['content']}"
            )

            chunk = KnowledgeChunk(
                chunk_id=f"{doc_id}_{ver_tag}_{sec_id}",
                doc_id=doc_id,
                doc_title=doc_title,
                chunk_type="SECTION",
                section_id=sec_id,
                section_title=display_title,
                content=full_sec_content,
                version=version,
                effective_date=effective_date,
                status=status,
                owner=owner,
                keywords=sec_keywords
            )
            doc_chunks.append(chunk)

        return doc_chunks

    def _split_hierarchical_sections(self, lines: List[str]) -> List[Dict[str, Any]]:
        """
        Splits markdown lines into hierarchical sections.
        If H3 is encountered within an H2, sets display_title = f'{parent_h2} > {h3_title}'.
        """
        sections: List[Dict[str, Any]] = []
        current_h2 = ""
        current_title = ""
        current_h3 = ""
        current_lines: List[str] = []
        sec_num = 0

        for line in lines:
            if line.startswith("## "):
                # Finish previous section
                if current_title and current_lines:
                    sec_num += 1
                    display = f"{current_h2} > {current_h3}" if (current_h2 and current_h3) else current_title
                    sections.append({
                        "sec_num": sec_num,
                        "display_title": display,
                        "parent_h2": current_h2 if current_h3 else None,
                        "h3_title": current_h3 if current_h3 else None,
                        "content": "\n".join(current_lines).strip()
                    })

                current_h2 = line.lstrip("# ").strip()
                current_h3 = ""
                current_title = current_h2
                current_lines = [line]

            elif line.startswith("### "):
                # Finish previous section under H2 or previous H3
                if current_title and current_lines:
                    sec_num += 1
                    display = f"{current_h2} > {current_h3}" if (current_h2 and current_h3) else current_title
                    sections.append({
                        "sec_num": sec_num,
                        "display_title": display,
                        "parent_h2": current_h2 if current_h3 else None,
                        "h3_title": current_h3 if current_h3 else None,
                        "content": "\n".join(current_lines).strip()
                    })

                current_h3 = line.lstrip("# ").strip()
                current_title = f"{current_h2} > {current_h3}" if current_h2 else current_h3
                current_lines = [line]

            else:
                current_lines.append(line)

        # Flush last section
        if current_title and current_lines:
            sec_num += 1
            display = f"{current_h2} > {current_h3}" if (current_h2 and current_h3) else current_title
            sections.append({
                "sec_num": sec_num,
                "display_title": display,
                "parent_h2": current_h2 if current_h3 else None,
                "h3_title": current_h3 if current_h3 else None,
                "content": "\n".join(current_lines).strip()
            })

        return sections

    def _extract_keywords_dynamic(self, text: str) -> List[str]:
        """
        Dynamically extracts technical entities, error codes, service names, CLI commands,
        and operational keywords using generic Regex Patterns instead of hardcoded lists.
        """
        keywords = set()
        text_lower = text.lower()

        # 1. Regex Pattern: Error Codes (e.g. ERR ConnTimeout, ERR NullPointer, ERR_HTTP_502, HTTP 502)
        err_matches = re.findall(r"\bERR[_\s-][A-Za-z0-9_\-\./]+", text, re.IGNORECASE)
        for e in err_matches:
            keywords.add(e.lower().strip())

        http_matches = re.findall(r"\b(?:HTTP|STATUS)[_\s-]?\d{3}\b", text, re.IGNORECASE)
        for h in http_matches:
            keywords.add(h.lower().strip())

        # 2. Regex Pattern: Microservice & Host names (kebab-case pattern: auth-service, payment-api, db-primary, etc.)
        svc_matches = re.findall(r"\b[a-z0-9]+(?:-[a-z0-9]+)+\b", text_lower)
        for s in svc_matches:
            if not s.startswith("-") and not s.endswith("-") and len(s) > 3:
                keywords.add(s)

        # 3. Regex Pattern: Technical Code Tokens inside backticks (e.g. `systemctl restart ...`, `request_id`)
        backtick_matches = re.findall(r"`([^`]+)`", text)
        for b in backtick_matches:
            b_clean = b.strip().lower()
            if 2 < len(b_clean) < 40:
                keywords.add(b_clean)

        # 4. Regex Pattern: Emphasized Operational Terms in bold (e.g. **23:30**, **P1**, **30 ngày**, **quyền tối thiểu**)
        bold_matches = re.findall(r"\*\*([^*]+)\*\*", text)
        for bm in bold_matches:
            bm_clean = bm.strip().lower()
            if 2 < len(bm_clean) < 30 and not any(w in bm_clean for w in ["công ty", "phòng cntt"]):
                keywords.add(bm_clean)

        # 5. Regex Pattern: SLA, Incident Severities, and Operational Tokens
        op_token_matches = re.findall(
            r"\b(?:P[1-3]|SLA|WARN|CRITICAL|KMS|TLS|2FA|UTC|DBA|POST-MORTEM|RUNBOOK|BACKUP|RESTORE|RESTART|QUEUE|DEADLINE)\b",
            text, re.IGNORECASE
        )
        for ot in op_token_matches:
            keywords.add(ot.lower())

        # 6. Regex Pattern: Metric Thresholds (e.g. > 2%, > 5%, > 95%, > 2.000)
        threshold_matches = re.findall(r"[><=]\s*\d+(?:[\.,]\d+)?%?", text)
        for tm in threshold_matches:
            keywords.add(tm.replace(" ", ""))

        # 7. Common Operational Stem Patterns (sao lưu, bảo mật, mật khẩu, tài khoản, khóa, nghỉ việc)
        domain_patterns = [
            r"\bsao lưu\b", r"\bkhôi phục\b", r"\bmật khẩu\b", r"\btruy cập\b",
            r"\btài khoản\b", r"\bkhoá\b", r"\bnghỉ việc\b", r"\bkiểm toán\b",
            r"\bleo thang\b", r"\bquá tải\b", r"\bđột biến\b", r"\blệch số dư\b"
        ]
        for dp in domain_patterns:
            if re.search(dp, text_lower):
                keywords.add(dp.replace(r"\b", ""))

        return sorted(list(keywords))
