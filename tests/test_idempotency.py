"""Unit tests for ELT pipeline idempotency and duplicate prevention."""

from __future__ import annotations

from pathlib import Path
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.pipeline.load_raw import load_all_raw_data, load_raw_table


def test_raw_loading_idempotent(mock_raw_data_dir: Path, test_engine: Engine):
    """Assert that running the raw loading twice produces identical row counts without duplicating records."""
    # First Execution
    counts_first = load_all_raw_data(mock_raw_data_dir, test_engine)
    with test_engine.connect() as conn:
        orders_cnt_1 = conn.execute(text("SELECT COUNT(*) FROM raw_orders;")).scalar()
        items_cnt_1 = conn.execute(text("SELECT COUNT(*) FROM raw_order_items;")).scalar()
        payments_cnt_1 = conn.execute(text("SELECT COUNT(*) FROM raw_order_payments;")).scalar()

    assert orders_cnt_1 == 2
    assert items_cnt_1 == 3
    assert payments_cnt_1 == 3

    # Second Execution (Idempotency Test)
    counts_second = load_all_raw_data(mock_raw_data_dir, test_engine)
    with test_engine.connect() as conn:
        orders_cnt_2 = conn.execute(text("SELECT COUNT(*) FROM raw_orders;")).scalar()
        items_cnt_2 = conn.execute(text("SELECT COUNT(*) FROM raw_order_items;")).scalar()
        payments_cnt_2 = conn.execute(text("SELECT COUNT(*) FROM raw_order_payments;")).scalar()

    # Verify counts did not double
    assert orders_cnt_2 == orders_cnt_1
    assert items_cnt_2 == items_cnt_1
    assert payments_cnt_2 == payments_cnt_1


def test_duplicate_prevention_on_conflict(mock_raw_data_dir: Path, test_engine: Engine):
    """Assert that re-running with unchanged files maintains financial totals."""
    load_all_raw_data(mock_raw_data_dir, test_engine)

    with test_engine.connect() as conn:
        sum_payments_1 = conn.execute(text("SELECT SUM(payment_value) FROM raw_order_payments;")).scalar()

    # Re-run
    load_all_raw_data(mock_raw_data_dir, test_engine)

    with test_engine.connect() as conn:
        sum_payments_2 = conn.execute(text("SELECT SUM(payment_value) FROM raw_order_payments;")).scalar()

    assert sum_payments_1 == sum_payments_2
