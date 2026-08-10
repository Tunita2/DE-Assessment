"""
Ingestion Module for Log Processing Pipeline
Safely streams and parses raw JSON lines
"""

import json
from pathlib import Path
from typing import Iterator, Union
from pipeline.src.models import RawLogRecord


def stream_raw_logs(file_path: Union[str, Path]) -> Iterator[RawLogRecord]:
    """
    Stream log records line by line from a JSONL file.
    Recovers from malformed JSON and encoding quirks without crashing.
    
    Args:
        file_path: Path to the JSONL log file
        
    Yields:
        RawLogRecord containing parsed JSON or parse error metadata
    """
    path = Path(file_path)
    if not path.exists():
        raise FileNotFoundError(f"Log file does not exist at: {path}")

    with open(path, "r", encoding="utf-8", errors="replace") as f:
        for line_number, line in enumerate(f, start=1):
            raw_text = line.strip()
            if not raw_text:
                yield RawLogRecord(
                    line_number=line_number,
                    raw_text=raw_text,
                    is_valid_json=False,
                    parse_error="Empty line"
                )
                continue

            try:
                parsed = json.loads(raw_text)
                if not isinstance(parsed, dict):
                    yield RawLogRecord(
                        line_number=line_number,
                        raw_text=raw_text,
                        is_valid_json=False,
                        parse_error=f"JSON root is not an object (type={type(parsed).__name__})"
                    )
                    continue

                yield RawLogRecord(
                    line_number=line_number,
                    raw_text=raw_text,
                    parsed_json=parsed,
                    is_valid_json=True
                )
            except json.JSONDecodeError as exc:
                yield RawLogRecord(
                    line_number=line_number,
                    raw_text=raw_text,
                    is_valid_json=False,
                    parse_error=f"JSONDecodeError: {exc.msg} at line {exc.lineno} col {exc.colno}"
                )
            except Exception as exc:
                yield RawLogRecord(
                    line_number=line_number,
                    raw_text=raw_text,
                    is_valid_json=False,
                    parse_error=f"Unexpected parsing error: {str(exc)}"
                )
