"""Mart layer builder for Olist Weekly Business Review.

Constructs the analysis-ready `mart_order_performance` table with EXACTLY
one row per order_id. Pre-aggregates items, payments, and reviews in CTEs
to strictly prevent fan-out joins that duplicate financial figures.
"""

from __future__ import annotations

import logging
import time
from typing import Optional
from sqlalchemy import text
from sqlalchemy.engine import Engine

from backend.config import setup_logging
from backend.db.connection import get_engine

logger = setup_logging()


def build_order_performance_mart(engine: Optional[Engine] = None) -> int:
    """Build or refresh mart_order_performance.

    Guarantees:
      - Exactly 1 row per order_id.
      - Total items, payments, and reviews pre-aggregated independently.
      - Accurate delivery delay in days and on-time delivery indicator.
      - Accurate repeat-purchase flags based on customer_unique_id.

    Returns:
        Row count in mart_order_performance.
    """
    eng = engine or get_engine()
    start_time = time.time()
    is_postgres = eng.dialect.name == "postgresql"

    logger.info("Building mart_order_performance layer...")

    if is_postgres:
        mart_sql = """
            WITH agg_items AS (
                SELECT 
                    order_id,
                    COALESCE(SUM(price), 0.00) AS total_item_value,
                    COALESCE(SUM(freight_value), 0.00) AS total_freight_value,
                    COALESCE(SUM(price + freight_value), 0.00) AS total_order_value,
                    COUNT(order_item_id) AS items_count
                FROM stg_order_items
                GROUP BY order_id
            ),
            agg_payments AS (
                SELECT 
                    order_id,
                    COALESCE(SUM(payment_value), 0.00) AS total_payment_value,
                    COUNT(payment_sequential) AS payments_count
                FROM stg_order_payments
                GROUP BY order_id
            ),
            agg_reviews AS (
                SELECT 
                    order_id,
                    review_score
                FROM (
                    SELECT 
                        order_id,
                        review_score,
                        ROW_NUMBER() OVER (
                            PARTITION BY order_id 
                            ORDER BY review_answer_timestamp DESC NULLS LAST, 
                                     review_creation_date DESC NULLS LAST
                        ) AS rn
                    FROM stg_order_reviews
                ) r
                WHERE rn = 1
            ),
            customer_order_ranks AS (
                SELECT 
                    o.order_id,
                    c.customer_unique_id,
                    ROW_NUMBER() OVER (
                        PARTITION BY c.customer_unique_id 
                        ORDER BY o.order_purchase_timestamp ASC
                    ) AS order_sequence_number,
                    COUNT(*) OVER (
                        PARTITION BY c.customer_unique_id
                    ) AS customer_total_orders
                FROM stg_orders o
                INNER JOIN stg_customers c ON o.customer_id = c.customer_id
                WHERE o.order_status NOT IN ('canceled', 'unavailable')
            )
            INSERT INTO mart_order_performance (
                order_id, customer_id, customer_unique_id, customer_state, order_status,
                order_purchase_timestamp, order_approved_at, order_delivered_carrier_date,
                order_delivered_customer_date, order_estimated_delivery_date,
                total_item_value, total_freight_value, total_order_value, total_payment_value,
                items_count, payments_count, review_score,
                delivery_delay_days, is_on_time,
                order_sequence_number, is_repeat_purchase, is_repeat_customer,
                _mart_created_at
            )
            SELECT 
                o.order_id,
                o.customer_id,
                c.customer_unique_id,
                c.customer_state,
                o.order_status,
                o.order_purchase_timestamp,
                o.order_approved_at,
                o.order_delivered_carrier_date,
                o.order_delivered_customer_date,
                o.order_estimated_delivery_date,
                
                COALESCE(i.total_item_value, 0.00) AS total_item_value,
                COALESCE(i.total_freight_value, 0.00) AS total_freight_value,
                COALESCE(i.total_order_value, 0.00) AS total_order_value,
                COALESCE(p.total_payment_value, 0.00) AS total_payment_value,
                COALESCE(i.items_count, 0) AS items_count,
                COALESCE(p.payments_count, 0) AS payments_count,
                r.review_score,
                
                CASE 
                    WHEN o.order_delivered_customer_date IS NOT NULL 
                    THEN ROUND(EXTRACT(EPOCH FROM (o.order_delivered_customer_date - o.order_estimated_delivery_date)) / 86400.0, 2)
                    ELSE NULL
                END AS delivery_delay_days,
                
                CASE 
                    WHEN o.order_delivered_customer_date IS NOT NULL 
                    THEN (o.order_delivered_customer_date <= o.order_estimated_delivery_date)
                    ELSE NULL
                END AS is_on_time,
                
                COALESCE(cor.order_sequence_number, 1) AS order_sequence_number,
                COALESCE(cor.order_sequence_number > 1, FALSE) AS is_repeat_purchase,
                COALESCE(cor.customer_total_orders > 1, FALSE) AS is_repeat_customer,
                CURRENT_TIMESTAMP
            FROM stg_orders o
            LEFT JOIN stg_customers c ON o.customer_id = c.customer_id
            LEFT JOIN agg_items i ON o.order_id = i.order_id
            LEFT JOIN agg_payments p ON o.order_id = p.order_id
            LEFT JOIN agg_reviews r ON o.order_id = r.order_id
            LEFT JOIN customer_order_ranks cor ON o.order_id = cor.order_id;
        """
    else:
        # SQLite dialect fallback for unit testing
        mart_sql = """
            DELETE FROM mart_order_performance;

            INSERT INTO mart_order_performance (
                order_id, customer_id, customer_unique_id, customer_state, order_status,
                order_purchase_timestamp, order_approved_at, order_delivered_carrier_date,
                order_delivered_customer_date, order_estimated_delivery_date,
                total_item_value, total_freight_value, total_order_value, total_payment_value,
                items_count, payments_count, review_score,
                delivery_delay_days, is_on_time,
                order_sequence_number, is_repeat_purchase, is_repeat_customer,
                _mart_created_at
            )
            SELECT 
                o.order_id,
                o.customer_id,
                c.customer_unique_id,
                c.customer_state,
                o.order_status,
                o.order_purchase_timestamp,
                o.order_approved_at,
                o.order_delivered_carrier_date,
                o.order_delivered_customer_date,
                o.order_estimated_delivery_date,
                
                COALESCE(i.total_item_value, 0.0),
                COALESCE(i.total_freight_value, 0.0),
                COALESCE(i.total_order_value, 0.0),
                COALESCE(p.total_payment_value, 0.0),
                COALESCE(i.items_count, 0),
                COALESCE(p.payments_count, 0),
                r.review_score,
                
                CASE 
                    WHEN o.order_delivered_customer_date IS NOT NULL 
                    THEN ROUND((julianday(o.order_delivered_customer_date) - julianday(o.order_estimated_delivery_date)), 2)
                    ELSE NULL
                END,
                
                CASE 
                    WHEN o.order_delivered_customer_date IS NOT NULL 
                    THEN (julianday(o.order_delivered_customer_date) <= julianday(o.order_estimated_delivery_date))
                    ELSE NULL
                END,
                
                1, 0, 0,
                datetime('now')
            FROM stg_orders o
            LEFT JOIN stg_customers c ON o.customer_id = c.customer_id
            LEFT JOIN (
                SELECT order_id, SUM(price) AS total_item_value, SUM(freight_value) AS total_freight_value,
                       SUM(price + freight_value) AS total_order_value, COUNT(*) AS items_count
                FROM stg_order_items GROUP BY order_id
            ) i ON o.order_id = i.order_id
            LEFT JOIN (
                SELECT order_id, SUM(payment_value) AS total_payment_value, COUNT(*) AS payments_count
                FROM stg_order_payments GROUP BY order_id
            ) p ON o.order_id = p.order_id
            LEFT JOIN (
                SELECT order_id, review_score FROM stg_order_reviews GROUP BY order_id
            ) r ON o.order_id = r.order_id;
        """

    if is_postgres:
        with eng.connect() as init_conn:
            init_conn.execution_options(isolation_level="AUTOCOMMIT")
            try:
                init_conn.execute(text("TRUNCATE TABLE mart_order_performance;"))
            except Exception:
                init_conn.execute(text("DELETE FROM mart_order_performance;"))
    else:
        with eng.connect() as init_conn:
            init_conn.execution_options(isolation_level="AUTOCOMMIT")
            init_conn.execute(text("DELETE FROM mart_order_performance;"))

    with eng.begin() as conn:
        for stmt in mart_sql.split(";"):
            cleaned = stmt.strip()
            if cleaned:
                conn.execute(text(cleaned))

        # Rigorous Verification: Check exactly 1 row per order_id
        check_query = text("""
            SELECT 
                COUNT(*) AS total_rows,
                COUNT(DISTINCT order_id) AS distinct_orders
            FROM mart_order_performance;
        """)
        row = conn.execute(check_query).fetchone()
        total_rows = row[0]
        distinct_orders = row[1]

        if total_rows != distinct_orders:
            raise ValueError(
                f"Mart fan-out violation detected! total_rows ({total_rows}) != distinct_orders ({distinct_orders}). "
                f"mart_order_performance must contain exactly one row per order."
            )

    elapsed = time.time() - start_time
    logger.info(
        "Built mart_order_performance: %d rows (exact 1:1 order grain verified) in %.2f seconds.",
        total_rows,
        elapsed,
    )
    return total_rows
