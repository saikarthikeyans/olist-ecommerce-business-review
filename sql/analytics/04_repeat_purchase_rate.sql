-- ==============================================================================
-- ANALYTICAL QUERY 04: REPEAT-PURCHASE RATE & CUSTOMER RETENTION
-- ==============================================================================
-- Business Description:
--   Calculates customer retention and repeat-purchase loyalty for Olist.
--
-- Olist Architecture Note (Critical):
--   In the Olist data model:
--     - customer_id is a per-order surrogate key generated for each checkout session.
--     - customer_unique_id represents the actual unique person across multiple orders.
--   Evaluating retention using customer_id yields a false 0% repeat rate.
--   Therefore, customer_unique_id MUST be used.
--
-- Metric Definitions:
--   - Qualifying Orders: Non-canceled orders (order_status NOT IN ('canceled', 'unavailable')).
--   - Denominator: Count of distinct customer_unique_id with >= 1 qualifying order.
--   - Numerator: Count of distinct customer_unique_id with >= 2 qualifying orders.
--   - Repeat-Purchase Rate (%): (Repeat Customers / Total Customers) * 100.0
-- ==============================================================================

WITH customer_order_history AS (
    SELECT 
        customer_unique_id,
        COUNT(DISTINCT order_id) AS total_orders_placed,
        MIN(order_purchase_timestamp) AS first_order_date,
        MAX(order_purchase_timestamp) AS last_order_date,
        SUM(total_order_value) AS lifetime_gross_spend
    FROM mart_order_performance
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY customer_unique_id
),
retention_summary AS (
    SELECT 
        COUNT(*) AS total_distinct_customers,
        COUNT(CASE WHEN total_orders_placed = 1 THEN 1 END) AS one_time_customers,
        COUNT(CASE WHEN total_orders_placed >= 2 THEN 1 END) AS repeat_customers,
        COUNT(CASE WHEN total_orders_placed = 2 THEN 1 END) AS two_time_customers,
        COUNT(CASE WHEN total_orders_placed >= 3 THEN 1 END) AS three_plus_customers,
        SUM(total_orders_placed) AS total_qualifying_orders
    FROM customer_order_history
)
SELECT 
    total_distinct_customers,
    one_time_customers,
    repeat_customers,
    two_time_customers,
    three_plus_customers,
    total_qualifying_orders,
    ROUND((repeat_customers * 100.0) / NULLIF(total_distinct_customers, 0), 2) AS repeat_purchase_rate_pct,
    ROUND((total_qualifying_orders * 1.0) / NULLIF(total_distinct_customers, 0), 3) AS avg_orders_per_customer
FROM retention_summary;
