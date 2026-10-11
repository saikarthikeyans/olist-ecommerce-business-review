"""Staging transformation module for Olist Weekly Business Review.

Cleanses, normalizes, casts data types, standardizes column names, and deduplicates
records from raw_* tables into stg_* tables.
"""

from __future__ import annotations

import logging
import time
from typing import Dict, Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.config import setup_logging
from backend.db.connection import get_engine

logger = setup_logging()


def transform_staging_tables(engine: Optional[Engine] = None) -> Dict[str, int]:
    """Execute transformations from raw tables into cleaned staging tables.

    Returns:
        Mapping of staging table names to their row counts.
    """
    eng = engine or get_engine()
    start_time = time.time()
    is_postgres = eng.dialect.name == "postgresql"

    logger.info("Transforming raw layer into cleaned staging layer...")

    # SQL for PostgreSQL dialect
    pg_transforms = {
        "stg_customers": """
            INSERT INTO stg_customers (
                customer_id, customer_unique_id, customer_zip_code_prefix,
                customer_city, customer_state, _staged_at
            )
            SELECT 
                TRIM(customer_id),
                TRIM(customer_unique_id),
                NULLIF(TRIM(customer_zip_code_prefix), ''),
                NULLIF(LOWER(TRIM(customer_city)), ''),
                NULLIF(UPPER(TRIM(customer_state)), ''),
                CURRENT_TIMESTAMP
            FROM raw_customers
            WHERE customer_id IS NOT NULL AND TRIM(customer_id) != '';
        """,
        "stg_orders": """
            INSERT INTO stg_orders (
                order_id, customer_id, order_status,
                order_purchase_timestamp, order_approved_at,
                order_delivered_carrier_date, order_delivered_customer_date,
                order_estimated_delivery_date, _staged_at
            )
            SELECT 
                TRIM(order_id),
                TRIM(customer_id),
                LOWER(TRIM(order_status)),
                order_purchase_timestamp::TIMESTAMPTZ,
                NULLIF(order_approved_at, '')::TIMESTAMPTZ,
                NULLIF(order_delivered_carrier_date, '')::TIMESTAMPTZ,
                NULLIF(order_delivered_customer_date, '')::TIMESTAMPTZ,
                order_estimated_delivery_date::TIMESTAMPTZ,
                CURRENT_TIMESTAMP
            FROM raw_orders
            WHERE order_id IS NOT NULL AND TRIM(order_id) != '';
        """,
        "stg_order_items": """
            INSERT INTO stg_order_items (
                order_id, order_item_id, product_id, seller_id,
                shipping_limit_date, price, freight_value, _staged_at
            )
            SELECT 
                TRIM(order_id),
                order_item_id::INTEGER,
                TRIM(product_id),
                TRIM(seller_id),
                NULLIF(shipping_limit_date, '')::TIMESTAMPTZ,
                COALESCE(price::NUMERIC(12, 2), 0.00),
                COALESCE(freight_value::NUMERIC(12, 2), 0.00),
                CURRENT_TIMESTAMP
            FROM raw_order_items
            WHERE order_id IS NOT NULL AND order_item_id IS NOT NULL;
        """,
        "stg_order_payments": """
            INSERT INTO stg_order_payments (
                order_id, payment_sequential, payment_type,
                payment_installments, payment_value, _staged_at
            )
            SELECT 
                TRIM(order_id),
                payment_sequential::INTEGER,
                LOWER(TRIM(payment_type)),
                COALESCE(payment_installments::INTEGER, 1),
                COALESCE(payment_value::NUMERIC(12, 2), 0.00),
                CURRENT_TIMESTAMP
            FROM raw_order_payments
            WHERE order_id IS NOT NULL AND payment_sequential IS NOT NULL;
        """,
        "stg_order_reviews": """
            WITH deduplicated_reviews AS (
                SELECT 
                    TRIM(review_id) AS review_id,
                    TRIM(order_id) AS order_id,
                    review_score::INTEGER AS review_score,
                    NULLIF(TRIM(review_comment_title), '') AS review_comment_title,
                    NULLIF(TRIM(review_comment_message), '') AS review_comment_message,
                    NULLIF(review_creation_date, '')::TIMESTAMPTZ AS review_creation_date,
                    NULLIF(review_answer_timestamp, '')::TIMESTAMPTZ AS review_answer_timestamp,
                    ROW_NUMBER() OVER (
                        PARTITION BY TRIM(review_id), TRIM(order_id)
                        ORDER BY NULLIF(review_answer_timestamp, '')::TIMESTAMPTZ DESC NULLS LAST,
                                 NULLIF(review_creation_date, '')::TIMESTAMPTZ DESC NULLS LAST
                    ) AS rn
                FROM raw_order_reviews
                WHERE review_id IS NOT NULL AND order_id IS NOT NULL
            )
            INSERT INTO stg_order_reviews (
                review_id, order_id, review_score,
                review_comment_title, review_comment_message,
                review_creation_date, review_answer_timestamp, _staged_at
            )
            SELECT 
                review_id, order_id, review_score,
                review_comment_title, review_comment_message,
                review_creation_date, review_answer_timestamp, CURRENT_TIMESTAMP
            FROM deduplicated_reviews
            WHERE rn = 1;
        """,
        "stg_products": """
            INSERT INTO stg_products (
                product_id, product_category_name, product_category_name_english,
                product_name_length, product_description_length, product_photos_qty,
                product_weight_g, product_length_cm, product_height_cm, product_width_cm, _staged_at
            )
            SELECT 
                TRIM(p.product_id),
                NULLIF(LOWER(TRIM(p.product_category_name)), ''),
                COALESCE(NULLIF(TRIM(t.product_category_name_english), ''), NULLIF(LOWER(TRIM(p.product_category_name)), ''), 'unspecified'),
                p.product_name_lenght::INTEGER,
                p.product_description_lenght::INTEGER,
                p.product_photos_qty::INTEGER,
                p.product_weight_g::NUMERIC(10, 2),
                p.product_length_cm::NUMERIC(10, 2),
                p.product_height_cm::NUMERIC(10, 2),
                p.product_width_cm::NUMERIC(10, 2),
                CURRENT_TIMESTAMP
            FROM raw_products p
            LEFT JOIN raw_product_category_translation t ON LOWER(TRIM(p.product_category_name)) = LOWER(TRIM(t.product_category_name))
            WHERE p.product_id IS NOT NULL;
        """,
        "stg_sellers": """
            INSERT INTO stg_sellers (
                seller_id, seller_zip_code_prefix, seller_city, seller_state, _staged_at
            )
            SELECT 
                TRIM(seller_id),
                NULLIF(TRIM(seller_zip_code_prefix), ''),
                NULLIF(LOWER(TRIM(seller_city)), ''),
                NULLIF(UPPER(TRIM(seller_state)), ''),
                CURRENT_TIMESTAMP
            FROM raw_sellers
            WHERE seller_id IS NOT NULL;
        """,
    }

    # SQLite dialect fallback transforms
    sqlite_transforms = {
        "stg_customers": """
            INSERT INTO stg_customers (
                customer_id, customer_unique_id, customer_zip_code_prefix,
                customer_city, customer_state, _staged_at
            )
            SELECT 
                TRIM(customer_id), TRIM(customer_unique_id),
                TRIM(customer_zip_code_prefix), LOWER(TRIM(customer_city)),
                UPPER(TRIM(customer_state)), datetime('now')
            FROM raw_customers;
        """,
        "stg_orders": """
            INSERT INTO stg_orders (
                order_id, customer_id, order_status,
                order_purchase_timestamp, order_approved_at,
                order_delivered_carrier_date, order_delivered_customer_date,
                order_estimated_delivery_date, _staged_at
            )
            SELECT 
                TRIM(order_id), TRIM(customer_id), LOWER(TRIM(order_status)),
                order_purchase_timestamp, order_approved_at,
                order_delivered_carrier_date, order_delivered_customer_date,
                order_estimated_delivery_date, datetime('now')
            FROM raw_orders;
        """,
        "stg_order_items": """
            INSERT INTO stg_order_items (
                order_id, order_item_id, product_id, seller_id,
                shipping_limit_date, price, freight_value, _staged_at
            )
            SELECT 
                TRIM(order_id), CAST(order_item_id AS INTEGER),
                TRIM(product_id), TRIM(seller_id),
                shipping_limit_date, CAST(price AS REAL),
                CAST(freight_value AS REAL), datetime('now')
            FROM raw_order_items;
        """,
        "stg_order_payments": """
            INSERT INTO stg_order_payments (
                order_id, payment_sequential, payment_type,
                payment_installments, payment_value, _staged_at
            )
            SELECT 
                TRIM(order_id), CAST(payment_sequential AS INTEGER),
                LOWER(TRIM(payment_type)), CAST(payment_installments AS INTEGER),
                CAST(payment_value AS REAL), datetime('now')
            FROM raw_order_payments;
        """,
        "stg_order_reviews": """
            INSERT INTO stg_order_reviews (
                review_id, order_id, review_score,
                review_comment_title, review_comment_message,
                review_creation_date, review_answer_timestamp, _staged_at
            )
            SELECT 
                TRIM(review_id), TRIM(order_id), CAST(review_score AS INTEGER),
                TRIM(review_comment_title), TRIM(review_comment_message),
                review_creation_date, review_answer_timestamp, datetime('now')
            FROM raw_order_reviews;
        """,
        "stg_products": """
            INSERT INTO stg_products (
                product_id, product_category_name, product_category_name_english,
                product_name_length, product_description_length, product_photos_qty,
                product_weight_g, product_length_cm, product_height_cm, product_width_cm, _staged_at
            )
            SELECT 
                TRIM(p.product_id), LOWER(TRIM(p.product_category_name)),
                COALESCE(t.product_category_name_english, p.product_category_name, 'unspecified'),
                CAST(p.product_name_lenght AS INTEGER), CAST(p.product_description_lenght AS INTEGER),
                CAST(p.product_photos_qty AS INTEGER), CAST(p.product_weight_g AS REAL),
                CAST(p.product_length_cm AS REAL), CAST(p.product_height_cm AS REAL),
                CAST(p.product_width_cm AS REAL), datetime('now')
            FROM raw_products p
            LEFT JOIN raw_product_category_translation t ON p.product_category_name = t.product_category_name;
        """,
        "stg_sellers": """
            INSERT INTO stg_sellers (
                seller_id, seller_zip_code_prefix, seller_city, seller_state, _staged_at
            )
            SELECT 
                TRIM(seller_id), TRIM(seller_zip_code_prefix),
                LOWER(TRIM(seller_city)), UPPER(TRIM(seller_state)), datetime('now')
            FROM raw_sellers;
        """,
    }

    transforms = pg_transforms if is_postgres else sqlite_transforms
    counts: Dict[str, int] = {}

    for table_name, query in transforms.items():
        with eng.begin() as conn:
            truncate_stmt = f"TRUNCATE TABLE {table_name};" if is_postgres else f"DELETE FROM {table_name};"
            conn.execute(text(truncate_stmt))
            conn.execute(text(query))

            # Retrieve staged row count
            count_res = conn.execute(text(f"SELECT COUNT(*) FROM {table_name};")).scalar()
            counts[table_name] = count_res or 0
            logger.info("Staged '%s': %d rows.", table_name, counts[table_name])

    elapsed = time.time() - start_time
    logger.info("Staging transformation completed in %.2f seconds.", elapsed)
    return counts
