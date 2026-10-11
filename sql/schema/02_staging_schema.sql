-- ==============================================================================
-- OLIST WEEKLY BUSINESS REVIEW — SCHEMA MIGRATION 02: STAGING LAYER
-- ==============================================================================
-- Purpose:
--   Cleaned, typed, deduplicated, and normalized staging tables.
--   Enforces proper timestamp types, trims whitespace, standardizes column names,
--   and provides referential integrity foundations.
-- ==============================================================================

-- Staging Customers
CREATE TABLE IF NOT EXISTS stg_customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    customer_unique_id VARCHAR(64) NOT NULL,
    customer_zip_code_prefix VARCHAR(16),
    customer_city VARCHAR(128),
    customer_state VARCHAR(8),
    _staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_stg_customers_unique ON stg_customers(customer_unique_id);
CREATE INDEX IF NOT EXISTS idx_stg_customers_state ON stg_customers(customer_state);

-- Staging Orders
CREATE TABLE IF NOT EXISTS stg_orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    order_status VARCHAR(32) NOT NULL,
    order_purchase_timestamp TIMESTAMP WITH TIME ZONE NOT NULL,
    order_approved_at TIMESTAMP WITH TIME ZONE,
    order_delivered_carrier_date TIMESTAMP WITH TIME ZONE,
    order_delivered_customer_date TIMESTAMP WITH TIME ZONE,
    order_estimated_delivery_date TIMESTAMP WITH TIME ZONE NOT NULL,
    _staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_stg_orders_customer ON stg_orders(customer_id);
CREATE INDEX IF NOT EXISTS idx_stg_orders_purchase_date ON stg_orders(order_purchase_timestamp);
CREATE INDEX IF NOT EXISTS idx_stg_orders_status ON stg_orders(order_status);

-- Staging Order Items
CREATE TABLE IF NOT EXISTS stg_order_items (
    order_id VARCHAR(64) NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(64) NOT NULL,
    seller_id VARCHAR(64) NOT NULL,
    shipping_limit_date TIMESTAMP WITH TIME ZONE,
    price NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    freight_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    _staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, order_item_id)
);
CREATE INDEX IF NOT EXISTS idx_stg_items_product ON stg_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_stg_items_seller ON stg_order_items(seller_id);

-- Staging Order Payments
CREATE TABLE IF NOT EXISTS stg_order_payments (
    order_id VARCHAR(64) NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(32) NOT NULL,
    payment_installments INTEGER NOT NULL DEFAULT 1,
    payment_value NUMERIC(12, 2) NOT NULL DEFAULT 0.00,
    _staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, payment_sequential)
);
CREATE INDEX IF NOT EXISTS idx_stg_payments_order ON stg_order_payments(order_id);

-- Staging Order Reviews (Deduplicated per review_id, order_id)
CREATE TABLE IF NOT EXISTS stg_order_reviews (
    review_id VARCHAR(64) NOT NULL,
    order_id VARCHAR(64) NOT NULL,
    review_score INTEGER NOT NULL,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP WITH TIME ZONE,
    review_answer_timestamp TIMESTAMP WITH TIME ZONE,
    _staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);
CREATE INDEX IF NOT EXISTS idx_stg_reviews_order ON stg_order_reviews(order_id);
CREATE INDEX IF NOT EXISTS idx_stg_reviews_score ON stg_order_reviews(review_score);

-- Staging Products
CREATE TABLE IF NOT EXISTS stg_products (
    product_id VARCHAR(64) PRIMARY KEY,
    product_category_name VARCHAR(128),
    product_category_name_english VARCHAR(128),
    product_name_length INTEGER,
    product_description_length INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(10, 2),
    product_length_cm NUMERIC(10, 2),
    product_height_cm NUMERIC(10, 2),
    product_width_cm NUMERIC(10, 2),
    _staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_stg_products_cat_en ON stg_products(product_category_name_english);

-- Staging Sellers
CREATE TABLE IF NOT EXISTS stg_sellers (
    seller_id VARCHAR(64) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(16),
    seller_city VARCHAR(128),
    seller_state VARCHAR(8),
    _staged_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
