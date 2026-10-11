-- ==============================================================================
-- QUALITY CHECK 05: INVALID REVIEW SCORES OUTSIDE THE ALLOWED RANGE 1–5
-- ==============================================================================
-- Description:
--   Verifies domain validity on review_score in stg_order_reviews.
--   Customer ratings must strictly fall between 1 (lowest) and 5 (highest).
-- Category: CRITICAL
-- Threshold: 0 (Zero Tolerance)
-- ==============================================================================

WITH invalid_reviews AS (
    SELECT 
        review_id,
        order_id,
        review_score
    FROM stg_order_reviews
    WHERE review_score IS NULL 
       OR review_score < 1 
       OR review_score > 5
),
sample_failures AS (
    SELECT review_id 
    FROM invalid_reviews 
    LIMIT 5
)
SELECT 
    '05_invalid_review_scores' AS check_name,
    'CRITICAL' AS severity,
    0 AS threshold,
    (SELECT COUNT(*) FROM invalid_reviews) AS failed_count,
    CASE 
        WHEN (SELECT COUNT(*) FROM invalid_reviews) = 0 THEN 'PASS'
        ELSE 'FAIL'
    END AS status,
    COALESCE(
        (SELECT string_agg(review_id, ', ') FROM sample_failures),
        'none'
    ) AS sample_failing_identifiers,
    'Review scores must be integers strictly within the range [1, 5].' AS details;
