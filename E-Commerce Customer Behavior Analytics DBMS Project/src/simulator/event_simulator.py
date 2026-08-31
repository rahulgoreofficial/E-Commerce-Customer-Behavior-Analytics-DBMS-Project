"""
E-Commerce Event Simulator — Generates realistic customer events in real-time.
Inserts events into PostgreSQL to make the system dynamic.
"""
import random
import threading
import time
from datetime import datetime, timedelta
from src.database.connection import db
from src.config import (
    SIM_EVENTS_PER_BATCH, SIM_BATCH_INTERVAL_SEC, SIM_PURCHASE_PROB,
    SIM_CART_ADD_PROB, SIM_CART_ABANDON_PROB, SIM_REVIEW_PROB,
    SIM_RETURN_PROB, SIM_MOBILE_RATIO,
)

SEARCH_QUERIES = [
    "best smartphone", "running shoes sale", "laptop deals", "wireless earbuds",
    "cotton shirts men", "kitchen blender", "fiction books", "skincare routine",
    "gaming accessories", "yoga mat", "winter wear", "smartwatch under 5000",
]

RETURN_REASONS = ["defective", "wrong_size", "not_as_described", "changed_mind", "damaged"]
PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "COD"]


class EventSimulator:
    """Generates realistic e-commerce customer events and inserts them into PostgreSQL."""

    def __init__(self, config=None):
        self.running = False
        self._thread = None
        self._customer_ids = []
        self._product_ids = []
        self._stop_event = threading.Event()
        self.stats = {"sessions": 0, "events": 0, "carts": 0, "orders": 0, "batches": 0}
        self.callbacks = []  # UI callbacks for real-time updates

        # Configurable parameters
        self.events_per_batch = SIM_EVENTS_PER_BATCH
        self.batch_interval = SIM_BATCH_INTERVAL_SEC
        self.purchase_prob = SIM_PURCHASE_PROB
        self.cart_add_prob = SIM_CART_ADD_PROB
        self.cart_abandon_prob = SIM_CART_ABANDON_PROB
        self.mobile_ratio = SIM_MOBILE_RATIO

        if config:
            for k, v in config.items():
                if hasattr(self, k):
                    setattr(self, k, v)

    def add_callback(self, fn):
        """Register a callback to be called after each batch."""
        self.callbacks.append(fn)

    def _notify(self, message):
        for cb in self.callbacks:
            try:
                cb(message, self.stats.copy())
            except Exception:
                pass

    def _load_ids(self):
        """Load existing customer and product IDs from database."""
        self._customer_ids = [
            r["customer_id"] for r in db.execute_query("SELECT customer_id FROM customer ORDER BY RANDOM() LIMIT 200")
        ]
        self._product_ids = [
            r["product_id"] for r in db.execute_query("SELECT product_id FROM product WHERE is_active = TRUE ORDER BY RANDOM() LIMIT 100")
        ]
        if not self._customer_ids or not self._product_ids:
            raise ValueError("No customers or products in database. Run seed_data first.")

    def start(self, num_batches=None):
        """Start generating events in a background thread."""
        if self.running:
            return
        self._stop_event.clear()
        self._load_ids()
        self.running = True
        self._thread = threading.Thread(target=self._run, args=(num_batches,), daemon=True)
        self._thread.start()

    def stop(self):
        """Stop the simulator."""
        self._stop_event.set()
        self.running = False
        if self._thread:
            self._thread.join(timeout=5)

    def _run(self, num_batches=None):
        """Main simulation loop."""
        batch = 0
        while not self._stop_event.is_set():
            if num_batches and batch >= num_batches:
                break
            try:
                self._generate_batch()
                batch += 1
                self.stats["batches"] = batch
                self._notify(f"Batch {batch} complete: {self.stats['events']} total events")
            except Exception as e:
                self._notify(f"Error in batch: {e}")

            self._stop_event.wait(timeout=self.batch_interval)

        self.running = False
        self._notify("Simulator stopped.")

    def _generate_batch(self):
        """Generate one batch of sessions/events."""
        num_sessions = max(1, self.events_per_batch // 5)
        
        with db.transaction() as cur:
            for _ in range(num_sessions):
                self._generate_session(cur)

    def _generate_session(self, cur):
        """Simulate a complete shopping session."""
        cust_id = random.choice(self._customer_ids)
        now = datetime.now()
        session_start = now - timedelta(minutes=random.randint(0, 5))
        device = random.choices(["mobile", "desktop", "tablet"],
                                weights=[int(self.mobile_ratio * 100), int((1 - self.mobile_ratio) * 70), 15])[0]
        channel = "mobile_app" if device == "mobile" else ("mobile_web" if device == "tablet" else "web")
        duration = random.randint(60, 3600)
        session_end = session_start + timedelta(seconds=duration)

        cur.execute("""
            INSERT INTO session (customer_id, session_start, session_end, device, channel, session_duration_sec)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING session_id
        """, (cust_id, session_start, session_end, device, channel, duration))
        session_id = cur.fetchone()["session_id"]
        self.stats["sessions"] += 1

        viewed_products = random.sample(self._product_ids, min(random.randint(1, 6), len(self._product_ids)))
        event_time = session_start + timedelta(seconds=random.randint(3, 15))

        # ── Search ──
        if random.random() < 0.35:
            cur.execute("""
                INSERT INTO event (session_id, customer_id, event_type, event_timestamp, event_data)
                VALUES (%s, %s, 'search', %s, %s)
            """, (session_id, cust_id, event_time,
                  f'{{"query": "{random.choice(SEARCH_QUERIES)}"}}'))
            event_time += timedelta(seconds=random.randint(5, 20))
            self.stats["events"] += 1

        # ── Views ──
        for prod_id in viewed_products:
            cur.execute("""
                INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                VALUES (%s, %s, %s, 'product_view', %s)
            """, (session_id, cust_id, prod_id, event_time))
            event_time += timedelta(seconds=random.randint(10, 90))
            self.stats["events"] += 1

            if random.random() < 0.12:
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                    VALUES (%s, %s, %s, 'compare', %s)
                """, (session_id, cust_id, prod_id, event_time))
                event_time += timedelta(seconds=random.randint(10, 40))
                self.stats["events"] += 1

        # ── Cart ──
        if random.random() < self.cart_add_prob:
            cart_prods = random.sample(viewed_products, min(random.randint(1, 3), len(viewed_products)))
            cur.execute("""
                INSERT INTO cart (customer_id, session_id, created_at)
                VALUES (%s, %s, %s) RETURNING cart_id
            """, (cust_id, session_id, event_time))
            cart_id = cur.fetchone()["cart_id"]
            self.stats["carts"] += 1

            for cp_id in cart_prods:
                cur.execute("SELECT price FROM product WHERE product_id = %s", (cp_id,))
                price = float(cur.fetchone()["price"])
                qty = random.randint(1, 2)
                cur.execute("""
                    INSERT INTO cart_item (cart_id, product_id, quantity, unit_price, added_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (cart_id, cp_id, qty, price, event_time))
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                    VALUES (%s, %s, %s, 'add_to_cart', %s)
                """, (session_id, cust_id, cp_id, event_time))
                event_time += timedelta(seconds=random.randint(5, 20))
                self.stats["events"] += 1

            # ── Purchase or Abandon ──
            if random.random() > self.cart_abandon_prob:
                # Checkout
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, event_type, event_timestamp)
                    VALUES (%s, %s, 'checkout_start', %s)
                """, (session_id, cust_id, event_time))
                event_time += timedelta(seconds=random.randint(30, 120))
                self.stats["events"] += 1

                cur.execute("""
                    SELECT COALESCE(SUM(quantity * unit_price), 0) AS total 
                    FROM cart_item WHERE cart_id = %s AND removed_at IS NULL
                """, (cart_id,))
                cart_total = float(cur.fetchone()["total"])
                if cart_total <= 0:
                    cart_total = 499.0

                cur.execute("""
                    INSERT INTO event (session_id, customer_id, event_type, event_timestamp)
                    VALUES (%s, %s, 'checkout_complete', %s)
                """, (session_id, cust_id, event_time))
                self.stats["events"] += 1

                payment_method = random.choice(PAYMENT_METHODS)
                cur.execute("""
                    INSERT INTO order_table (customer_id, cart_id, order_date, order_status, 
                                             total_amount, payment_method)
                    VALUES (%s, %s, %s, 'confirmed', %s, %s) RETURNING order_id
                """, (cust_id, cart_id, event_time, cart_total, payment_method))
                order_id = cur.fetchone()["order_id"]
                self.stats["orders"] += 1

                cur.execute("""
                    INSERT INTO order_item (order_id, product_id, quantity, unit_price, subtotal)
                    SELECT %s, product_id, quantity, unit_price, quantity * unit_price
                    FROM cart_item WHERE cart_id = %s AND removed_at IS NULL
                """, (order_id, cart_id))

                cur.execute("""
                    INSERT INTO payment (order_id, payment_method, payment_status, amount, payment_date)
                    VALUES (%s, %s, 'completed', %s, %s)
                """, (order_id, payment_method, cart_total, event_time))

                for cp_id in cart_prods:
                    cur.execute("""
                        INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                        VALUES (%s, %s, %s, 'purchase', %s)
                    """, (session_id, cust_id, cp_id, event_time))
                    self.stats["events"] += 1

                cur.execute("UPDATE cart SET cart_status = 'converted' WHERE cart_id = %s", (cart_id,))
            else:
                cur.execute("UPDATE cart SET cart_status = 'abandoned' WHERE cart_id = %s", (cart_id,))

    def get_stats(self):
        return self.stats.copy()

    def update_config(self, **kwargs):
        """Update simulator parameters at runtime."""
        for k, v in kwargs.items():
            if hasattr(self, k):
                setattr(self, k, v)


# Module-level singleton
simulator = EventSimulator()
