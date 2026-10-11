-- ==============================================================================
-- OLIST WEEKLY BUSINESS REVIEW — SCHEMA MIGRATION 01: RAW LAYER
-- ==============================================================================
-- Purpose:
--   Preserves raw source representations from Olist CSV files.
--   Provides auditability, metadata tracking, and idempotent ingestion targets.
-- ==============================================================================

-- Raw Customers
CREATE TABLE IF NOT EXISTS raw_customers (
    customer_id VARCHAR(64) PRIMARY KEY,
    customer_unique_id VARCHAR(64) NOT NULL,
    customer_zip_code_prefix VARCHAR(16),
    customer_city VARCHAR(128),
    customer_state VARCHAR(8),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw Geolocation
-- Note: Geolocation table with surrogate primary key
CREATE TABLE IF NOT EXISTS raw_geolocation (
    geolocation_id BIGSERIAL PRIMARY KEY,
    geolocation_zip_code_prefix VARCHAR(16),
    geolocation_lat NUMERIC(10, 7),
    geolocation_lng NUMERIC(10, 7),
    geolocation_city VARCHAR(128),
    geolocation_state VARCHAR(8),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_raw_geo_zip ON raw_geolocation(geolocation_zip_code_prefix);

-- Raw Orders
CREATE TABLE IF NOT EXISTS raw_orders (
    order_id VARCHAR(64) PRIMARY KEY,
    customer_id VARCHAR(64) NOT NULL,
    order_status VARCHAR(32),
    order_purchase_timestamp VARCHAR(64),
    order_approved_at VARCHAR(64),
    order_delivered_carrier_date VARCHAR(64),
    order_delivered_customer_date VARCHAR(64),
    order_estimated_delivery_date VARCHAR(64),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
CREATE INDEX IF NOT EXISTS idx_raw_orders_customer ON raw_orders(customer_id);

-- Raw Order Items
-- Composite natural key: (order_id, order_item_id)
CREATE TABLE IF NOT EXISTS raw_order_items (
    order_id VARCHAR(64) NOT NULL,
    order_item_id INTEGER NOT NULL,
    product_id VARCHAR(64) NOT NULL,
    seller_id VARCHAR(64) NOT NULL,
    shipping_limit_date VARCHAR(64),
    price NUMERIC(12, 2),
    freight_value NUMERIC(12, 2),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, order_item_id)
);
CREATE INDEX IF NOT EXISTS idx_raw_items_product ON raw_order_items(product_id);
CREATE INDEX IF NOT EXISTS idx_raw_items_seller ON raw_order_items(seller_id);

-- Raw Order Payments
-- Composite key: (order_id, payment_sequential)
CREATE TABLE IF NOT EXISTS raw_order_payments (
    order_id VARCHAR(64) NOT NULL,
    payment_sequential INTEGER NOT NULL,
    payment_type VARCHAR(32),
    payment_installments INTEGER,
    payment_value NUMERIC(12, 2),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (order_id, payment_sequential)
);

-- Raw Order Reviews
-- Note: A review_id can sometimes be duplicated across re-submitted reviews or multiple orders;
-- We track review record with composite key (review_id, order_id).
CREATE TABLE IF NOT EXISTS raw_order_reviews (
    review_id VARCHAR(64) NOT NULL,
    order_id VARCHAR(64) NOT NULL,
    review_score INTEGER,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date VARCHAR(64),
    review_answer_timestamp VARCHAR(64),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    PRIMARY KEY (review_id, order_id)
);
CREATE INDEX IF NOT EXISTS idx_raw_reviews_order ON raw_order_reviews(order_id);

-- Raw Products
CREATE TABLE IF NOT EXISTS raw_products (
    product_id VARCHAR(64) PRIMARY KEY,
    product_category_name VARCHAR(128),
    product_name_lenght INTEGER,
    product_description_lenght INTEGER,
    product_photos_qty INTEGER,
    product_weight_g NUMERIC(10, 2),
    product_length_cm NUMERIC(10, 2),
    product_height_cm NUMERIC(10, 2),
    product_width_cm NUMERIC(10, 2),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw Sellers
CREATE TABLE IF NOT EXISTS raw_sellers (
    seller_id VARCHAR(64) PRIMARY KEY,
    seller_zip_code_prefix VARCHAR(16),
    seller_city VARCHAR(128),
    seller_state VARCHAR(8),
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

-- Raw Product Category Name Translation
CREATE TABLE IF NOT EXISTS raw_product_category_translation (
    product_category_name VARCHAR(128) PRIMARY KEY,
    product_category_name_english VARCHAR(128) NOT NULL,
    _loaded_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
