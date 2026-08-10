"""
Data Models for Log Processing Pipeline
Using Pydantic for validation and serialization
"""

from typing import Optional, Dict, Any, List
from datetime import datetime
from pydantic import BaseModel, Field


class RawLogRecord(BaseModel):
    """Raw record as parsed from JSONL line."""
    line_number: int
    raw_text: str
    parsed_json: Optional[Dict[str, Any]] = None
    is_valid_json: bool = True
    parse_error: Optional[str] = None


class CleanedLogRecord(BaseModel):
    """Standardized and validated log record."""
    line_number: int
    timestamp: str = Field(description="ISO 8601 UTC formatted timestamp (YYYY-MM-DDTHH:MM:SSZ)")
    log_date: str = Field(description="Date in YYYY-MM-DD format (UTC) for partitioning")
    service: str = Field(description="Internal service name")
    level: str = Field(description="Normalized log level: INFO, WARN, ERROR, DEBUG")
    message: str = Field(description="Log message text")
    request_id: Optional[str] = Field(default=None, description="Unique request identifier")
    trace_id: Optional[str] = Field(default=None, description="Distributed trace identifier if present")
    raw_timestamp: Optional[str] = Field(default=None, description="Original timestamp before UTC normalization")

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "timestamp": self.timestamp,
            "log_date": self.log_date,
            "service": self.service,
            "level": self.level,
            "message": self.message,
            "request_id": self.request_id,
            "trace_id": self.trace_id,
            "raw_timestamp": self.raw_timestamp
        }


class QuarantineRecord(BaseModel):
    """Quarantined or rejected record with specific failure reason."""
    line_number: int
    raw_content: str
    issue_category: str = Field(description="Category: Malformed JSON, Invalid Timestamp, Missing Level, Duplicate, etc.")
    reason_detail: str
    parsed_payload: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "line_number": self.line_number,
            "issue_category": self.issue_category,
            "reason_detail": self.reason_detail,
            "raw_content": self.raw_content,
            "parsed_payload": self.parsed_payload
        }


class PipelineSummary(BaseModel):
    """Summary statistics for the pipeline execution."""
    total_lines_read: int
    cleaned_records_count: int
    quarantined_records_count: int
    quarantine_breakdown: Dict[str, int]
    service_distribution: Dict[str, int]
    level_distribution: Dict[str, int]
    date_distribution: Dict[str, int]
    execution_time_seconds: float
