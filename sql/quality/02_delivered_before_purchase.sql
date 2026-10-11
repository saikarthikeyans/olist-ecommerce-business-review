-- ==============================================================================
-- QUALITY CHECK 02: DELIVERED TIMESTAMPS EARLIER THAN PURCHASE TIMESTAMPS
-- ==============================================================================
-- Description:
--   Verifies chronological consistency. A delivery to a customer cannot logically
--   occur prior to the initial purchase timestamp.
-- Category: CRITICAL
-- Threshold: 0 (Zero Tolerance)
-- Action on Failure: STOP PIPELINE or Flag Records.
-- ==============================================================================

WITH invalid_chronology AS (
    SELECT 
        order_id,
        order_purchase_timestamp,
        order_delivered_customer_date
    FROM stg_orders
    WHERE order_delivered_customer_date IS NOT NULL
      AND order_purchase_timestamp IS NOT NULL
      AND order_delivered_customer_date < order_purchase_timestamp
),
sample_failures AS (
    SELECT order_id 
    FROM invalid_chronology 
    LIMIT 5
)
SELECT 
    '02_delivered_before_purchase' AS check_name,
    'CRITICAL' AS severity,
    0 AS threshold,
    (SELECT COUNT(*) FROM invalid_chronology) AS failed_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM invalid_chronology) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status,
    COALESCE(
        (SELECT string_agg(order_id, ', ') FROM sample_failures),
        'none'
    ) AS sample_failing_identifiers,
    'Orders cannot have delivery timestamp earlier than purchase timestamp.' AS details;
