-- ==============================================================================
-- ANALYTICAL QUERY 02: TOP THREE PRODUCT CATEGORIES BY CUSTOMER STATE
-- ==============================================================================
-- Business Description:
--   Identifies the top 3 highest-grossing product categories across each
--   Brazilian customer state to uncover regional demand preferences.
--
-- Joins & Logic:
--   - stg_order_items: provides individual item price and product association.
--   - stg_orders: filters out canceled/unavailable orders and links customer_id.
--   - stg_customers: provides customer_state (destination market).
--   - stg_products: provides translated product_category_name_english.
--
-- Ranking & Tie Handling:
--   - DENSE_RANK() partitioned by customer_state ordered by category_revenue DESC.
--   - Documented Tie Behavior: If two categories tie in revenue, both receive identical
--     rankings (e.g. joint rank 1) and the subsequent category receives rank 2 without gaps.
-- ==============================================================================

WITH category_state_revenue AS (
    SELECT 
        c.customer_state,
        COALESCE(p.product_category_name_english, p.product_category_name, 'unspecified') AS product_category,
        COUNT(DISTINCT o.order_id) AS distinct_orders,
        COUNT(i.order_item_id) AS total_items_sold,
        SUM(i.price) AS total_category_revenue
    FROM stg_order_items i
    INNER JOIN stg_orders o ON i.order_id = o.order_id
    INNER JOIN stg_customers c ON o.customer_id = c.customer_id
    LEFT JOIN stg_products p ON i.product_id = p.product_id
    WHERE o.order_status NOT IN ('canceled', 'unavailable')
      AND c.customer_state IS NOT NULL
    GROUP BY 
        c.customer_state, 
        COALESCE(p.product_category_name_english, p.product_category_name, 'unspecified')
),
ranked_categories AS (
    SELECT 
        customer_state,
        product_category,
        distinct_orders,
        total_items_sold,
        ROUND(total_category_revenue, 2) AS total_category_revenue,
        DENSE_RANK() OVER (
            PARTITION BY customer_state 
            ORDER BY total_category_revenue DESC
        ) AS category_rank
    FROM category_state_revenue
)
SELECT 
    customer_state,
    category_rank,
    product_category,
    distinct_orders,
    total_items_sold,
    total_category_revenue
FROM ranked_categories
WHERE category_rank <= 3
ORDER BY 
    customer_state ASC, 
    category_rank ASC, 
    total_category_revenue DESC;
