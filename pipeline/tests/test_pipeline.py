"""
Unit Tests for Data Pipeline
Tests Ingestion, Validation, Timezone Normalization, Deduplication, Storage, Analytics, and Dual Verification
"""

import json
import pytest
from pathlib import Path
import pandas as pd

from pipeline.src.models import RawLogRecord, CleanedLogRecord, QuarantineRecord
from pipeline.src.ingest import stream_raw_logs
from pipeline.src.validator import LogValidator
from pipeline.src.storage import StorageManager
from pipeline.src.analytics import LogAnalytics


def test_validator_clean_record():
    validator = LogValidator()
    raw = RawLogRecord(
        line_number=1,
        raw_text='{"timestamp": "2026-07-27T00:02:47Z", "service": "payment-api", "level": "ERROR", "message": "ERR ConnTimeout db-primary", "request_id": "req-1"}',
        parsed_json={
            "timestamp": "2026-07-27T00:02:47Z",
            "service": "payment-api",
            "level": "ERROR",
            "message": "ERR ConnTimeout db-primary",
            "request_id": "req-1"
        }
    )
    cleaned, quarantined = validator.process_raw_record(raw)
    assert cleaned is not None
    assert quarantined is None
    assert cleaned.timestamp == "2026-07-27T00:02:47Z"
    assert cleaned.log_date == "2026-07-27"
    assert cleaned.service == "payment-api"
    assert cleaned.level == "ERROR"


def test_validator_timezone_normalization():
    validator = LogValidator()
    # Log with local timezone +07:00 (07:15:00 in +07:00 is 00:15:00 UTC)
    raw = RawLogRecord(
        line_number=2,
        raw_text='{"timestamp": "2026-07-27T07:15:00+07:00", "service": "auth-service", "level": "INFO", "message": "User login", "request_id": "req-2"}',
        parsed_json={
            "timestamp": "2026-07-27T07:15:00+07:00",
            "service": "auth-service",
            "level": "INFO",
            "message": "User login",
            "request_id": "req-2"
        }
    )
    cleaned, quarantined = validator.process_raw_record(raw)
    assert cleaned is not None
    assert quarantined is None
    assert cleaned.timestamp == "2026-07-27T00:15:00Z"
    assert cleaned.log_date == "2026-07-27"


def test_validator_invalid_timestamp():
    validator = LogValidator()
    raw = RawLogRecord(
        line_number=3,
        raw_text='{"timestamp": "not-a-date", "service": "auth-service", "level": "WARN", "message": "Clock sync failed"}',
        parsed_json={
            "timestamp": "not-a-date",
            "service": "auth-service",
            "level": "WARN",
            "message": "Clock sync failed"
        }
    )
    cleaned, quarantined = validator.process_raw_record(raw)
    assert cleaned is None
    assert quarantined is not None
    assert quarantined.issue_category == "Invalid Timestamp"


def test_validator_missing_level():
    validator = LogValidator()
    raw = RawLogRecord(
        line_number=4,
        raw_text='{"timestamp": "2026-07-30T12:07:36Z", "service": "notification-worker", "message": "Heartbeat ok"}',
        parsed_json={
            "timestamp": "2026-07-30T12:07:36Z",
            "service": "notification-worker",
            "message": "Heartbeat ok"
        }
    )
    cleaned, quarantined = validator.process_raw_record(raw)
    assert cleaned is None
    assert quarantined is not None
    assert quarantined.issue_category == "Missing / Invalid Level"


def test_validator_deduplication():
    validator = LogValidator()
    payload = {
        "timestamp": "2026-07-27T00:02:47Z",
        "service": "payment-api",
        "level": "ERROR",
        "message": "ERR ConnTimeout",
        "request_id": "req-dup"
    }
    raw1 = RawLogRecord(line_number=10, raw_text=json.dumps(payload), parsed_json=payload)
    raw2 = RawLogRecord(line_number=11, raw_text=json.dumps(payload), parsed_json=payload)

    c1, q1 = validator.process_raw_record(raw1)
    c2, q2 = validator.process_raw_record(raw2)

    assert c1 is not None and q1 is None
    assert c2 is None and q2 is not None
    assert q2.issue_category == "Duplicate Record"


def test_storage_manager(tmp_path):
    storage = StorageManager(tmp_path)
    records = [
        CleanedLogRecord(
            line_number=1,
            timestamp="2026-07-27T00:00:00Z",
            log_date="2026-07-27",
            service="payment-api",
            level="ERROR",
            message="Test error",
            request_id="req-1"
        )
    ]
    parquet_file = storage.save_clean_logs_parquet(records)
    sqlite_file = storage.save_clean_logs_sqlite(records)

    assert parquet_file.exists()
    assert sqlite_file.exists()

    df = pd.read_parquet(parquet_file)
    assert len(df) == 1
    assert df.iloc[0]["service"] == "payment-api"


def test_analytics_and_dual_verification():
    records = [
        CleanedLogRecord(
            line_number=1,
            timestamp="2026-07-27T00:00:00Z",
            log_date="2026-07-27",
            service="payment-api",
            level="ERROR",
            message="ERR ConnTimeout db-primary",
            request_id="req-1"
        ),
        CleanedLogRecord(
            line_number=2,
            timestamp="2026-07-27T01:00:00Z",
            log_date="2026-07-27",
            service="payment-api",
            level="ERROR",
            message="ERR ConnTimeout db-primary",
            request_id="req-2"
        ),
        CleanedLogRecord(
            line_number=3,
            timestamp="2026-07-28T00:00:00Z",
            log_date="2026-07-28",
            service="web-portal",
            level="INFO",
            message="Page view",
            request_id="req-3"
        )
    ]
    quarantine = [
        QuarantineRecord(
            line_number=99,
            raw_content="corrupted",
            issue_category="Malformed JSON",
            reason_detail="Syntax error"
        )
    ]

    analytics = LogAnalytics(records, quarantine)
    q1 = analytics.question_1_service_errors()
    assert q1["top_service"] == "payment-api"
    assert q1["top_errors"] == 2
    assert q1["top_error_rate"] == 100.0

    q2 = analytics.question_2_daily_trend()
    assert q2["anomaly_date"] == "2026-07-27"
    assert q2["anomaly_errors"] == 2

    q3 = analytics.question_3_top_error_types()
    assert len(q3["top_3"]) >= 1
    assert q3["top_3"][0]["message"] == "ERR ConnTimeout db-primary"

    q4 = analytics.question_4_cleaning_statistics(total_raw_lines=4)
    assert q4["total_clean"] == 3
    assert q4["total_quarantined"] == 1

    # Dual verification check
    dual_check = analytics.verify_pandas_vs_sql()
    assert dual_check["all_match"] is True
