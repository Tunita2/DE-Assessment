"""
Storage & Indexer Module for Knowledge Base
Persists chunks to JSON and builds SQLite FTS5 Full-Text Search Database.
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Tuple

from kb.src.models import KnowledgeChunk


class KnowledgeIndexer:
    """Manages persistent storage and FTS5 indexing of knowledge chunks."""

    def __init__(self, output_dir: Path):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.json_path = self.output_dir / "chunks.json"
        self.db_path = self.output_dir / "knowledge_base.db"

    def index_chunks(self, chunks: List[KnowledgeChunk]) -> Tuple[Path, Path]:
        """Saves chunks to JSON and builds SQLite FTS5 database."""
        # 1. Save JSON
        chunks_data = [c.to_dict() for c in chunks]
        with open(self.json_path, "w", encoding="utf-8") as f:
            json.dump(chunks_data, f, ensure_ascii=False, indent=2)

        # 2. Build SQLite FTS5 Database
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()

        # Create relational table
        cursor.execute("DROP TABLE IF EXISTS chunks;")
        cursor.execute("""
        CREATE TABLE chunks (
            chunk_id TEXT PRIMARY KEY,
            doc_id TEXT,
            doc_title TEXT,
            chunk_type TEXT,
            section_id TEXT,
            section_title TEXT,
            content TEXT,
            version TEXT,
            effective_date TEXT,
            status TEXT,
            owner TEXT,
            keywords TEXT
        );
        """)

        # Create FTS5 virtual table
        cursor.execute("DROP TABLE IF EXISTS chunk_fts;")
        cursor.execute("""
        CREATE VIRTUAL TABLE chunk_fts USING fts5(
            chunk_id UNINDEXED,
            doc_id,
            doc_title,
            section_title,
            content,
            keywords,
            tokenize = 'unicode61 remove_diacritics 2'
        );
        """)

        # Insert records
        for chunk in chunks:
            kw_str = ", ".join(chunk.keywords)
            cursor.execute("""
            INSERT INTO chunks (
                chunk_id, doc_id, doc_title, chunk_type, section_id, section_title,
                content, version, effective_date, status, owner, keywords
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (
                chunk.chunk_id, chunk.doc_id, chunk.doc_title, chunk.chunk_type,
                chunk.section_id, chunk.section_title, chunk.content, chunk.version,
                chunk.effective_date, chunk.status, chunk.owner, kw_str
            ))

            cursor.execute("""
            INSERT INTO chunk_fts (chunk_id, doc_id, doc_title, section_title, content, keywords)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (chunk.chunk_id, chunk.doc_id, chunk.doc_title, chunk.section_title, chunk.content, kw_str))

        conn.commit()
        conn.close()

        return self.json_path, self.db_path

