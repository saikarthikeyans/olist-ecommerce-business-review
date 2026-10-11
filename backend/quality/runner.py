"""Data Quality test runner and audit logger for Olist Weekly Business Review.

Executes standalone SQL checks, logs failures, persists audit history to
pipeline_quality_audit, and halts execution on critical failures.
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.config import QUALITY_SQL_DIR, setup_logging
from backend.db.connection import get_engine

logger = setup_logging()


class CriticalQualityCheckFailure(Exception):
    """Raised when one or more CRITICAL quality checks fail, terminating the pipeline."""
    pass


QUALITY_CHECK_FILES = [
    "01_null_duplicate_orders.sql",
    "02_delivered_before_purchase.sql",
    "03_payment_vs_order_value.sql",
    "04_orphan_orders.sql",
    "05_invalid_review_scores.sql",
    "06_delivery_date_anomalies.sql",
]


def run_single_check(file_path: Path, engine: Engine) -> Dict[str, Any]:
    """Execute a single quality check SQL script and parse its standardized result."""
    with open(file_path, "r", encoding="utf-8") as f:
        query = f.read()

    with engine.connect() as conn:
        result = conn.execute(text(query))
        row = result.fetchone()
        columns = list(result.keys())

    if not row:
        raise ValueError(f"Quality check script {file_path.name} did not return any result row.")

    data = dict(zip(columns, row))
    return data


def log_and_record_check(check_result: Dict[str, Any], engine: Engine) -> None:
    """Persist check execution result into pipeline_quality_audit table."""
    is_postgres = engine.dialect.name == "postgresql"

    # Only persist if table exists
    try:
        sample_json = json.dumps(str(check_result.get("sample_failing_identifiers", "none")))
        with engine.begin() as conn:
            if is_postgres:
                insert_stmt = text("""
                    INSERT INTO pipeline_quality_audit (
                        check_name, check_category, threshold_limit,
                        failed_count, status, sample_failing_identifiers, details
                    ) VALUES (
                        :check_name, :severity, :threshold,
                        :failed_count, :status, CAST(:samples AS JSONB), :details
                    );
                """)
            else:
                insert_stmt = text("""
                    INSERT INTO pipeline_quality_audit (
                        check_name, check_category, threshold_limit,
                        failed_count, status, sample_failing_identifiers, details
                    ) VALUES (
                        :check_name, :severity, :threshold,
                        :failed_count, :status, :samples, :details
                    );
                """)

            conn.execute(
                insert_stmt,
                {
                    "check_name": check_result.get("check_name"),
                    "severity": check_result.get("severity", "WARNING"),
                    "threshold": int(check_result.get("threshold", 0)),
                    "failed_count": int(check_result.get("failed_count", 0)),
                    "status": check_result.get("status", "FAIL"),
                    "samples": sample_json,
                    "details": check_result.get("details", ""),
                },
            )
    except Exception as exc:
        logger.warning("Could not persist audit record to pipeline_quality_audit: %s", str(exc))


def run_all_quality_checks(
    engine: Optional[Engine] = None,
    quality_dir: Optional[Path] = None,
    halt_on_critical: bool = True,
) -> List[Dict[str, Any]]:
    """Execute all quality check scripts, print a summary report, and validate thresholds.

    Returns:
        List of check outcome dictionaries.

    Raises:
        CriticalQualityCheckFailure: If any CRITICAL check fails and halt_on_critical is True.
    """
    eng = engine or get_engine()
    target_dir = quality_dir or QUALITY_SQL_DIR

    logger.info("Executing Data Quality Verification Suite from: %s", target_dir)

    results: List[Dict[str, Any]] = []
    critical_failures: List[Dict[str, Any]] = []

    print("\n" + "=" * 90)
    print(f"{'DATA QUALITY VERIFICATION REPORT':^90}")
    print("=" * 90)
    print(f"{'Check Name':<32} {'Severity':<10} {'Failed':<8} {'Threshold':<10} {'Status':<8}")
    print("-" * 90)

    for file_name in QUALITY_CHECK_FILES:
        file_path = target_dir / file_name
        if not file_path.exists():
            logger.error("Quality check file missing: %s", file_path)
            continue

        try:
            res = run_single_check(file_path, eng)
            results.append(res)
            log_and_record_check(res, eng)

            check_name = res.get("check_name", file_name)
            severity = res.get("severity", "UNKNOWN")
            failed_count = res.get("failed_count", 0)
            threshold = res.get("threshold", 0)
            status = res.get("status", "FAIL")

            print(f"{check_name:<32} {severity:<10} {failed_count:<8} {threshold:<10} {status:<8}")

            if status == "FAIL" and severity == "CRITICAL":
                critical_failures.append(res)
        except Exception as e:
            logger.error("Error executing %s: %s", file_name, str(e))
            fail_record = {
                "check_name": file_name,
                "severity": "CRITICAL",
                "threshold": 0,
                "failed_count": -1,
                "status": "ERROR",
                "sample_failing_identifiers": "execution_error",
                "details": str(e),
            }
            results.append(fail_record)
            critical_failures.append(fail_record)

    print("=" * 90 + "\n")

    if critical_failures and halt_on_critical:
        failure_summary = "\n".join(
            f"  - {f['check_name']} (Failed Rows: {f['failed_count']}, Samples: {f.get('sample_failing_identifiers')})"
            for f in critical_failures
        )
        raise CriticalQualityCheckFailure(
            f"Pipeline halted due to {len(critical_failures)} CRITICAL data quality check failures:\n"
            f"{failure_summary}\n"
            f"Action: Review source data and upstream ingestion before proceeding."
        )

    logger.info("Quality check suite finished. Total checks: %d, Critical failures: %d", len(results), len(critical_failures))
    return results


def get_latest_quality_audit(engine: Optional[Engine] = None) -> List[Dict[str, Any]]:
    """Retrieve the latest quality check outcomes from database."""
    eng = engine or get_engine()
    query = """
        SELECT DISTINCT ON (check_name)
            check_name,
            check_category,
            execution_timestamp,
            threshold_limit,
            failed_count,
            status,
            sample_failing_identifiers,
            details
        FROM pipeline_quality_audit
        ORDER BY check_name, execution_timestamp DESC;
    """
    try:
        with eng.connect() as conn:
            rows = conn.execute(text(query)).fetchall()
            return [dict(zip(rows[0].keys(), r)) for r in rows] if rows else []
    except Exception:
        return []
