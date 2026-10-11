-- ==============================================================================
-- QUALITY CHECK 06: DELIVERY DATE AND ESTIMATED DATE ANOMALIES
-- ==============================================================================
-- Description:
--   Custom delivery check identifying:
--     1. Orders marked 'delivered' that lack an actual customer delivery timestamp.
--     2. Orders where the estimated delivery date is earlier than the purchase date.
--   Reasoning:
--     Carrier sync dropouts can occasionally leave a delivered order without
--     a timestamp, or estimated dates may have system clock glitches.
-- Category: WARNING
-- Threshold: 50
-- ==============================================================================

WITH delivery_anomalies AS (
    SELECT 
        order_id,
        order_status,
        order_purchase_timestamp,
        order_delivered_customer_date,
        order_estimated_delivery_date
    FROM stg_orders
    WHERE 
        (order_status = 'delivered' AND order_delivered_customer_date IS NULL)
        OR 
        (order_estimated_delivery_date IS NOT NULL 
         AND order_purchase_timestamp IS NOT NULL 
         AND order_estimated_delivery_date < order_purchase_timestamp)
),
sample_failures AS (
    SELECT order_id 
    FROM delivery_anomalies 
    LIMIT 5
)
SELECT 
    '06_delivery_date_anomalies' AS check_name,
    'WARNING' AS severity,
    50 AS threshold,
    (SELECT COUNT(*) FROM delivery_anomalies) AS failed_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM delivery_anomalies) <= 50 THEN 'PASS'
        ELSE 'FAIL'
    END AS status,
    COALESCE(
        (SELECT string_agg(order_id, ', ') FROM sample_failures),
        'none'
    ) AS sample_failing_identifiers,
    'Delivered orders missing customer delivery timestamp or estimated delivery preceding purchase.' AS details;
