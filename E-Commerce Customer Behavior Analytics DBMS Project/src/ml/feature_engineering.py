"""
Feature Engineering — Extracts ML-ready features from the database.
"""
import pandas as pd
from src.database.connection import db


class FeatureEngineer:
    """Extracts feature vectors from PostgreSQL for ML models."""

    def get_purchase_prediction_features(self):
        """Extract session-level features for purchase prediction.
        
        Target: purchased (1 if session has a purchase event, 0 otherwise)
        """
        query = """
        SELECT 
            s.session_id,
            s.customer_id,
            -- Session features
            COALESCE(EXTRACT(EPOCH FROM (s.session_end - s.session_start)) / 60.0, 0) AS session_duration_min,
            COALESCE(s.total_events, 0) AS total_events,
            s.device,
            s.channel,
            EXTRACT(DOW FROM s.session_start) AS day_of_week,
            EXTRACT(HOUR FROM s.session_start) AS hour_of_day,
            
            -- Behavioral features
            COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.event_id END) AS pages_viewed,
            COUNT(DISTINCT CASE WHEN e.event_type = 'product_view' THEN e.product_id END) AS products_viewed,
            COUNT(DISTINCT CASE WHEN e.event_type = 'search' THEN e.event_id END) AS searches,
            COUNT(DISTINCT CASE WHEN e.event_type = 'add_to_cart' THEN e.event_id END) AS cart_adds,
            COUNT(DISTINCT CASE WHEN e.event_type = 'remove_from_cart' THEN e.event_id END) AS cart_removes,
            COUNT(DISTINCT CASE WHEN e.event_type = 'compare' THEN e.event_id END) AS compares,
            COUNT(DISTINCT CASE WHEN e.event_type = 'wishlist' THEN e.event_id END) AS wishlists,
            
            -- Customer history features
            CASE WHEN EXISTS (
                SELECT 1 FROM order_table o 
                WHERE o.customer_id = s.customer_id AND o.order_date < s.session_start
            ) THEN 1 ELSE 0 END AS is_returning_customer,
            
            COALESCE((
                SELECT COUNT(DISTINCT o.order_id) FROM order_table o 
                WHERE o.customer_id = s.customer_id AND o.order_date < s.session_start
                AND o.order_status NOT IN ('cancelled')
            ), 0) AS past_orders,
            
            COALESCE((
                SELECT AVG(o.total_amount) FROM order_table o 
                WHERE o.customer_id = s.customer_id AND o.order_date < s.session_start
                AND o.order_status NOT IN ('cancelled')
            ), 0) AS avg_past_order_value,
            
            -- Target variable
            CASE WHEN COUNT(DISTINCT CASE WHEN e.event_type = 'purchase' THEN e.event_id END) > 0 
                 THEN 1 ELSE 0 END AS purchased
                 
        FROM session s
        LEFT JOIN event e ON s.session_id = e.session_id
        WHERE s.session_end IS NOT NULL
        GROUP BY s.session_id, s.customer_id, s.session_start, s.session_end, 
                 s.total_events, s.device, s.channel
        """
        df = pd.read_sql(query, db.connect())
        
        # One-hot encode categorical variables
        df = pd.get_dummies(df, columns=['device', 'channel'], drop_first=True)
        
        return df

    def get_cart_abandonment_features(self):
        """Extract cart-level features for cart abandonment prediction.
        
        Target: abandoned (1 if cart_status='abandoned', 0 if 'converted')
        """
        query = """
        SELECT 
            c.cart_id,
            c.customer_id,
            
            -- Cart features
            c.total_value AS cart_value,
            COUNT(DISTINCT ci.cart_item_id) AS num_items,
            COUNT(DISTINCT ci.product_id) AS num_unique_products,
            COALESCE(AVG(ci.unit_price), 0) AS avg_item_price,
            COALESCE(MAX(ci.unit_price), 0) AS max_item_price,
            COALESCE(MIN(ci.unit_price), 0) AS min_item_price,
            COALESCE(SUM(ci.quantity), 0) AS total_quantity,
            
            -- Cart behavior
            COUNT(CASE WHEN ci.removed_at IS NOT NULL THEN 1 END) AS items_removed,
            
            -- Session context
            COALESCE(EXTRACT(EPOCH FROM (s.session_end - s.session_start)) / 60.0, 0) AS session_duration_min,
            s.device,
            s.channel,
            EXTRACT(DOW FROM c.created_at) AS day_of_week,
            EXTRACT(HOUR FROM c.created_at) AS hour_of_day,
            
            -- Events before cart
            COALESCE((
                SELECT COUNT(*) FROM event e 
                WHERE e.session_id = s.session_id 
                AND e.event_timestamp < c.created_at
            ), 0) AS events_before_cart,
            
            -- Checkout started?
            CASE WHEN EXISTS (
                SELECT 1 FROM event e 
                WHERE e.session_id = s.session_id AND e.event_type = 'checkout_start'
            ) THEN 1 ELSE 0 END AS checkout_started,
            
            -- Customer history
            CASE WHEN EXISTS (
                SELECT 1 FROM order_table o WHERE o.customer_id = c.customer_id
                AND o.order_date < c.created_at
            ) THEN 1 ELSE 0 END AS is_returning_customer,
            
            COALESCE((
                SELECT COUNT(CASE WHEN ct.cart_status = 'abandoned' THEN 1 END)::NUMERIC / 
                       NULLIF(COUNT(*), 0)
                FROM cart ct WHERE ct.customer_id = c.customer_id AND ct.created_at < c.created_at
            ), 0) AS past_abandonment_rate,
            
            -- Target
            CASE WHEN c.cart_status = 'abandoned' THEN 1 ELSE 0 END AS abandoned
            
        FROM cart c
        JOIN session s ON c.session_id = s.session_id
        LEFT JOIN cart_item ci ON c.cart_id = ci.cart_id
        WHERE c.cart_status IN ('abandoned', 'converted')
        GROUP BY c.cart_id, c.customer_id, c.total_value, c.cart_status, c.created_at,
                 s.session_start, s.session_end, s.device, s.channel, s.session_id
        """
        df = pd.read_sql(query, db.connect())
        df = pd.get_dummies(df, columns=['device', 'channel'], drop_first=True)
        return df


# Module-level singleton
feature_engineer = FeatureEngineer()
