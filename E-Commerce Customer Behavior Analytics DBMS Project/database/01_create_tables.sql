-- ============================================================
-- AI-Powered E-Commerce Customer Behavior Analytics
-- Database DDL Script — PostgreSQL 15+
-- ============================================================

-- Drop existing tables (in reverse dependency order)
DROP TABLE IF EXISTS campaign_interaction CASCADE;
DROP TABLE IF EXISTS campaign CASCADE;
DROP TABLE IF EXISTS return_table CASCADE;
DROP TABLE IF EXISTS payment CASCADE;
DROP TABLE IF EXISTS review CASCADE;
DROP TABLE IF EXISTS order_item CASCADE;
DROP TABLE IF EXISTS order_table CASCADE;
DROP TABLE IF EXISTS cart_item CASCADE;
DROP TABLE IF EXISTS cart CASCADE;
DROP TABLE IF EXISTS event CASCADE;
DROP TABLE IF EXISTS session CASCADE;
DROP TABLE IF EXISTS product CASCADE;
DROP TABLE IF EXISTS category CASCADE;
DROP TABLE IF EXISTS customer CASCADE;

-- ============================================================
-- 1. CUSTOMER
-- ============================================================
CREATE TABLE customer (
    customer_id     SERIAL PRIMARY KEY,
    customer_code   VARCHAR(20) UNIQUE NOT NULL,
    registration_date DATE NOT NULL DEFAULT CURRENT_DATE,
    age_group       VARCHAR(10) CHECK (age_group IN ('18-24','25-34','35-44','45-54','55+')),
    gender          VARCHAR(10) CHECK (gender IN ('M','F','Other','Unknown')),
    city            VARCHAR(100),
    state           VARCHAR(100),
    country         VARCHAR(50) DEFAULT 'India',
    preferred_channel VARCHAR(20) CHECK (preferred_channel IN ('web','mobile_app','mobile_web')),
    segment         VARCHAR(20) DEFAULT 'New',
    lifetime_value  DECIMAL(12,2) DEFAULT 0,
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE customer IS 'Customer profile and computed segment information';

-- ============================================================
-- 2. CATEGORY
-- ============================================================
CREATE TABLE category (
    category_id         SERIAL PRIMARY KEY,
    category_name       VARCHAR(100) UNIQUE NOT NULL,
    parent_category_id  INT REFERENCES category(category_id) ON DELETE SET NULL
);

COMMENT ON TABLE category IS 'Product categorization with optional hierarchy';

-- ============================================================
-- 3. PRODUCT
-- ============================================================
CREATE TABLE product (
    product_id      SERIAL PRIMARY KEY,
    product_code    VARCHAR(30) UNIQUE NOT NULL,
    product_name    VARCHAR(200) NOT NULL,
    category_id     INT REFERENCES category(category_id) ON DELETE SET NULL,
    brand           VARCHAR(100),
    price           DECIMAL(10,2) NOT NULL CHECK (price > 0),
    original_price  DECIMAL(10,2),
    avg_rating      DECIMAL(3,2) DEFAULT 0 CHECK (avg_rating >= 0 AND avg_rating <= 5),
    total_reviews   INT DEFAULT 0,
    stock_quantity  INT DEFAULT 0 CHECK (stock_quantity >= 0),
    is_active       BOOLEAN DEFAULT TRUE,
    created_at      TIMESTAMP DEFAULT NOW()
);

COMMENT ON TABLE product IS 'Product catalog with derived rating metrics';

-- ============================================================
-- 4. SESSION
-- ============================================================
CREATE TABLE session (
    session_id          SERIAL PRIMARY KEY,
    customer_id         INT NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    session_start       TIMESTAMP NOT NULL,
    session_end         TIMESTAMP,
    device              VARCHAR(20) CHECK (device IN ('desktop','mobile','tablet')),
    channel             VARCHAR(20) CHECK (channel IN ('web','mobile_app','mobile_web')),
    browser             VARCHAR(50),
    landing_page        VARCHAR(200),
    utm_source          VARCHAR(100),
    utm_campaign        VARCHAR(100),
    total_events        INT DEFAULT 0,
    session_duration_sec INT
);

COMMENT ON TABLE session IS 'Shopping session with device/channel context';

-- ============================================================
-- 5. EVENT (core behavioral data)
-- ============================================================
CREATE TABLE event (
    event_id        BIGSERIAL PRIMARY KEY,
    session_id      INT NOT NULL REFERENCES session(session_id) ON DELETE CASCADE,
    customer_id     INT NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    product_id      INT REFERENCES product(product_id) ON DELETE SET NULL,
    event_type      VARCHAR(30) NOT NULL CHECK (event_type IN (
                        'search','product_view','compare','add_to_cart',
                        'remove_from_cart','wishlist','checkout_start',
                        'checkout_complete','purchase','review','return_request'
                    )),
    event_timestamp TIMESTAMP NOT NULL DEFAULT NOW(),
    event_data      JSONB,
    page_url        VARCHAR(300)
);

COMMENT ON TABLE event IS 'Unified behavioral event log — the most queried table';
COMMENT ON COLUMN event.customer_id IS 'Denormalized from session for query performance (documented 3NF deviation)';

-- ============================================================
-- 6. CART
-- ============================================================
CREATE TABLE cart (
    cart_id         SERIAL PRIMARY KEY,
    customer_id     INT NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    session_id      INT REFERENCES session(session_id) ON DELETE SET NULL,
    cart_status     VARCHAR(20) DEFAULT 'active' CHECK (cart_status IN ('active','abandoned','converted')),
    created_at      TIMESTAMP DEFAULT NOW(),
    updated_at      TIMESTAMP DEFAULT NOW(),
    total_value     DECIMAL(12,2) DEFAULT 0
);

COMMENT ON TABLE cart IS 'Cart lifecycle — cart_status is key for abandonment analysis';

-- ============================================================
-- 7. CART_ITEM
-- ============================================================
CREATE TABLE cart_item (
    cart_item_id    SERIAL PRIMARY KEY,
    cart_id         INT NOT NULL REFERENCES cart(cart_id) ON DELETE CASCADE,
    product_id      INT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    quantity        INT NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(10,2) NOT NULL,
    added_at        TIMESTAMP DEFAULT NOW(),
    removed_at      TIMESTAMP
);

COMMENT ON TABLE cart_item IS 'Individual cart items with add/remove timestamps for behavioral analysis';

-- ============================================================
-- 8. ORDER_TABLE
-- ============================================================
CREATE TABLE order_table (
    order_id            SERIAL PRIMARY KEY,
    customer_id         INT NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    cart_id             INT REFERENCES cart(cart_id) ON DELETE SET NULL,
    order_date          TIMESTAMP NOT NULL DEFAULT NOW(),
    order_status        VARCHAR(20) DEFAULT 'pending' CHECK (order_status IN (
                            'pending','confirmed','shipped','delivered','cancelled','returned'
                        )),
    total_amount        DECIMAL(12,2) NOT NULL CHECK (total_amount > 0),
    discount_amount     DECIMAL(10,2) DEFAULT 0,
    payment_method      VARCHAR(30),
    shipping_address_city VARCHAR(100),
    delivery_date       TIMESTAMP
);

COMMENT ON TABLE order_table IS 'Completed transactions linked to carts for funnel analysis';

-- ============================================================
-- 9. ORDER_ITEM
-- ============================================================
CREATE TABLE order_item (
    order_item_id   SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES order_table(order_id) ON DELETE CASCADE,
    product_id      INT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    quantity        INT NOT NULL CHECK (quantity > 0),
    unit_price      DECIMAL(10,2) NOT NULL,
    subtotal        DECIMAL(12,2) NOT NULL
);

COMMENT ON TABLE order_item IS 'Order line items for product-level revenue analysis';

-- ============================================================
-- 10. REVIEW
-- ============================================================
CREATE TABLE review (
    review_id       SERIAL PRIMARY KEY,
    customer_id     INT NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    product_id      INT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    order_id        INT REFERENCES order_table(order_id) ON DELETE SET NULL,
    rating          INT NOT NULL CHECK (rating >= 1 AND rating <= 5),
    review_text     TEXT,
    sentiment_score DECIMAL(3,2),
    review_date     TIMESTAMP DEFAULT NOW(),
    is_verified     BOOLEAN DEFAULT FALSE
);

COMMENT ON TABLE review IS 'Customer feedback with computed sentiment score';

-- ============================================================
-- 11. PAYMENT
-- ============================================================
CREATE TABLE payment (
    payment_id      SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES order_table(order_id) ON DELETE CASCADE,
    payment_method  VARCHAR(30) NOT NULL,
    payment_status  VARCHAR(20) DEFAULT 'pending' CHECK (payment_status IN (
                        'pending','completed','failed','refunded'
                    )),
    amount          DECIMAL(12,2) NOT NULL,
    payment_date    TIMESTAMP,
    transaction_ref VARCHAR(100)
);

COMMENT ON TABLE payment IS 'Payment tracking for payment-method analysis';

-- ============================================================
-- 12. RETURN_TABLE
-- ============================================================
CREATE TABLE return_table (
    return_id       SERIAL PRIMARY KEY,
    order_id        INT NOT NULL REFERENCES order_table(order_id) ON DELETE CASCADE,
    product_id      INT NOT NULL REFERENCES product(product_id) ON DELETE CASCADE,
    customer_id     INT NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    return_reason   VARCHAR(100),
    return_date     TIMESTAMP DEFAULT NOW(),
    refund_amount   DECIMAL(10,2),
    return_status   VARCHAR(20) DEFAULT 'requested' CHECK (return_status IN (
                        'requested','approved','completed','rejected'
                    ))
);

COMMENT ON TABLE return_table IS 'Post-purchase returns for product issue detection';

-- ============================================================
-- 13. CAMPAIGN
-- ============================================================
CREATE TABLE campaign (
    campaign_id     SERIAL PRIMARY KEY,
    campaign_name   VARCHAR(200) NOT NULL,
    campaign_type   VARCHAR(30) CHECK (campaign_type IN ('email','sms','push','social','display')),
    start_date      DATE NOT NULL,
    end_date        DATE,
    budget          DECIMAL(10,2),
    target_segment  VARCHAR(50),
    status          VARCHAR(20) DEFAULT 'draft' CHECK (status IN ('draft','active','completed','paused'))
);

COMMENT ON TABLE campaign IS 'Marketing campaign definitions';

-- ============================================================
-- 14. CAMPAIGN_INTERACTION
-- ============================================================
CREATE TABLE campaign_interaction (
    interaction_id      SERIAL PRIMARY KEY,
    campaign_id         INT NOT NULL REFERENCES campaign(campaign_id) ON DELETE CASCADE,
    customer_id         INT NOT NULL REFERENCES customer(customer_id) ON DELETE CASCADE,
    interaction_type    VARCHAR(20) NOT NULL CHECK (interaction_type IN (
                            'sent','opened','clicked','converted','unsubscribed'
                        )),
    interaction_date    TIMESTAMP DEFAULT NOW(),
    channel             VARCHAR(20)
);

COMMENT ON TABLE campaign_interaction IS 'Customer-campaign interaction tracking for ROI analysis';

-- ============================================================
-- INDEXES
-- ============================================================

-- EVENT table (largest table, most queried)
CREATE INDEX idx_event_customer ON event(customer_id);
CREATE INDEX idx_event_session ON event(session_id);
CREATE INDEX idx_event_type ON event(event_type);
CREATE INDEX idx_event_timestamp ON event(event_timestamp);
CREATE INDEX idx_event_product ON event(product_id);
CREATE INDEX idx_event_customer_type ON event(customer_id, event_type);
CREATE INDEX idx_event_type_timestamp ON event(event_type, event_timestamp);

-- SESSION table
CREATE INDEX idx_session_customer ON session(customer_id);
CREATE INDEX idx_session_device ON session(device);
CREATE INDEX idx_session_start ON session(session_start);

-- ORDER_TABLE
CREATE INDEX idx_order_customer ON order_table(customer_id);
CREATE INDEX idx_order_date ON order_table(order_date);
CREATE INDEX idx_order_status ON order_table(order_status);

-- CART
CREATE INDEX idx_cart_customer ON cart(customer_id);
CREATE INDEX idx_cart_status ON cart(cart_status);

-- REVIEW
CREATE INDEX idx_review_product ON review(product_id);
CREATE INDEX idx_review_rating ON review(rating);

-- CAMPAIGN_INTERACTION
CREATE INDEX idx_ci_campaign ON campaign_interaction(campaign_id);
CREATE INDEX idx_ci_customer ON campaign_interaction(customer_id);

-- RETURN
CREATE INDEX idx_return_product ON return_table(product_id);
CREATE INDEX idx_return_customer ON return_table(customer_id);

-- ORDER_ITEM
CREATE INDEX idx_oi_order ON order_item(order_id);
CREATE INDEX idx_oi_product ON order_item(product_id);

SELECT 'All tables, constraints, and indexes created successfully.' AS status;
