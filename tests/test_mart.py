"""Unit tests for Mart layer aggregation and exact 1:1 order grain enforcement."""

from __future__ import annotations

from pathlib import Path
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.pipeline.build_mart import build_order_performance_mart
from backend.pipeline.load_raw import load_all_raw_data
from backend.pipeline.transform_stg import transform_staging_tables


def test_mart_exact_one_row_per_order(mock_raw_data_dir: Path, test_engine: Engine):
    """Assert mart_order_performance contains exactly one row per order_id (fan-out prevented)."""
    # Load and transform mock data
    load_all_raw_data(mock_raw_data_dir, test_engine)
    transform_staging_tables(test_engine)

    # Build mart
    mart_count = build_order_performance_mart(test_engine)

    with test_engine.connect() as conn:
        res = conn.execute(text("SELECT COUNT(*), COUNT(DISTINCT order_id) FROM mart_order_performance;")).fetchone()
        total_rows = res[0]
        distinct_orders = res[1]

    assert total_rows == 2
    assert distinct_orders == 2
    assert total_rows == distinct_orders


def test_mart_financial_aggregations(mock_raw_data_dir: Path, test_engine: Engine):
    """Assert items, payments, and reviews are pre-aggregated independently without cross-multiplication."""
    load_all_raw_data(mock_raw_data_dir, test_engine)
    transform_staging_tables(test_engine)
    build_order_performance_mart(test_engine)

    with test_engine.connect() as conn:
        # Check order 1 (which has 2 items: 100 and 50; 2 payments: 100 and 75)
        row = conn.execute(
            text("SELECT total_item_value, total_freight_value, total_payment_value, items_count, payments_count, review_score, is_on_time FROM mart_order_performance WHERE order_id = 'ord_1';")
        ).fetchone()

        total_item_val = row[0]
        total_freight = row[1]
        total_payment = row[2]
        items_cnt = row[3]
        payments_cnt = row[4]
        rev_score = row[5]
        on_time = row[6]

    # Verify no fan-out: If joined naively 2 items x 2 payments would give 4 rows and 2x sums
    assert total_item_val == 150.00
    assert total_freight == 25.00
    assert total_payment == 175.00
    assert items_cnt == 2
    assert payments_cnt == 2
    assert rev_score == 5
    assert bool(on_time) is True


def test_mart_late_delivery_flag(mock_raw_data_dir: Path, test_engine: Engine):
    """Assert late delivery (delivered 2017-01-15 vs estimated 2017-01-12) is flagged correctly."""
    load_all_raw_data(mock_raw_data_dir, test_engine)
    transform_staging_tables(test_engine)
    build_order_performance_mart(test_engine)

    with test_engine.connect() as conn:
        row = conn.execute(
            text("SELECT delivery_delay_days, is_on_time, review_score FROM mart_order_performance WHERE order_id = 'ord_2';")
        ).fetchone()

        delay_days = row[0]
        on_time = row[1]
        rev_score = row[2]

    assert delay_days > 0  # Delivered 3 days late
    assert bool(on_time) is False  # Marked late
    assert rev_score == 2
