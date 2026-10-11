-- ==============================================================================
-- QUALITY CHECK 01: NULL OR DUPLICATE ORDER IDENTIFIERS
-- ==============================================================================
-- Description:
--   Verifies Primary Key integrity on stg_orders. Every order record must have
--   a non-null, uniquely identifiable order_id.
-- Category: CRITICAL
-- Threshold: 0 (Zero Tolerance - Fails pipeline if count > 0)
-- Action on Failure: STOP PIPELINE. Data integrity compromised.
-- ==============================================================================

WITH duplicate_orders AS (
    SELECT 
        order_id, 
        COUNT(*) AS occurrence_count
    FROM stg_orders
    WHERE order_id IS NOT NULL
    GROUP BY order_id
    HAVING COUNT(*) > 1
),
null_orders AS (
    SELECT COUNT(*) AS null_count
    FROM stg_orders
    WHERE order_id IS NULL OR TRIM(order_id) = ''
),
sample_failures AS (
    SELECT order_id 
    FROM duplicate_orders 
    LIMIT 5
)
SELECT 
    '01_null_duplicate_orders' AS check_name,
    'CRITICAL' AS severity,
    0 AS threshold,
    (
        COALESCE((SELECT SUM(occurrence_count) FROM duplicate_orders), 0) + 
        COALESCE((SELECT null_count FROM null_orders), 0)
    ) AS failed_count,
    CASE 
        WHEN (COALESCE((SELECT SUM(occurrence_count) FROM duplicate_orders), 0) + 
              COALESCE((SELECT null_count FROM null_orders), 0)) = 0 
        THEN 'PASS'
        ELSE 'FAIL'
    END AS status,
    COALESCE(
        (SELECT string_agg(order_id, ', ') FROM sample_failures),
        'none'
    ) AS sample_failing_identifiers,
    'Orders table must not have null or duplicate order_id primary keys.' AS details;
