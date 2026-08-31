-- ============================================================
-- Database Security & Access Control
-- ============================================================

-- Create roles
DO $$
BEGIN
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ecom_admin') THEN
        CREATE ROLE ecom_admin WITH LOGIN PASSWORD 'admin_secure_2024';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ecom_analyst') THEN
        CREATE ROLE ecom_analyst WITH LOGIN PASSWORD 'analyst_2024';
    END IF;
    IF NOT EXISTS (SELECT 1 FROM pg_roles WHERE rolname = 'ecom_app') THEN
        CREATE ROLE ecom_app WITH LOGIN PASSWORD 'app_2024';
    END IF;
END $$;

-- Admin: full access
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ecom_admin;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ecom_admin;
GRANT EXECUTE ON ALL FUNCTIONS IN SCHEMA public TO ecom_admin;

-- Analyst: read-only
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ecom_analyst;
GRANT SELECT ON mv_daily_sales, mv_customer_rfm, mv_product_performance, mv_segment_kpis TO ecom_analyst;

-- App user: read + controlled write
GRANT SELECT ON ALL TABLES IN SCHEMA public TO ecom_app;
GRANT INSERT ON event, session, cart, cart_item, order_table, order_item, payment, review, return_table, campaign_interaction TO ecom_app;
GRANT UPDATE ON cart, cart_item, customer, order_table, product TO ecom_app;
GRANT USAGE ON ALL SEQUENCES IN SCHEMA public TO ecom_app;

SELECT 'Security roles and permissions configured.' AS status;
