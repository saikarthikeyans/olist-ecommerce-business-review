-- ==============================================================================
-- ANALYTICAL QUERY 05: DELIVERY DELAY VERSUS CUSTOMER REVIEW SCORE
-- ==============================================================================
-- Business Description:
--   Investigates the statistical association between delivery punctuality and
--   customer satisfaction ratings (CSAT / review_score).
--
-- Delay Metric Definition:
--   - delivery_delay_days = (actual_delivery_date - estimated_delivery_date) in days.
--   - Positive values (> 0) indicate late deliveries.
--   - Negative or zero values (<= 0) indicate on-time or early deliveries.
--   - Only delivered orders with both valid actual and estimated timestamps are included.
--
-- Statistical & Analytical Guardrail:
--   - Association does NOT prove causation. Delays may correlate with damaged packaging,
--     difficult geography, seller fulfillment latency, or poor customer communication.
-- ==============================================================================

WITH delivered_orders_with_reviews AS (
    SELECT 
        order_id,
        review_score,
        delivery_delay_days,
        is_on_time,
        CASE 
            WHEN delivery_delay_days <= -3.0 THEN '1_Significant Early (>3d ahead)'
            WHEN delivery_delay_days <= 0.0 THEN '2_On-Time (0-3d ahead)'
            WHEN delivery_delay_days <= 5.0 THEN '3_Moderate Delay (1-5d late)'
            ELSE '4_Severe Delay (>5d late)'
        END AS delivery_performance_cohort,
        CASE 
            WHEN is_on_time = TRUE THEN 'On-Time / Early'
            ELSE 'Late'
        END AS on_time_classification
    FROM mart_order_performance
    WHERE order_status = 'delivered'
      AND order_delivered_customer_date IS NOT NULL
      AND order_estimated_delivery_date IS NOT NULL
      AND review_score IS NOT NULL
),
total_dataset_delivered AS (
    SELECT COUNT(*) AS total_count FROM delivered_orders_with_reviews
),
cohort_summary AS (
    SELECT 
        'BY_DELIVERY_COHORT' AS analysis_dimension,
        delivery_performance_cohort AS segment_label,
        COUNT(*) AS sample_size,
        ROUND((COUNT(*) * 100.0) / (SELECT total_count FROM total_dataset_delivered), 2) AS pct_of_delivered_orders,
        ROUND(AVG(delivery_delay_days), 2) AS avg_delay_days,
        ROUND(AVG(review_score), 2) AS avg_review_score,
        COUNT(CASE WHEN review_score = 5 THEN 1 END) AS score_5_count,
        COUNT(CASE WHEN review_score = 1 THEN 1 END) AS score_1_count,
        ROUND((COUNT(CASE WHEN review_score = 1 THEN 1 END) * 100.0) / COUNT(*), 2) AS score_1_dissatisfaction_rate_pct
    FROM delivered_orders_with_reviews
    GROUP BY delivery_performance_cohort

    UNION ALL

    SELECT 
        'BY_REVIEW_SCORE' AS analysis_dimension,
        CONCAT('Score: ', review_score::TEXT, ' Stars') AS segment_label,
        COUNT(*) AS sample_size,
        ROUND((COUNT(*) * 100.0) / (SELECT total_count FROM total_dataset_delivered), 2) AS pct_of_delivered_orders,
        ROUND(AVG(delivery_delay_days), 2) AS avg_delay_days,
        ROUND(AVG(review_score), 2) AS avg_review_score,
        COUNT(CASE WHEN is_on_time = FALSE THEN 1 END) AS score_5_count, -- Reused column for late orders count
        COUNT(CASE WHEN is_on_time = TRUE THEN 1 END) AS score_1_count,  -- Reused column for on-time orders count
        ROUND((COUNT(CASE WHEN is_on_time = FALSE THEN 1 END) * 100.0) / COUNT(*), 2) AS score_1_dissatisfaction_rate_pct -- Late rate %
    FROM delivered_orders_with_reviews
    GROUP BY review_score
)
SELECT 
    analysis_dimension,
    segment_label,
    sample_size,
    pct_of_delivered_orders,
    avg_delay_days,
    avg_review_score,
    score_1_dissatisfaction_rate_pct,
    'Association does not prove causation; underlying logistics frictions and product issues co-exist.' AS methodological_note
FROM cohort_summary
ORDER BY analysis_dimension ASC, segment_label ASC;
