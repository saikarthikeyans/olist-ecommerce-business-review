"""Pytest configuration and test fixtures for Olist Weekly Business Review."""

from __future__ import annotations

import csv
from pathlib import Path
import pytest
from sqlalchemy import create_engine, text
from sqlalchemy.engine import Engine

from backend.db.migrations import run_migrations
from backend.pipeline.extract import REQUIRED_DATASETS


@pytest.fixture
def mock_raw_data_dir(tmp_path: Path) -> Path:
    """Creates a temporary mock dataset folder containing all 9 valid CSV files."""
    data_dir = tmp_path / "raw"
    data_dir.mkdir()

    # 1. Orders
    with open(data_dir / "olist_orders_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_orders_dataset.csv"]["required_columns"])
        writer.writerow(["ord_1", "cust_1", "delivered", "2017-01-01 10:00:00", "2017-01-01 11:00:00", "2017-01-03 10:00:00", "2017-01-05 15:00:00", "2017-01-10 00:00:00"])
        writer.writerow(["ord_2", "cust_2", "delivered", "2017-01-02 10:00:00", "2017-01-02 11:00:00", "2017-01-04 10:00:00", "2017-01-15 15:00:00", "2017-01-12 00:00:00"])

    # 2. Customers
    with open(data_dir / "olist_customers_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_customers_dataset.csv"]["required_columns"])
        writer.writerow(["cust_1", "uniq_1", "01001", "sao paulo", "SP"])
        writer.writerow(["cust_2", "uniq_1", "01001", "sao paulo", "SP"])  # Same unique customer (repeat buyer)

    # 3. Order Items
    with open(data_dir / "olist_order_items_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_order_items_dataset.csv"]["required_columns"])
        writer.writerow(["ord_1", 1, "prod_1", "sell_1", "2017-01-05 10:00:00", "100.00", "15.00"])
        writer.writerow(["ord_1", 2, "prod_2", "sell_1", "2017-01-05 10:00:00", "50.00", "10.00"])
        writer.writerow(["ord_2", 1, "prod_1", "sell_2", "2017-01-06 10:00:00", "200.00", "20.00"])

    # 4. Order Payments
    with open(data_dir / "olist_order_payments_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_order_payments_dataset.csv"]["required_columns"])
        writer.writerow(["ord_1", 1, "credit_card", 2, "100.00"])
        writer.writerow(["ord_1", 2, "voucher", 1, "75.00"])
        writer.writerow(["ord_2", 1, "credit_card", 1, "220.00"])

    # 5. Order Reviews
    with open(data_dir / "olist_order_reviews_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_order_reviews_dataset.csv"]["required_columns"])
        writer.writerow(["rev_1", "ord_1", 5, "Great", "Good service", "2017-01-06 00:00:00", "2017-01-06 12:00:00"])
        writer.writerow(["rev_2", "ord_2", 2, "Late", "Arrived late", "2017-01-16 00:00:00", "2017-01-16 12:00:00"])

    # 6. Products
    with open(data_dir / "olist_products_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_products_dataset.csv"]["required_columns"])
        writer.writerow(["prod_1", "beleza_saude", 40, 200, 1, 300, 15, 10, 10])
        writer.writerow(["prod_2", "cama_mesa_banho", 35, 150, 2, 500, 20, 15, 15])

    # 7. Sellers
    with open(data_dir / "olist_sellers_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_sellers_dataset.csv"]["required_columns"])
        writer.writerow(["sell_1", "13000", "campinas", "SP"])
        writer.writerow(["sell_2", "20000", "rio de janeiro", "RJ"])

    # 8. Geolocation
    with open(data_dir / "olist_geolocation_dataset.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["olist_geolocation_dataset.csv"]["required_columns"])
        writer.writerow(["01001", "-23.55", "-46.63", "sao paulo", "SP"])

    # 9. Translation
    with open(data_dir / "product_category_name_translation.csv", "w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(REQUIRED_DATASETS["product_category_name_translation.csv"]["required_columns"])
        writer.writerow(["beleza_saude", "health_beauty"])
        writer.writerow(["cama_mesa_banho", "bed_bath_table"])

    return data_dir


@pytest.fixture
def test_engine() -> Engine:
    """Provides an in-memory SQLite database initialized with core tables for testing."""
    engine = create_engine("sqlite:///:memory:", future=True)

    # DDL for SQLite in-memory test environment
    ddl = """
    CREATE TABLE raw_customers (
        customer_id TEXT PRIMARY KEY,
        customer_unique_id TEXT,
        customer_zip_code_prefix TEXT,
        customer_city TEXT,
        customer_state TEXT,
        _loaded_at TEXT
    );
    CREATE TABLE raw_orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        order_status TEXT,
        order_purchase_timestamp TEXT,
        order_approved_at TEXT,
        order_delivered_carrier_date TEXT,
        order_delivered_customer_date TEXT,
        order_estimated_delivery_date TEXT,
        _loaded_at TEXT
    );
    CREATE TABLE raw_order_items (
        order_id TEXT,
        order_item_id INTEGER,
        product_id TEXT,
        seller_id TEXT,
        shipping_limit_date TEXT,
        price REAL,
        freight_value REAL,
        _loaded_at TEXT,
        PRIMARY KEY (order_id, order_item_id)
    );
    CREATE TABLE raw_order_payments (
        order_id TEXT,
        payment_sequential INTEGER,
        payment_type TEXT,
        payment_installments INTEGER,
        payment_value REAL,
        _loaded_at TEXT,
        PRIMARY KEY (order_id, payment_sequential)
    );
    CREATE TABLE raw_order_reviews (
        review_id TEXT,
        order_id TEXT,
        review_score INTEGER,
        review_comment_title TEXT,
        review_comment_message TEXT,
        review_creation_date TEXT,
        review_answer_timestamp TEXT,
        _loaded_at TEXT,
        PRIMARY KEY (review_id, order_id)
    );
    CREATE TABLE raw_products (
        product_id TEXT PRIMARY KEY,
        product_category_name TEXT,
        product_name_lenght INTEGER,
        product_description_lenght INTEGER,
        product_photos_qty INTEGER,
        product_weight_g REAL,
        product_length_cm REAL,
        product_height_cm REAL,
        product_width_cm REAL,
        _loaded_at TEXT
    );
    CREATE TABLE raw_sellers (
        seller_id TEXT PRIMARY KEY,
        seller_zip_code_prefix TEXT,
        seller_city TEXT,
        seller_state TEXT,
        _loaded_at TEXT
    );
    CREATE TABLE raw_geolocation (
        geolocation_zip_code_prefix TEXT,
        geolocation_lat REAL,
        geolocation_lng REAL,
        geolocation_city TEXT,
        geolocation_state TEXT,
        _loaded_at TEXT
    );
    CREATE TABLE raw_product_category_translation (
        product_category_name TEXT PRIMARY KEY,
        product_category_name_english TEXT,
        _loaded_at TEXT
    );

    CREATE TABLE stg_customers (
        customer_id TEXT PRIMARY KEY,
        customer_unique_id TEXT,
        customer_zip_code_prefix TEXT,
        customer_city TEXT,
        customer_state TEXT,
        _staged_at TEXT
    );
    CREATE TABLE stg_orders (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        order_status TEXT,
        order_purchase_timestamp TEXT,
        order_approved_at TEXT,
        order_delivered_carrier_date TEXT,
        order_delivered_customer_date TEXT,
        order_estimated_delivery_date TEXT,
        _staged_at TEXT
    );
    CREATE TABLE stg_order_items (
        order_id TEXT,
        order_item_id INTEGER,
        product_id TEXT,
        seller_id TEXT,
        shipping_limit_date TEXT,
        price REAL,
        freight_value REAL,
        _staged_at TEXT,
        PRIMARY KEY (order_id, order_item_id)
    );
    CREATE TABLE stg_order_payments (
        order_id TEXT,
        payment_sequential INTEGER,
        payment_type TEXT,
        payment_installments INTEGER,
        payment_value REAL,
        _staged_at TEXT,
        PRIMARY KEY (order_id, payment_sequential)
    );
    CREATE TABLE stg_order_reviews (
        review_id TEXT,
        order_id TEXT,
        review_score INTEGER,
        review_comment_title TEXT,
        review_comment_message TEXT,
        review_creation_date TEXT,
        review_answer_timestamp TEXT,
        _staged_at TEXT,
        PRIMARY KEY (review_id, order_id)
    );
    CREATE TABLE stg_products (
        product_id TEXT PRIMARY KEY,
        product_category_name TEXT,
        product_category_name_english TEXT,
        product_name_length INTEGER,
        product_description_length INTEGER,
        product_photos_qty INTEGER,
        product_weight_g REAL,
        product_length_cm REAL,
        product_height_cm REAL,
        product_width_cm REAL,
        _staged_at TEXT
    );
    CREATE TABLE stg_sellers (
        seller_id TEXT PRIMARY KEY,
        seller_zip_code_prefix TEXT,
        seller_city TEXT,
        seller_state TEXT,
        _staged_at TEXT
    );

    CREATE TABLE mart_order_performance (
        order_id TEXT PRIMARY KEY,
        customer_id TEXT,
        customer_unique_id TEXT,
        customer_state TEXT,
        order_status TEXT,
        order_purchase_timestamp TEXT,
        order_approved_at TEXT,
        order_delivered_carrier_date TEXT,
        order_delivered_customer_date TEXT,
        order_estimated_delivery_date TEXT,
        total_item_value REAL,
        total_freight_value REAL,
        total_order_value REAL,
        total_payment_value REAL,
        items_count INTEGER,
        payments_count INTEGER,
        review_score INTEGER,
        delivery_delay_days REAL,
        is_on_time INTEGER,
        order_sequence_number INTEGER,
        is_repeat_purchase INTEGER,
        is_repeat_customer INTEGER,
        _mart_created_at TEXT
    );

    CREATE TABLE pipeline_quality_audit (
        audit_id INTEGER PRIMARY KEY AUTOINCREMENT,
        check_name TEXT,
        check_category TEXT,
        execution_timestamp TEXT,
        threshold_limit INTEGER,
        failed_count INTEGER,
        status TEXT,
        sample_failing_identifiers TEXT,
        details TEXT
    );
    """
    with engine.begin() as conn:
        for stmt in ddl.split(";"):
            if stmt.strip():
                conn.execute(text(stmt))

    return engine
