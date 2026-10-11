-- ==============================================================================
-- OLIST WEEKLY BUSINESS REVIEW — SCHEMA MIGRATION 03: MART LAYER
-- ==============================================================================
-- Purpose:
--   Creates the analysis-ready `mart_order_performance` table with exactly
--   one row per order_id. Pre-aggregates items, payments, and reviews independently
--   to eliminate fan-out joins that duplicate financial figures.
-- ==============================================================================

-- Mart: Order Performance
CREATE TABLE IF NOT EXISTS mart_order_performance (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    customer_unique_id VARCHAR(64) NOT NULL,
    customer_state VARCHAR(8),
    order_status VARCHAR(32) NOT NULL,
    order_purchase_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    order_approved_at TIMESTAMP WITH TIME ZONE,
    order_delivered_carrier_date TIMESTAMP WITH TIME ZONE,
    order_delivered_customer_date TIMESTAMP WITH TIME ZONE,
    order_estimated_delivery_date TIMESTAMP WITH TIME ZONE NOT NULL,
    
    -- Financial aggregates (pre-aggregated from items & payments)
    total_item_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_freight_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    total_order_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,  -- item_value + freight_value
    total_payment_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    items_count INTEGER NOT NULL DEFAULT 0,
    payments_count INTEGER NOT NULL DEFAULT 0,
    
    -- Review aggregates
    review_score INTEGER,
    
    -- Delivery Performance & Timeliness
    delivery_delay_days NUMERIC(10, 2), -- Positive = late, Negative = early
    is_on_time BOOLEAN,                 -- TRUE if delivered on or before estimated date
    
    -- Customer Retention / Loyalty indicators
    order_sequence_number INTEGER NOT NULL DEFAULT 1,
    is_repeat_purchase BOOLEAN NOT NULL DEFAULT FALSE,
    is_repeat_customer BOOLEAN NOT NULL DEFAULT FALSE,
    
    _mart_created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_mart_purchase_ts ON mart_order_performance(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_mart_cust_unique ON mart_order_performance(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_mart_cust_state ON mart_order_performance(customer_state);
CREATE INDEX IF NOT EXISTS idx_mart_status ON mart_order_performance(order_status);
CREATE INDEX IF NOT EXISTS idx_mart_on_time ON mart_order_performance(is_on_time);
CREATE INDEX IF NOT EXISTS idx_mart_review ON mart_order_performance(review_score);

-- Audit Table: Data Quality Check Logs
CREATE TABLE IF NOT EXISTS pipeline_quality_audit (
    audit_id BIGSERIAL PRIMARY KEY,
    check_name VARCHAR(128) NOT NULL,
    check_category VARCHAR(64) NOT NULL, -- CRITICAL, WARNING, INFO
    execution_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    threshold_limit INTEGER NOT NULL,
    failed_count INTEGER NOT NULL,
    status VARCHAR(16) NOT NULL,        -- PASS, FAIL
    sample_failing_identifiers JSONB,
    details TEXT
);
CREATE INDEX IF NOT EXISTS idx_audit_exec_ts ON pipeline_quality_audit(execution_timestamp);
