-- ==============================================================================
-- ANALYTICAL QUERY 03: SEVEN-DAY ROLLING AVERAGE OF DAILY ORDERS
-- ==============================================================================
-- Business Description:
--   Tracks daily order volumes and computes a smoothed 7-day rolling average
--   to identify marketplace demand velocity while eliminating day-of-week seasonality.
--
-- Continuous Calendar Series:
--   - Uses PostgreSQL GENERATE_SERIES to construct every consecutive calendar day
--     between the dataset's earliest and latest purchase dates.
--   - LEFT JOIN ensures days with zero placed orders are preserved as 0 rather than skipped.
--
-- Window Specification & Cold-Start Handling:
--   - ROWS BETWEEN 6 PRECEDING AND CURRENT ROW over the continuous daily timeline.
--   - First 6 Days Treatment: Evaluated as an expanding partial-window average over all
--     available preceding days (from 1 to 6 days), noted by window_days_available.
-- ==============================================================================

WITH date_boundaries AS (
    SELECT 
        DATE_TRUNC('day', MIN(order_purchase_timestamp))::DATE AS min_date,
        DATE_TRUNC('day', MAX(order_purchase_timestamp))::DATE AS max_date
    FROM mart_order_performance
    WHERE order_status NOT IN ('canceled', 'unavailable')
),
calendar_spine AS (
    SELECT 
        GENERATE_SERIES(min_date, max_date, INTERVAL '1 day')::DATE AS calendar_date
    FROM date_boundaries
),
daily_order_counts AS (
    SELECT 
        DATE_TRUNC('day', order_purchase_timestamp)::DATE AS purchase_date,
        COUNT(DISTINCT order_id) AS orders_count,
        SUM(total_item_value) AS daily_item_revenue
    FROM mart_order_performance
    WHERE order_status NOT IN ('canceled', 'unavailable')
    GROUP BY 1
),
continuous_timeline AS (
    SELECT 
        c.calendar_date,
        COALESCE(d.orders_count, 0) AS daily_orders,
        COALESCE(d.daily_item_revenue, 0.00) AS daily_revenue
    FROM calendar_spine c
    LEFT JOIN daily_order_counts d ON c.calendar_date = d.purchase_date
)
SELECT 
    calendar_date,
    daily_orders,
    ROUND(daily_revenue, 2) AS daily_revenue,
    COUNT(daily_orders) OVER (
        ORDER BY calendar_date 
        ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
    ) AS window_days_available,
    ROUND(
        AVG(daily_orders) OVER (
            ORDER BY calendar_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS rolling_7d_avg_orders,
    ROUND(
        AVG(daily_revenue) OVER (
            ORDER BY calendar_date 
            ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
        ), 
        2
    ) AS rolling_7d_avg_revenue
FROM continuous_timeline
ORDER BY calendar_date ASC;
