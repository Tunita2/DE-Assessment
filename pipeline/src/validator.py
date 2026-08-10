"""
Validation & Cleaning Engine for Log Processing Pipeline
Validates schemas, normalizes timestamps to UTC, and handles deduplication
"""

import re
from typing import Set, Tuple, List, Optional
from datetime import datetime, timezone
import dateutil.parser

from pipeline.src.models import RawLogRecord, CleanedLogRecord, QuarantineRecord

VALID_SERVICES = {
    "auth-service",
    "payment-api",
    "web-portal",
    "batch-report",
    "notification-worker"
}

VALID_LEVELS = {"INFO", "WARN", "ERROR", "DEBUG"}


class LogValidator:
    """
    Validates, standardizes, and deduplicates raw log records.
    """

    def __init__(self):
        self._seen_signatures: Set[Tuple[str, str, str, str, Optional[str]]] = set()

    def reset_deduplication_state(self):
        """Reset internal deduplication cache."""
        self._seen_signatures.clear()

    def process_raw_record(
        self, raw_record: RawLogRecord
    ) -> Tuple[Optional[CleanedLogRecord], Optional[QuarantineRecord]]:
        """
        Validate a single RawLogRecord.
        
        Returns:
            Tuple of (CleanedLogRecord or None, QuarantineRecord or None)
        """
        # 1. Check if raw JSON parsing succeeded
        if not raw_record.is_valid_json or raw_record.parsed_json is None:
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Malformed JSON",
                reason_detail=raw_record.parse_error or "Invalid JSON syntax",
                parsed_payload=None
            )

        payload = raw_record.parsed_json

        # 2. Validate timestamp
        ts_raw = payload.get("timestamp")
        if not ts_raw or not isinstance(ts_raw, str):
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Invalid Timestamp",
                reason_detail=f"Missing or non-string timestamp: {ts_raw}",
                parsed_payload=payload
            )

        try:
            # Parse timestamp with dateutil
            dt = dateutil.parser.isoparse(ts_raw)
            if dt.tzinfo is None:
                # If naive, treat as UTC
                dt = dt.replace(tzinfo=timezone.utc)
            else:
                # Convert timezone offset (e.g. +07:00) to UTC
                dt = dt.astimezone(timezone.utc)

            # Format to standard ISO 8601 UTC
            ts_utc = dt.strftime("%Y-%m-%dT%H:%M:%SZ")
            log_date = dt.strftime("%Y-%m-%d")
        except Exception as exc:
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Invalid Timestamp",
                reason_detail=f"Cannot parse timestamp '{ts_raw}': {str(exc)}",
                parsed_payload=payload
            )

        # 3. Validate Log Level
        level_raw = payload.get("level")
        if not level_raw or not isinstance(level_raw, str):
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Missing / Invalid Level",
                reason_detail=f"Log level is null or missing (got {level_raw})",
                parsed_payload=payload
            )

        level_norm = level_raw.strip().upper()
        if level_norm not in VALID_LEVELS:
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Missing / Invalid Level",
                reason_detail=f"Unrecognized log level '{level_raw}'",
                parsed_payload=payload
            )

        # 4. Validate Service Name
        service_raw = payload.get("service")
        if not service_raw or not isinstance(service_raw, str):
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Invalid Service",
                reason_detail=f"Service is null or missing (got {service_raw})",
                parsed_payload=payload
            )

        service_norm = service_raw.strip().lower()
        if service_norm not in VALID_SERVICES:
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Invalid Service",
                reason_detail=f"Unrecognized service '{service_raw}' not in known 5 internal systems",
                parsed_payload=payload
            )

        # 5. Extract other fields
        message_raw = payload.get("message")
        message = str(message_raw) if message_raw is not None else ""
        request_id = str(payload.get("request_id")) if payload.get("request_id") is not None else None
        trace_id = str(payload.get("trace_id")) if payload.get("trace_id") is not None else None

        # 6. Deduplication check
        sig = (ts_utc, service_norm, level_norm, message, request_id)
        if sig in self._seen_signatures:
            return None, QuarantineRecord(
                line_number=raw_record.line_number,
                raw_content=raw_record.raw_text,
                issue_category="Duplicate Record",
                reason_detail=f"Exact duplicate of earlier record (signature={sig})",
                parsed_payload=payload
            )

        self._seen_signatures.add(sig)

        cleaned = CleanedLogRecord(
            line_number=raw_record.line_number,
            timestamp=ts_utc,
            log_date=log_date,
            service=service_norm,
            level=level_norm,
            message=message,
            request_id=request_id,
            trace_id=trace_id,
            raw_timestamp=ts_raw
        )

        return cleaned, None
