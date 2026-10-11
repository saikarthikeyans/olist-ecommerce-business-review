-- ==============================================================================
-- ANALYTICAL QUERY 01: MONTH-OVER-MONTH REVENUE AND GROWTH
-- ==============================================================================
-- Business Description:
--   Aggregates merchandise and shipping revenue by calendar month to analyze
--   top-line business trajectory. Evaluates month-over-month (MoM) absolute
--   revenue expansion and percentage growth rates.
--
-- Revenue Definition:
--   - gross_item_revenue: Total price paid for goods (merchandise GMV), excluding freight.
--   - total_freight_revenue: Total shipping and delivery fees charged.
--   - total_gross_revenue: Comprehensive GMV (items + freight).
--   Orders included: Non-canceled qualifying orders (order_status NOT IN ('canceled', 'unavailable')).
--
-- Window Function Logic:
--   - LAG(gross_item_revenue, 1) retrieves prior calendar month's baseline.
--   - Safe division handles the inaugural month (NULL) and zero-baseline edge cases.
-- ==============================================================================

WITH monthly_orders AS (
    SELECT 
        DATE_TRUNC('month', order_purchase_timestamp)::DATE AS revenue_month,
        TO_CHAR(order_purchase_timestamp, 'YYYY-MM') AS year_month,
        COUNT(DISTINCT order_id) AS total_orders,
        SUM(total_item_value) AS gross_item_revenue,
        SUM(total_freight_value) AS total_freight_revenue,
        SUM(total_order_value) AS total_gross_revenue,
        SUM(total_payment_value) AS total_payment_captured
    FROM mart_order_performance
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1, 2
),
mom_calculations AS (
    SELECT 
        revenue_month,
        year_month,
        total_orders,
        gross_item_revenue,
        total_freight_revenue,
        total_gross_revenue,
        LAG(gross_item_revenue, 1) OVER (ORDER BY revenue_month) AS prev_month_item_revenue,
        LAG(total_gross_revenue, 1) OVER (ORDER BY revenue_month) AS prev_month_gross_revenue
    FROM monthly_orders
)
SELECT 
    year_month,
    total_orders,
    ROUND(gross_item_revenue, 2) AS gross_item_revenue,
    ROUND(total_freight_revenue, 2) AS total_freight_revenue,
    ROUND(total_gross_revenue, 2) AS total_gross_revenue,
    ROUND(prev_month_item_revenue, 2) AS prev_month_item_revenue,
    ROUND(gross_item_revenue - prev_month_item_revenue, 2) AS item_revenue_mom_change,
    CASE 
        WHEN prev_month_item_revenue IS NULL THEN NULL
        WHEN prev_month_item_revenue = 0 THEN NULL
        ELSE ROUND(((gross_item_revenue - prev_month_item_revenue) / prev_month_item_revenue) * 100.0, 2)
    END AS item_revenue_mom_growth_pct,
    CASE 
        WHEN prev_month_gross_revenue IS NULL THEN NULL
        WHEN prev_month_gross_revenue = 0 THEN NULL
        ELSE ROUND(((total_gross_revenue - prev_month_gross_revenue) / prev_month_gross_revenue) * 100.0, 2)
    END AS gross_revenue_mom_growth_pct
FROM mom_calculations
ORDER BY revenue_month ASC;
