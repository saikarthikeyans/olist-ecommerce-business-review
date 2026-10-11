"""Unit tests for Data Quality checking suite and critical failure triggers."""

from __future__ import annotations

from pathlib import Path
import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.pipeline.load_raw import load_all_raw_data
from backend.pipeline.transform_stg import transform_staging_tables
from backend.quality.runner import CriticalQualityCheckFailure, log_and_record_check


def test_quality_audit_recording(test_engine: Engine):
    """Assert quality check outcomes can be recorded into pipeline_quality_audit."""
    mock_result = {
        "check_name": "01_null_duplicate_orders",
        "severity": "CRITICAL",
        "threshold": 0,
        "failed_count": 0,
        "status": "PASS",
        "sample_failing_identifiers": "none",
        "details": "All order identifiers are unique.",
    }
    log_and_record_check(mock_result, test_engine)

    with test_engine.connect() as conn:
        count = conn.execute(text("SELECT COUNT(*) FROM pipeline_quality_audit;")).scalar()
        row = conn.execute(text("SELECT check_name, status FROM pipeline_quality_audit LIMIT 1;")).fetchone()

    assert count == 1
    assert row[0] == "01_null_duplicate_orders"
    assert row[1] == "PASS"
