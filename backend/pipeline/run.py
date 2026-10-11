"""Executable ELT pipeline entrypoint for Olist Weekly Business Review.

Command:
    python -m backend.pipeline.run

Stages:
  1. Configuration & Supabase Connectivity Verification
  2. Dataset File Presence & Column Schema Validation
  3. Schema Migrations (Raw, Staging, Mart, Audit)
  4. Idempotent Raw Layer Ingestion
  5. Staging Cleansing, Deduplication & Normalization
  6. Mart Build (mart_order_performance)
  7. Data Quality Suite Execution & Audit Logging
"""

from __future__ import annotations

import logging
import sys
import time
from typing import Dict, Any

from backend.config import DATA_RAW_DIR, DATABASE_URL, setup_logging
from backend.db.connection import check_db_connectivity, get_engine
from backend.db.migrations import run_migrations
from backend.pipeline.build_mart import build_order_performance_mart
from backend.pipeline.extract import DatasetNotFoundError, DatasetSchemaError, run_extraction_checks
from backend.pipeline.load_raw import load_all_raw_data
from backend.pipeline.transform_stg import transform_staging_tables
from backend.quality.runner import CriticalQualityCheckFailure, run_all_quality_checks

logger = setup_logging()


def run_pipeline() -> int:
    """Execute the end-to-end idempotent ELT pipeline.

    Returns:
        0 on success, non-zero exit code on failure.
    """
    total_start = time.time()
    logger.info("=" * 80)
    logger.info("STARTING OLIST WEEKLY BUSINESS REVIEW ELT PIPELINE")
    logger.info("=" * 80)

    # --------------------------------------------------------------------------
    # STAGE 1: Configuration & Connectivity
    # --------------------------------------------------------------------------
    logger.info("[STAGE 1/7] Checking database connectivity and configuration...")
    if not DATABASE_URL:
        logger.error(
            "CRITICAL: DATABASE_URL is not configured in .env.\n"
            "Please create a .env file based on .env.example with your Supabase connection string:\n"
            "DATABASE_URL=postgresql+psycopg://postgres:[password]@db.[project-ref].supabase.co:5432/postgres"
        )
        return 1

    try:
        engine = get_engine()
        is_connected, msg = check_db_connectivity(engine)
        if not is_connected:
            logger.error("CRITICAL: Database connection failed: %s", msg)
            return 1
        logger.info("Database check passed: %s", msg)
    except Exception as exc:
        logger.error("CRITICAL: Database initialization error: %s", str(exc))
        return 1

    # --------------------------------------------------------------------------
    # STAGE 2: Extract & Pre-flight Schema Validation
    # --------------------------------------------------------------------------
    logger.info("[STAGE 2/7] Verifying dataset file existence and column schemas...")
    try:
        validated_files = run_extraction_checks(DATA_RAW_DIR)
        logger.info("Dataset validation passed (%d files verified).", len(validated_files))
    except DatasetNotFoundError as exc:
        logger.error("CRITICAL: Dataset file presence check failed:\n%s", str(exc))
        return 2
    except DatasetSchemaError as exc:
        logger.error("CRITICAL: CSV schema column check failed:\n%s", str(exc))
        return 2

    # --------------------------------------------------------------------------
    # STAGE 3: Database Migrations (Raw, Staging, Mart, Audit)
    # --------------------------------------------------------------------------
    logger.info("[STAGE 3/7] Applying database schema migrations...")
    try:
        run_migrations(engine)
    except Exception as exc:
        logger.error("CRITICAL: Schema migration failed: %s", str(exc))
        return 4

    # --------------------------------------------------------------------------
    # STAGE 4: Idempotent Raw Ingestion
    # --------------------------------------------------------------------------
    logger.info("[STAGE 4/7] Loading CSV records into raw_* tables...")
    try:
        raw_counts = load_all_raw_data(DATA_RAW_DIR, engine)
    except Exception as exc:
        logger.error("CRITICAL: Raw layer ingestion failed: %s", str(exc))
        return 4

    # --------------------------------------------------------------------------
    # STAGE 5: Staging Transformation & Cleansing
    # --------------------------------------------------------------------------
    logger.info("[STAGE 5/7] Transforming raw data into cleaned staging tables...")
    try:
        stg_counts = transform_staging_tables(engine)
    except Exception as exc:
        logger.error("CRITICAL: Staging transformations failed: %s", str(exc))
        return 4
    finally:
        engine.dispose()

    # --------------------------------------------------------------------------
    # STAGE 6: Mart Layer Build (mart_order_performance)
    # --------------------------------------------------------------------------
    logger.info("[STAGE 6/7] Building analytical mart (mart_order_performance)...")
    try:
        mart_orders = build_order_performance_mart(engine)
    except Exception as exc:
        logger.error("CRITICAL: Mart construction failed: %s", str(exc))
        return 4
    finally:
        engine.dispose()

    # --------------------------------------------------------------------------
    # STAGE 7: Data Quality Suite Execution
    # --------------------------------------------------------------------------
    logger.info("[STAGE 7/7] Executing SQL Data Quality Verification Suite...")
    try:
        dq_results = run_all_quality_checks(engine, halt_on_critical=True)
    except CriticalQualityCheckFailure as exc:
        logger.error("CRITICAL: Data Quality verification failed:\n%s", str(exc))
        return 3
    except Exception as exc:
        logger.error("CRITICAL: Unexpected error during quality checks: %s", str(exc))
        return 4
    finally:
        engine.dispose()

    # --------------------------------------------------------------------------
    # Final Execution Summary
    # --------------------------------------------------------------------------
    total_elapsed = time.time() - total_start
    print("\n" + "=" * 80)
    print(f"{'ELT PIPELINE EXECUTION SUMMARY':^80}")
    print("=" * 80)
    print(f"  Status:                   SUCCESS")
    print(f"  Total Duration:           {total_elapsed:.2f} seconds")
    print(f"  Raw Tables Populated:     {len(raw_counts)}")
    print(f"  Staging Tables Populated: {len(stg_counts)}")
    print(f"  Analysis Mart Orders:     {mart_orders:,} orders")
    print(f"  Quality Checks Executed:  {len(dq_results)} checks (0 Critical Failures)")
    print("=" * 80 + "\n")

    logger.info("ELT Pipeline completed successfully in %.2f seconds.", total_elapsed)
    return 0


if __name__ == "__main__":
    exit_code = run_pipeline()
    sys.exit(exit_code)
