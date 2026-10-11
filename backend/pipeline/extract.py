"""Extraction and pre-flight validation module for Olist dataset files.

Verifies presence of all 9 required Kaggle CSV files and validates schema
column conformance before any raw ingestion commences.
"""

from __future__ import annotations

import csv
from pathlib import Path
from typing import Dict, List, Set

from backend.config import DATA_RAW_DIR, setup_logging

logger = setup_logging()


class DatasetNotFoundError(FileNotFoundError):
    """Raised when one or more required Olist CSV dataset files are missing."""
    pass


class DatasetSchemaError(ValueError):
    """Raised when a CSV dataset file is missing required columns."""
    pass


# Strict dataset schema definitions
REQUIRED_DATASETS: Dict[str, Dict[str, any]] = {
    "olist_orders_dataset.csv": {
        "table": "raw_orders",
        "required_columns": [
            "order_id",
            "customer_id",
            "order_status",
            "order_purchase_timestamp",
            "order_approved_at",
            "order_delivered_carrier_date",
            "order_delivered_customer_date",
            "order_estimated_delivery_date",
        ],
    },
    "olist_customers_dataset.csv": {
        "table": "raw_customers",
        "required_columns": [
            "customer_id",
            "customer_unique_id",
            "customer_zip_code_prefix",
            "customer_city",
            "customer_state",
        ],
    },
    "olist_order_items_dataset.csv": {
        "table": "raw_order_items",
        "required_columns": [
            "order_id",
            "order_item_id",
            "product_id",
            "seller_id",
            "shipping_limit_date",
            "price",
            "freight_value",
        ],
    },
    "olist_order_payments_dataset.csv": {
        "table": "raw_order_payments",
        "required_columns": [
            "order_id",
            "payment_sequential",
            "payment_type",
            "payment_installments",
            "payment_value",
        ],
    },
    "olist_order_reviews_dataset.csv": {
        "table": "raw_order_reviews",
        "required_columns": [
            "review_id",
            "order_id",
            "review_score",
            "review_comment_title",
            "review_comment_message",
            "review_creation_date",
            "review_answer_timestamp",
        ],
    },
    "olist_products_dataset.csv": {
        "table": "raw_products",
        "required_columns": [
            "product_id",
            "product_category_name",
            "product_name_lenght",
            "product_description_lenght",
            "product_photos_qty",
            "product_weight_g",
            "product_length_cm",
            "product_height_cm",
            "product_width_cm",
        ],
    },
    "olist_sellers_dataset.csv": {
        "table": "raw_sellers",
        "required_columns": [
            "seller_id",
            "seller_zip_code_prefix",
            "seller_city",
            "seller_state",
        ],
    },
    "olist_geolocation_dataset.csv": {
        "table": "raw_geolocation",
        "required_columns": [
            "geolocation_zip_code_prefix",
            "geolocation_lat",
            "geolocation_lng",
            "geolocation_city",
            "geolocation_state",
        ],
    },
    "product_category_name_translation.csv": {
        "table": "raw_product_category_translation",
        "required_columns": [
            "product_category_name",
            "product_category_name_english",
        ],
    },
}


def verify_files_exist(raw_dir: Path | None = None) -> List[Path]:
    """Verify that every required CSV file exists in the raw directory.

    Raises:
        DatasetNotFoundError: If one or more files are missing, listing all missing filenames.
    """
    directory = raw_dir or DATA_RAW_DIR
    if not directory.exists():
        raise DatasetNotFoundError(
            f"Raw data directory does not exist: {directory.resolve()}.\n"
            f"Please create the directory and place the 9 Olist CSV files from Kaggle inside it."
        )

    missing_files: List[str] = []
    found_paths: List[Path] = []

    for filename in REQUIRED_DATASETS:
        file_path = directory / filename
        if not file_path.exists() or not file_path.is_file():
            missing_files.append(filename)
        else:
            found_paths.append(file_path)

    if missing_files:
        raise DatasetNotFoundError(
            f"Missing required Olist dataset files in {directory.resolve()}:\n"
            + "\n".join(f"  - {f}" for f in missing_files)
            + "\nDownload them from Kaggle (https://www.kaggle.com/datasets/olistbr/brazilian-ecommerce) "
            "and place them into data/raw/."
        )

    logger.info("Dataset presence verification passed: all %d required files detected.", len(found_paths))
    return found_paths


def verify_file_columns(raw_dir: Path | None = None) -> Dict[str, List[str]]:
    """Verify that every CSV file contains all required columns.

    Raises:
        DatasetSchemaError: If any CSV has missing columns.
    """
    directory = raw_dir or DATA_RAW_DIR
    schema_errors: List[str] = []
    validated_headers: Dict[str, List[str]] = {}

    for filename, meta in REQUIRED_DATASETS.items():
        file_path = directory / filename
        if not file_path.exists():
            continue

        try:
            with open(file_path, "r", encoding="utf-8", errors="replace") as f:
                reader = csv.reader(f)
                headers = next(reader, None)
                if not headers:
                    schema_errors.append(f"{filename}: File is completely empty.")
                    continue

                clean_headers = [h.lstrip('\ufeff').strip().replace('"', "") for h in headers]
                validated_headers[filename] = clean_headers
                header_set: Set[str] = set(clean_headers)

                missing_cols = [col for col in meta["required_columns"] if col not in header_set]
                if missing_cols:
                    schema_errors.append(
                        f"{filename}: Missing required columns: {', '.join(missing_cols)}"
                    )
        except Exception as e:
            schema_errors.append(f"{filename}: Failed to read CSV headers ({str(e)})")

    if schema_errors:
        raise DatasetSchemaError(
            "CSV Schema validation failed:\n" + "\n".join(f"  - {err}" for err in schema_errors)
        )

    logger.info("CSV column verification passed: all schemas match requirements.")
    return validated_headers


def run_extraction_checks(raw_dir: Path | None = None) -> Dict[str, Path]:
    """Execute pre-flight checks: presence and schema validation.

    Returns mapping of dataset filename to resolved file Path.
    """
    directory = raw_dir or DATA_RAW_DIR
    verify_files_exist(directory)
    verify_file_columns(directory)
    return {filename: directory / filename for filename in REQUIRED_DATASETS}
