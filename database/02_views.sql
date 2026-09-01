-- ============================================================
-- Views & Materialized Views
-- ============================================================

-- ============================================================
-- MV 1: Daily Sales Summary
-- ============================================================
CREATE MATERIALIZED VIEW mv_daily_sales AS
SELECT 
    DATE(order_date) AS sale_date,
    COUNT(DISTINCT order_id) AS total_orders,
    COUNT(DISTINCT customer_id) AS unique_customers,
    SUM(total_amount) AS total_revenue,
    AVG(total_amount) AS avg_order_value
FROM order_table
WHERE order_status NOT IN ('cancelled', 'returned')
GROUP BY DATE(order_date)
ORDER BY sale_date;

CREATE UNIQUE INDEX idx_mv_daily_sales_date ON mv_daily_sales(sale_date);

-- ============================================================
-- MV 2: Customer RFM Scores
-- ============================================================
CREATE MATERIALIZED VIEW mv_customer_rfm AS
SELECT 
    c.customer_id,
    c.customer_code,
    c.segment,
    COALESCE(CURRENT_DATE - MAX(DATE(o.order_date)), 9999) AS recency_days,
    COUNT(DISTINCT o.order_id) AS frequency,
    COALESCE(SUM(o.total_amount), 0) AS monetary,
    NTILE(5) OVER (ORDER BY COALESCE(CURRENT_DATE - MAX(DATE(o.order_date)), 9999) DESC) AS r_score,
    NTILE(5) OVER (ORDER BY COUNT(DISTINCT o.order_id)) AS f_score,
    NTILE(5) OVER (ORDER BY COALESCE(SUM(o.total_amount), 0)) AS m_score
FROM customer c
LEFT JOIN order_table o ON c.customer_id = o.customer_id
    AND o.order_status NOT IN ('cancelled', 'returned')
GROUP BY c.customer_id, c.customer_code, c.segment;

CREATE UNIQUE INDEX idx_mv_rfm_customer ON mv_customer_rfm(customer_id);

-- ============================================================
-- MV 3: Product Performance
-- ============================================================
CREATE MATERIALIZED VIEW mv_product_performance AS
SELECT 
    p.product_id,
    p.product_code,
    p.product_name,
    p.price,
    COALESCE(cat.category_name, 'Uncategorized') AS category_name,
    COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.event_id END) AS total_views,
    COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.event_id END) AS total_cart_adds,
    COUNT(DISTINCT oi.order_item_id) AS total_purchases,
    CASE WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.event_id END) > 0 
         THEN ROUND(COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.event_id END)::NUMERIC 
              / COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.event_id END) * 100, 2)
         ELSE 0 END AS view_to_cart_rate,
    CASE WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.event_id END) > 0 
         THEN ROUND(COUNT(DISTINCT oi.order_item_id)::NUMERIC 
              / COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.event_id END) * 100, 2)
         ELSE 0 END AS cart_to_purchase_rate,
    COALESCE(p.avg_rating, 0) AS avg_rating,
    p.total_reviews,
    COUNT(DISTINCT ret.return_id) AS total_returns
FROM product p
LEFT JOIN category cat ON p.category_id = cat.category_id
LEFT JOIN event e ON p.product_id = e.product_id
LEFT JOIN order_item oi ON p.product_id = oi.product_id
LEFT JOIN return_table ret ON p.product_id = ret.product_id
GROUP BY p.product_id, p.product_code, p.product_name, p.price, cat.category_name, p.avg_rating, p.total_reviews;

CREATE UNIQUE INDEX idx_mv_product_perf ON mv_product_performance(product_id);

