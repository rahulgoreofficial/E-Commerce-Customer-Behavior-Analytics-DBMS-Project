"""
SQL Analytics Module — All SQL-based analytics queries.
Provides functions for RFM, funnels, cohorts, product analytics, campaign analytics.
"""
from src.database.connection import db


class SQLAnalytics:
    """SQL-based analytics engine. All metrics flow from PostgreSQL."""

    # ──────────────────────────────────────────────
    # DASHBOARD KPIs
    # ──────────────────────────────────────────────
    def get_dashboard_kpis(self, days=7):
        """Get key performance indicators for the dashboard."""
        return db.execute_query("""
            WITH current_period AS (
                SELECT 
                    COUNT(DISTINCT order_id) AS orders,
                    COUNT(DISTINCT customer_id) AS customers,
                    COALESCE(SUM(total_amount), 0) AS revenue,
                    COALESCE(AVG(total_amount), 0) AS aov
                FROM order_table
                WHERE order_date >= NOW() - INTERVAL '%s days'
                AND order_status NOT IN ('cancelled', 'returned')
            ),
            previous_period AS (
                SELECT 
                    COUNT(DISTINCT order_id) AS orders,
                    COUNT(DISTINCT customer_id) AS customers,
                    COALESCE(SUM(total_amount), 0) AS revenue,
                    COALESCE(AVG(total_amount), 0) AS aov
                FROM order_table
                WHERE order_date >= NOW() - INTERVAL '%s days'
                AND order_date < NOW() - INTERVAL '%s days'
                AND order_status NOT IN ('cancelled', 'returned')
            ),
            conversion AS (
                SELECT 
                    COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) AS views,
                    COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS purchases
                FROM event
                WHERE event_timestamp >= NOW() - INTERVAL '%s days'
            ),
            abandonment AS (
                SELECT 
                    COUNT(CASE WHEN cart_status = 'abandoned' THEN 1 END) AS abandoned,
                    COUNT(*) AS total_carts
                FROM cart
                WHERE created_at >= NOW() - INTERVAL '%s days'
            )
            SELECT 
                cp.orders, cp.customers, cp.revenue, cp.aov,
                pp.orders AS prev_orders, pp.revenue AS prev_revenue,
                CASE WHEN conv.views > 0 
                     THEN ROUND(conv.purchases::NUMERIC / conv.views * 100, 2) ELSE 0 END AS conversion_rate,
                CASE WHEN ab.total_carts > 0 
                     THEN ROUND(ab.abandoned::NUMERIC / ab.total_carts * 100, 1) ELSE 0 END AS abandonment_rate
            FROM current_period cp, previous_period pp, conversion conv, abandonment ab
        """, (days, days * 2, days, days, days))

    def get_revenue_trend(self, days=30):
        """Daily revenue for the last N days."""
        return db.execute_query("""
            SELECT DATE(order_date) AS date, 
                   COALESCE(SUM(total_amount), 0) AS revenue,
                   COUNT(DISTINCT order_id) AS orders
            FROM order_table
            WHERE order_date >= NOW() - INTERVAL '%s days'
            AND order_status NOT IN ('cancelled', 'returned')
            GROUP BY DATE(order_date)
            ORDER BY date
        """, (days,))

    # ──────────────────────────────────────────────
    # RFM ANALYSIS
    # ──────────────────────────────────────────────
    def get_rfm_segments(self):
        """Get customer RFM segment distribution."""
        return db.execute_query("""
            SELECT segment, COUNT(*) AS count,
                   ROUND(AVG(lifetime_value)::NUMERIC, 2) AS avg_ltv
            FROM customer
            WHERE segment IS NOT NULL
            GROUP BY segment
            ORDER BY avg_ltv DESC
        """)

    def get_rfm_details(self, segment=None, limit=100):
        """Get individual RFM scores. Optionally filter by segment."""
        query = """
            SELECT customer_id, customer_code, segment, 
                   recency_days, frequency, monetary,
                   r_score, f_score, m_score
            FROM mv_customer_rfm
        """
        params = []
        if segment:
            query += " WHERE segment = %s"
            params.append(segment)
        query += f" ORDER BY monetary DESC LIMIT {limit}"
        return db.execute_query(query, params if params else None)

    # ──────────────────────────────────────────────
    # FUNNEL ANALYTICS
    # ──────────────────────────────────────────────
    def get_funnel_data(self, days=30):
        """Get conversion funnel: View → Cart → Checkout → Purchase."""
        return db.execute_query("""
            SELECT 
                COUNT(DISTINCT CASE WHEN event_type = 'product_view' THEN session_id END) AS view_sessions,
                COUNT(DISTINCT CASE WHEN event_type = 'add_to_cart' THEN session_id END) AS cart_sessions,
                COUNT(DISTINCT CASE WHEN event_type = 'checkout_start' THEN session_id END) AS checkout_sessions,
                COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN session_id END) AS purchase_sessions
            FROM event
            WHERE event_timestamp >= NOW() - INTERVAL '%s days'
        """, (days,))

    def get_funnel_by_device(self, days=30):
        """Funnel breakdown by device type."""
        return db.execute_query("""
            SELECT 
                s.device,
                COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) AS views,
                COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.session_id END) AS carts,
                COUNT(DISTINCT CASE WHEN e.event_type = 'checkout_start' THEN e.session_id END) AS checkouts,
                COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END) AS purchases,
                CASE WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) > 0
                     THEN ROUND(COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.session_id END)::NUMERIC 
                          / COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.session_id END) * 100, 2)
                     ELSE 0 END AS conversion_pct
            FROM event e
            JOIN session s ON e.session_id = s.session_id
            WHERE e.event_timestamp >= NOW() - INTERVAL '%s days'
            GROUP BY s.device
            ORDER BY conversion_pct DESC
        """, (days,))

    def get_funnel_weekly_trend(self, weeks=8):
        """Weekly funnel trend."""
        return db.execute_query("""
            SELECT * FROM v_conversion_funnel
            WHERE week_start >= NOW() - INTERVAL '%s weeks'
            ORDER BY week_start
        """, (weeks,))

    # ──────────────────────────────────────────────
    # PRODUCT ANALYTICS
    # ──────────────────────────────────────────────
    def get_product_performance(self, limit=50, sort_by="total_views"):
        """Get product performance metrics."""
        valid_sorts = ["total_views", "total_purchases", "view_to_cart_rate", "avg_rating", "total_returns"]
        sort_col = sort_by if sort_by in valid_sorts else "total_views"
        return db.execute_query(f"""
            SELECT * FROM mv_product_performance
            ORDER BY {sort_col} DESC
            LIMIT %s
        """, (limit,))

    def get_problem_products(self):
        """Products with high views but low conversion or high returns."""
        return db.execute_query("""
            SELECT * FROM mv_product_performance
            WHERE total_views > 20 
            AND (view_to_cart_rate < 5.0 OR cart_to_purchase_rate < 10.0 OR total_returns > 3)
            ORDER BY total_views DESC
        """)

    # ──────────────────────────────────────────────
    # COHORT ANALYTICS
    # ──────────────────────────────────────────────
    def get_cohort_retention(self):
        """Monthly registration cohort retention analysis."""
        return db.execute_query("""
            WITH cohort AS (
                SELECT customer_id, DATE_TRUNC('month', registration_date)::DATE AS cohort_month
                FROM customer
            ),
            activity AS (
                SELECT o.customer_id, DATE_TRUNC('month', o.order_date)::DATE AS activity_month
                FROM order_table o WHERE o.order_status NOT IN ('cancelled')
            )
            SELECT 
                c.cohort_month,
                COUNT(DISTINCT c.customer_id) AS cohort_size,
                COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month THEN c.customer_id END) AS month_0,
                COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '1 month' THEN c.customer_id END) AS month_1,
                COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '2 months' THEN c.customer_id END) AS month_2,
                COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '3 months' THEN c.customer_id END) AS month_3,
                COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '4 months' THEN c.customer_id END) AS month_4,
                COUNT(DISTINCT CASE WHEN a.activity_month = c.cohort_month + INTERVAL '5 months' THEN c.customer_id END) AS month_5
            FROM cohort c
            LEFT JOIN activity a ON c.customer_id = a.customer_id
            GROUP BY c.cohort_month
            HAVING COUNT(DISTINCT c.customer_id) >= 5
            ORDER BY c.cohort_month
        """)

    # ──────────────────────────────────────────────
    # CAMPAIGN ANALYTICS
    # ──────────────────────────────────────────────
    def get_campaign_performance(self):
        """Campaign effectiveness metrics."""
        return db.execute_query("""
            SELECT 
                c.campaign_id, c.campaign_name, c.campaign_type, c.target_segment, c.status,
                COUNT(DISTINCT CASE WHEN ci.interaction_type = 'sent' THEN ci.customer_id END) AS sent,
                COUNT(DISTINCT CASE WHEN ci.interaction_type = 'opened' THEN ci.customer_id END) AS opened,
                COUNT(DISTINCT CASE WHEN ci.interaction_type = 'clicked' THEN ci.customer_id END) AS clicked,
                COUNT(DISTINCT CASE WHEN ci.interaction_type = 'converted' THEN ci.customer_id END) AS converted,
                CASE WHEN COUNT(DISTINCT CASE WHEN ci.interaction_type = 'sent' THEN ci.customer_id END) > 0
                     THEN ROUND(COUNT(DISTINCT CASE WHEN ci.interaction_type = 'opened' THEN ci.customer_id END)::NUMERIC 
                          / COUNT(DISTINCT CASE WHEN ci.interaction_type = 'sent' THEN ci.customer_id END) * 100, 1)
                     ELSE 0 END AS open_rate,
                CASE WHEN COUNT(DISTINCT CASE WHEN ci.interaction_type = 'opened' THEN ci.customer_id END) > 0
                     THEN ROUND(COUNT(DISTINCT CASE WHEN ci.interaction_type = 'clicked' THEN ci.customer_id END)::NUMERIC 
                          / COUNT(DISTINCT CASE WHEN ci.interaction_type = 'opened' THEN ci.customer_id END) * 100, 1)
                     ELSE 0 END AS click_rate,
                CASE WHEN COUNT(DISTINCT CASE WHEN ci.interaction_type = 'clicked' THEN ci.customer_id END) > 0
                     THEN ROUND(COUNT(DISTINCT CASE WHEN ci.interaction_type = 'converted' THEN ci.customer_id END)::NUMERIC 
                          / COUNT(DISTINCT CASE WHEN ci.interaction_type = 'clicked' THEN ci.customer_id END) * 100, 1)
                     ELSE 0 END AS conversion_rate
            FROM campaign c
            LEFT JOIN campaign_interaction ci ON c.campaign_id = ci.campaign_id
            GROUP BY c.campaign_id, c.campaign_name, c.campaign_type, c.target_segment, c.status
            ORDER BY converted DESC
        """)

    # ──────────────────────────────────────────────
    # CUSTOMER ANALYTICS
    # ──────────────────────────────────────────────
    def get_customer_list(self, segment=None, limit=100):
        """Get customer list with summary metrics."""
        query = """
            SELECT customer_id, customer_code, segment, lifetime_value, 
                   registration_date, age_group, gender, city, preferred_channel
            FROM customer
        """
        params = []
        if segment:
            query += " WHERE segment = %s"
            params.append(segment)
        query += f" ORDER BY lifetime_value DESC LIMIT {limit}"
        return db.execute_query(query, params if params else None)

    def get_customer_detail(self, customer_id):
        """Get detailed customer information."""
        return db.execute_query("""
            SELECT * FROM v_customer_summary WHERE customer_id = %s
        """, (customer_id,))

    def get_customer_events(self, customer_id, limit=50):
        """Get recent events for a specific customer."""
        return db.execute_query("""
            SELECT e.event_id, e.event_type, e.event_timestamp, 
                   p.product_name, p.price, s.device, s.channel
            FROM event e
            LEFT JOIN product p ON e.product_id = p.product_id
            JOIN session s ON e.session_id = s.session_id
            WHERE e.customer_id = %s
            ORDER BY e.event_timestamp DESC
            LIMIT %s
        """, (customer_id, limit))

    # ──────────────────────────────────────────────
    # DATABASE PERFORMANCE BENCHMARK
    # ──────────────────────────────────────────────
    def get_table_sizes(self):
        """Get row counts for all project tables."""
        return db.execute_query("""
            SELECT 'customer' AS table_name, COUNT(*) AS row_count FROM customer
            UNION ALL SELECT 'product', COUNT(*) FROM product
            UNION ALL SELECT 'session', COUNT(*) FROM session
            UNION ALL SELECT 'event', COUNT(*) FROM event
            UNION ALL SELECT 'cart', COUNT(*) FROM cart
            UNION ALL SELECT 'cart_item', COUNT(*) FROM cart_item
            UNION ALL SELECT 'order_table', COUNT(*) FROM order_table
            UNION ALL SELECT 'order_item', COUNT(*) FROM order_item
            UNION ALL SELECT 'review', COUNT(*) FROM review
            UNION ALL SELECT 'payment', COUNT(*) FROM payment
            UNION ALL SELECT 'return_table', COUNT(*) FROM return_table
            UNION ALL SELECT 'campaign', COUNT(*) FROM campaign
            UNION ALL SELECT 'campaign_interaction', COUNT(*) FROM campaign_interaction
            UNION ALL SELECT 'category', COUNT(*) FROM category
            ORDER BY row_count DESC
        """)

    def benchmark_query(self, query, params=None):
        """Run EXPLAIN ANALYZE and return execution plan."""
        explain_query = f"EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON) {query}"
        result = db.execute_query(explain_query, params)
        return result


# Module-level singleton
analytics = SQLAnalytics()
