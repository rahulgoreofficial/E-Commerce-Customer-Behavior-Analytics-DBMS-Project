-- ============================================================
-- Stored Procedures, Functions & Triggers
-- ============================================================

-- ============================================================
-- FUNCTION: Assign RFM Segment Label
-- ============================================================
CREATE OR REPLACE FUNCTION fn_assign_rfm_segment(r INT, f INT, m INT)
RETURNS VARCHAR(20) AS $$
BEGIN
    IF r >= 4 AND f >= 4 AND m >= 4 THEN RETURN 'VIP';
    ELSIF r >= 4 AND f >= 3 THEN RETURN 'Loyal';
    ELSIF r >= 3 AND f >= 1 AND m >= 3 THEN RETURN 'Potential';
    ELSIF r >= 4 AND f <= 1 THEN RETURN 'New';
    ELSIF r <= 2 AND f >= 3 THEN RETURN 'At Risk';
    ELSIF r <= 2 AND f <= 2 THEN RETURN 'Churned';
    ELSE RETURN 'Regular';
    END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- PROCEDURE: Refresh All Materialized Views
-- ============================================================
CREATE OR REPLACE PROCEDURE sp_refresh_analytics()
LANGUAGE plpgsql AS $$
BEGIN
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_daily_sales;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_rfm;
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_product_performance;
    REFRESH MATERIALIZED VIEW mv_segment_kpis;
    RAISE NOTICE 'All materialized views refreshed at %', NOW();
END;
$$;

-- ============================================================
-- PROCEDURE: Update Customer Segments from RFM
-- ============================================================
CREATE OR REPLACE PROCEDURE sp_update_customer_segments()
LANGUAGE plpgsql AS $$
DECLARE
    updated_count INT;
BEGIN
    -- First refresh RFM view
    REFRESH MATERIALIZED VIEW CONCURRENTLY mv_customer_rfm;
    
    -- Update segments
    UPDATE customer c
    SET segment = fn_assign_rfm_segment(rfm.r_score, rfm.f_score, rfm.m_score),
        lifetime_value = rfm.monetary,
        updated_at = NOW()
    FROM mv_customer_rfm rfm
    WHERE c.customer_id = rfm.customer_id
      AND (c.segment IS DISTINCT FROM fn_assign_rfm_segment(rfm.r_score, rfm.f_score, rfm.m_score)
           OR c.lifetime_value IS DISTINCT FROM rfm.monetary);
    
    GET DIAGNOSTICS updated_count = ROW_COUNT;
    RAISE NOTICE 'Customer segments updated: % rows changed', updated_count;
END;
$$;

-- ============================================================
-- FUNCTION: Get Customer Behavior Summary
-- ============================================================
CREATE OR REPLACE FUNCTION fn_customer_behavior_summary(p_customer_id INT)
RETURNS TABLE(
    total_sessions BIGINT,
    total_events BIGINT,
    total_orders BIGINT,
    total_spent DECIMAL,
    avg_order_value DECIMAL,
    total_carts BIGINT,
    abandoned_carts BIGINT,
    total_reviews BIGINT,
    avg_rating DECIMAL,
    total_returns BIGINT,
    days_since_last_order INT,
    favorite_category VARCHAR
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        (SELECT COUNT(*) FROM session WHERE customer_id = p_customer_id),
        (SELECT COUNT(*) FROM event WHERE customer_id = p_customer_id),
        (SELECT COUNT(*) FROM order_table WHERE customer_id = p_customer_id AND order_status NOT IN ('cancelled')),
        COALESCE((SELECT SUM(ot.total_amount) FROM order_table ot WHERE ot.customer_id = p_customer_id AND ot.order_status NOT IN ('cancelled')), 0)::DECIMAL,
        COALESCE((SELECT AVG(ot.total_amount) FROM order_table ot WHERE ot.customer_id = p_customer_id AND ot.order_status NOT IN ('cancelled')), 0)::DECIMAL,
        (SELECT COUNT(*) FROM cart WHERE customer_id = p_customer_id),
        (SELECT COUNT(*) FROM cart WHERE customer_id = p_customer_id AND cart_status = 'abandoned'),
        (SELECT COUNT(*) FROM review WHERE customer_id = p_customer_id),
        COALESCE((SELECT AVG(rv.rating) FROM review rv WHERE rv.customer_id = p_customer_id), 0)::DECIMAL,
        (SELECT COUNT(*) FROM return_table WHERE customer_id = p_customer_id),
        COALESCE((SELECT (CURRENT_DATE - MAX(DATE(ot.order_date)))::INT FROM order_table ot WHERE ot.customer_id = p_customer_id), NULL)::INT,
        (SELECT cat.category_name FROM order_item oi 
         JOIN product p ON oi.product_id = p.product_id 
         JOIN category cat ON p.category_id = cat.category_id
         JOIN order_table o ON oi.order_id = o.order_id
         WHERE o.customer_id = p_customer_id
         GROUP BY cat.category_name ORDER BY COUNT(*) DESC LIMIT 1)::VARCHAR;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- FUNCTION: Get Conversion Funnel for Date Range
-- ============================================================
CREATE OR REPLACE FUNCTION fn_funnel_by_device(
    p_start_date TIMESTAMP,
    p_end_date TIMESTAMP
)
RETURNS TABLE(
    device VARCHAR,
    view_sessions BIGINT,
    cart_sessions BIGINT,
    checkout_sessions BIGINT,
    purchase_sessions BIGINT,
    overall_conversion_pct NUMERIC
) AS $$
BEGIN
    RETURN QUERY
    SELECT 
        s.device::VARCHAR,
        COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END),
        COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END),
        COUNT(DISTINCT CASE WHEN e.event_type = 'checkout_start' THEN e.session_id END),
        COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END),
        CASE WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) > 0
             THEN ROUND(COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END)::NUMERIC 
                  / COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) * 100, 2)
             ELSE 0 END
    FROM event e
    JOIN session s ON e.session_id = s.session_id
    WHERE e.event_timestamp BETWEEN p_start_date AND p_end_date
    GROUP BY s.device;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- TRIGGER: Update Product Rating After New Review