-- ============================================================
-- MV 4: Segment KPIs
-- ============================================================
CREATE MATERIALIZED VIEW mv_segment_kpis AS
SELECT 
    COALESCE(c.segment, 'Unknown') AS segment,
    COUNT(DISTINCT c.customer_id) AS customer_count,
    ROUND(AVG(c.lifetime_value)::NUMERIC, 2) AS avg_ltv,
    ROUND(AVG(COALESCE(CURRENT_DATE - MAX_order.last_order, 9999))::NUMERIC, 0) AS avg_recency_days,
    ROUND(AVG(COALESCE(order_counts.freq, 0))::NUMERIC, 1) AS avg_frequency,
    COUNT(DISTINCT CASE WHEN ct.cart_status = 'abandoned' THEN ct.cart_id END) AS abandoned_carts,
    COUNT(DISTINCT ct.cart_id) AS total_carts,
    CASE WHEN COUNT(DISTINCT ct.cart_id) > 0 
         THEN ROUND(COUNT(DISTINCT CASE WHEN ct.cart_status = 'abandoned' THEN ct.cart_id END)::NUMERIC 
              / COUNT(DISTINCT ct.cart_id) * 100, 1)
         ELSE 0 END AS abandonment_rate
FROM customer c
LEFT JOIN (
    SELECT customer_id, MAX(DATE(order_date)) AS last_order
    FROM order_table WHERE order_status NOT IN ('cancelled')
    GROUP BY customer_id
) MAX_order ON c.customer_id = MAX_order.customer_id
LEFT JOIN (
    SELECT customer_id, COUNT(DISTINCT order_id) AS freq
    FROM order_table WHERE order_status NOT IN ('cancelled')
    GROUP BY customer_id
) order_counts ON c.customer_id = order_counts.customer_id
LEFT JOIN cart ct ON c.customer_id = ct.customer_id
GROUP BY COALESCE(c.segment, 'Unknown');

-- ============================================================
-- View 5: Conversion Funnel (weekly)
-- ============================================================
CREATE VIEW v_conversion_funnel AS
SELECT 
    DATE_TRUNC('week', e.event_timestamp)::DATE AS week_start,
    COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) AS view_sessions,
    COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END) AS cart_sessions,
    COUNT(DISTINCT CASE WHEN e.event_type = 'checkout_start' THEN e.session_id END) AS checkout_sessions,
    COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END) AS purchase_sessions,
    -- Drop-off percentages
    CASE WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) > 0
         THEN ROUND(COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END)::NUMERIC 
              / COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) * 100, 1)
         ELSE 0 END AS view_to_cart_pct,
    CASE WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END) > 0
         THEN ROUND(COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END)::NUMERIC 
              / COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END) * 100, 1)
         ELSE 0 END AS cart_to_purchase_pct
FROM event e
GROUP BY DATE_TRUNC('week', e.event_timestamp)
ORDER BY week_start;

-- ============================================================
-- View 6: Customer Behavior Summary (for quick lookups)
-- ============================================================
CREATE VIEW v_customer_summary AS
SELECT 
    c.customer_id,
    c.customer_code,
    c.segment,
    c.lifetime_value,
    c.registration_date,
    COUNT(DISTINCT s.session_id) AS total_sessions,
    COUNT(DISTINCT e.event_id) AS total_events,
    COUNT(DISTINCT o.order_id) AS total_orders,
    COALESCE(SUM(o.total_amount), 0) AS total_spent,
    COUNT(DISTINCT r.review_id) AS total_reviews,
    COUNT(DISTINCT ret.return_id) AS total_returns,
    COUNT(DISTINCT CASE WHEN ct.cart_status = 'abandoned' THEN ct.cart_id END) AS abandoned_carts,
    MAX(o.order_date) AS last_order_date,
    MAX(s.session_start) AS last_session_date
FROM customer c
LEFT JOIN session s ON c.customer_id = s.customer_id
LEFT JOIN event e ON c.customer_id = e.customer_id
LEFT JOIN order_table o ON c.customer_id = o.customer_id AND o.order_status NOT IN ('cancelled')
LEFT JOIN review r ON c.customer_id = r.customer_id
LEFT JOIN return_table ret ON c.customer_id = ret.customer_id
LEFT JOIN cart ct ON c.customer_id = ct.customer_id
GROUP BY c.customer_id, c.customer_code, c.segment, c.lifetime_value, c.registration_date;

SELECT 'All views and materialized views created successfully.' AS status;
