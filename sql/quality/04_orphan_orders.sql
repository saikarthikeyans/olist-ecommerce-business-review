-- ==============================================================================
-- QUALITY CHECK 04: ORDERS WITH NO MATCHING CUSTOMER RECORD
-- ==============================================================================
-- Description:
--   Verifies referential integrity between orders and customers. Every order
--   must link to a valid customer record.
-- Category: CRITICAL
-- Threshold: 0 (Zero Tolerance)
-- Action on Failure: STOP PIPELINE. Foreign key violation breaks customer tracking.
-- ==============================================================================

WITH orphan_orders AS (
    SELECT 
        o.order_id,
        o.customer_id
    FROM stg_orders o
    LEFT JOIN stg_customers c ON o.customer_id = c.customer_id
    WHERE c.customer_id IS NULL
),
sample_failures AS (
    SELECT order_id 
    FROM orphan_orders 
    LIMIT 5
)
SELECT 
    '04_orphan_orders' AS check_name,
    'CRITICAL' AS severity,
    0 AS threshold,
    (SELECT COUNT(*) FROM orphan_orders) AS failed_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM orphan_orders) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status,
    COALESCE(
        (SELECT string_agg(order_id, ', ') FROM sample_failures),
        'none'
    ) AS sample_failing_identifiers,
    'Orders referencing nonexistent customer records violate referential integrity.' AS details;
