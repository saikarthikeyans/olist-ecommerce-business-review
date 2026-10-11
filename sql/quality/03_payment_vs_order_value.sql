-- ==============================================================================
-- QUALITY CHECK 03: PAYMENT TOTALS VERSUS ITEM PRICE PLUS FREIGHT
-- ==============================================================================
-- Description:
--   Compares total order payments against total item price plus freight.
--   Business Rule:
--     Payment reconciliation applies to delivered orders containing items.
--     Tolerance threshold: Absolute variance > 1.00 BRL is flagged.
--   Reasoning for Classification:
--     Marketplace promotional vouchers, partial cancellations, or gateway fees
--     frequently account for variances. This is classified as WARNING to monitor
--     financial leakage without halting ELT operations.
-- Category: WARNING
-- Threshold: 600 (Dataset warning boundary)
-- ==============================================================================

WITH item_totals AS (
    SELECT 
        order_id,
        SUM(price) AS items_sum,
        SUM(freight_value) AS freight_sum,
        SUM(price + freight_value) AS expected_total
    FROM stg_order_items
    GROUP BY order_id
),
payment_totals AS (
    SELECT 
        order_id,
        SUM(payment_value) AS actual_payment
    FROM stg_order_payments
    GROUP BY order_id
),
reconciled AS (
    SELECT 
        o.order_id,
        i.expected_total,
        p.actual_payment,
        ABS(COALESCE(p.actual_payment, 0) - COALESCE(i.expected_total, 0)) AS variance
    FROM stg_orders o
    INNER JOIN item_totals i ON o.order_id = i.order_id
    LEFT JOIN payment_totals p ON o.order_id = p.order_id
    WHERE o.order_status = 'delivered'
),
failing_rows AS (
    SELECT 
        order_id,
        expected_total,
        actual_payment,
        variance
    FROM reconciled
    WHERE variance > 1.00
),
sample_failures AS (
    SELECT order_id 
    FROM failing_rows 
    LIMIT 5
)
SELECT 
    '03_payment_vs_order_value' AS check_name,
    'WARNING' AS severity,
    600 AS threshold,
    (SELECT COUNT(*) FROM failing_rows) AS failed_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM failing_rows) <= 600 THEN 'PASS'
        ELSE 'FAIL'
    END AS status,
    COALESCE(
        (SELECT string_agg(order_id, ', ') FROM sample_failures),
        'none'
    ) AS sample_failing_identifiers,
    'Delivered orders with payment reconciliation discrepancy greater than 1.00 BRL.' AS details;
