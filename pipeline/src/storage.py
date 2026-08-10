"""
Storage Module for Cleaned and Quarantined Logs
Supports Apache Parquet, SQLite, and JSONL formats
"""

import json
import sqlite3
from pathlib import Path
from typing import List, Union, Dict, Any
import pandas as pd

from pipeline.src.models import CleanedLogRecord, QuarantineRecord, PipelineSummary


class StorageManager:
    """Manages writing cleaned and quarantined datasets to persistent storage."""

    def __init__(self, output_dir: Union[str, Path]):
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.parquet_path = self.output_dir / "clean_logs.parquet"
        self.sqlite_path = self.output_dir / "clean_logs.db"
        self.quarantine_path = self.output_dir / "quarantine_logs.jsonl"
        self.summary_path = self.output_dir / "pipeline_summary.json"

    def save_clean_logs_parquet(self, records: List[CleanedLogRecord]) -> Path:
        """Save cleaned records as Apache Parquet."""
        if not records:
            df = pd.DataFrame(columns=[
                "line_number", "timestamp", "log_date", "service", "level",
                "message", "request_id", "trace_id", "raw_timestamp"
            ])
        else:
            df = pd.DataFrame([r.to_dict() for r in records])

        # Cast data types explicitly
        df["line_number"] = df["line_number"].astype("int64")
        df["timestamp"] = pd.to_datetime(df["timestamp"])
        df["log_date"] = df["log_date"].astype("string")
        df["service"] = df["service"].astype("category")
        df["level"] = df["level"].astype("category")
        df["message"] = df["message"].astype("string")
        df["request_id"] = df["request_id"].astype("string")
        df["trace_id"] = df["trace_id"].astype("string")
        df["raw_timestamp"] = df["raw_timestamp"].astype("string")

        df.to_parquet(
            self.parquet_path,
            engine="pyarrow",
            compression="snappy",
            index=False
        )
        return self.parquet_path

    def save_clean_logs_sqlite(self, records: List[CleanedLogRecord]) -> Path:
        """Save cleaned records to SQLite table with indexes."""
        if self.sqlite_path.exists():
            self.sqlite_path.unlink()

        conn = sqlite3.connect(self.sqlite_path)
        cursor = conn.cursor()

        cursor.execute("""
        CREATE TABLE cleaned_logs (
            line_number INTEGER,
            timestamp TEXT NOT NULL,
            log_date TEXT NOT NULL,
            service TEXT NOT NULL,
            level TEXT NOT NULL,
            message TEXT,
            request_id TEXT,
            trace_id TEXT,
            raw_timestamp TEXT
        );
        """)

        cursor.execute("CREATE INDEX idx_logs_date_service ON cleaned_logs(log_date, service);")
        cursor.execute("CREATE INDEX idx_logs_level ON cleaned_logs(level);")
        cursor.execute("CREATE INDEX idx_logs_service_level ON cleaned_logs(service, level);")

        data = [
            (
                r.line_number, r.timestamp, r.log_date, r.service, r.level,
                r.message, r.request_id, r.trace_id, r.raw_timestamp
            )
            for r in records
        ]

        cursor.executemany(
            "INSERT INTO cleaned_logs VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?);",
            data
        )

        conn.commit()
        conn.close()
        return self.sqlite_path

    def save_quarantine_logs(self, records: List[QuarantineRecord]) -> Path:
        """Save quarantined records to JSONL file."""
        with open(self.quarantine_path, "w", encoding="utf-8") as f:
            for r in records:
                f.write(json.dumps(r.to_dict(), ensure_ascii=False) + "\n")
        return self.quarantine_path

    def save_summary(self, summary: PipelineSummary) -> Path:
        """Save summary metadata to JSON."""
        with open(self.summary_path, "w", encoding="utf-8") as f:
            json.dump(summary.model_dump(), f, indent=2, ensure_ascii=False)
        return self.summary_path
