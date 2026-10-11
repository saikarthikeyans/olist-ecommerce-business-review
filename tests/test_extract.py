"""Unit tests for dataset extraction and pre-flight schema validation."""

from __future__ import annotations

from pathlib import Path
import pytest

from backend.pipeline.extract import (
    DatasetNotFoundError,
    DatasetSchemaError,
    run_extraction_checks,
    verify_file_columns,
    verify_files_exist,
)


def test_verify_files_exist_success(mock_raw_data_dir: Path):
    """Assert all 9 files are recognized when present."""
    files = verify_files_exist(mock_raw_data_dir)
    assert len(files) == 9


def test_verify_files_exist_missing_file_raises(mock_raw_data_dir: Path):
    """Assert DatasetNotFoundError is raised when a file is missing."""
    orders_file = mock_raw_data_dir / "olist_orders_dataset.csv"
    orders_file.unlink()

    with pytest.raises(DatasetNotFoundError) as exc_info:
        verify_files_exist(mock_raw_data_dir)

    assert "olist_orders_dataset.csv" in str(exc_info.value)


def test_verify_file_columns_success(mock_raw_data_dir: Path):
    """Assert all required columns pass validation."""
    headers = verify_file_columns(mock_raw_data_dir)
    assert len(headers) == 9
    assert "order_id" in headers["olist_orders_dataset.csv"]
    assert "customer_unique_id" in headers["olist_customers_dataset.csv"]


def test_verify_file_columns_missing_col_raises(mock_raw_data_dir: Path):
    """Assert DatasetSchemaError is raised when a required column is missing."""
    payments_file = mock_raw_data_dir / "olist_order_payments_dataset.csv"
    # Overwrite with missing payment_value column
    payments_file.write_text("order_id,payment_sequential,payment_type\nord_1,1,credit_card\n", encoding="utf-8")

    with pytest.raises(DatasetSchemaError) as exc_info:
        verify_file_columns(mock_raw_data_dir)

    assert "payment_value" in str(exc_info.value)


def test_run_extraction_checks_success(mock_raw_data_dir: Path):
    """Assert high-level extraction check passes with valid mock data."""
    mapping = run_extraction_checks(mock_raw_data_dir)
    assert len(mapping) == 9