-- ============================================================
CREATE OR REPLACE FUNCTION trg_update_product_rating()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE product
    SET avg_rating = sub.new_avg,
        total_reviews = sub.new_count
    FROM (
        SELECT AVG(rating)::DECIMAL(3,2) AS new_avg, COUNT(*) AS new_count
        FROM review WHERE product_id = NEW.product_id
    ) sub
    WHERE product.product_id = NEW.product_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_product_rating
AFTER INSERT OR UPDATE ON review
FOR EACH ROW EXECUTE FUNCTION trg_update_product_rating();

-- ============================================================
-- TRIGGER: Update Cart Total When Items Change
-- ============================================================
CREATE OR REPLACE FUNCTION trg_update_cart_total()
RETURNS TRIGGER AS $$
DECLARE
    target_cart_id INT;
BEGIN
    target_cart_id := COALESCE(NEW.cart_id, OLD.cart_id);
    
    UPDATE cart
    SET total_value = COALESCE((
        SELECT SUM(quantity * unit_price)
        FROM cart_item 
        WHERE cart_id = target_cart_id AND removed_at IS NULL
    ), 0),
    updated_at = NOW()
    WHERE cart_id = target_cart_id;
    
    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_cart_total
AFTER INSERT OR UPDATE OR DELETE ON cart_item
FOR EACH ROW EXECUTE FUNCTION trg_update_cart_total();

-- ============================================================
-- TRIGGER: Update Session Event Count
-- ============================================================
CREATE OR REPLACE FUNCTION trg_update_session_events()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE session
    SET total_events = (SELECT COUNT(*) FROM event WHERE session_id = NEW.session_id)
    WHERE session_id = NEW.session_id;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_session_events
AFTER INSERT ON event
FOR EACH ROW EXECUTE FUNCTION trg_update_session_events();

-- ============================================================
-- TRIGGER: Update Customer Lifetime Value After Order
-- ============================================================
CREATE OR REPLACE FUNCTION trg_update_customer_ltv()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.order_status IN ('confirmed', 'shipped', 'delivered') THEN
        UPDATE customer
        SET lifetime_value = COALESCE((
            SELECT SUM(total_amount) FROM order_table 
            WHERE customer_id = NEW.customer_id 
            AND order_status NOT IN ('cancelled', 'returned')
        ), 0),
        updated_at = NOW()
        WHERE customer_id = NEW.customer_id;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

CREATE TRIGGER trigger_update_customer_ltv
AFTER INSERT OR UPDATE ON order_table
FOR EACH ROW EXECUTE FUNCTION trg_update_customer_ltv();

SELECT 'All procedures, functions, and triggers created successfully.' AS status;
