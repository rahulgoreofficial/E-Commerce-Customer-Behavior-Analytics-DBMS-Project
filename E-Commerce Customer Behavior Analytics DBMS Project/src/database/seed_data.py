"""
Seed Data Generator — Creates realistic initial data for the database.
Run this ONCE after creating tables to populate with base data.
"""
import random
import string
from datetime import datetime, timedelta
from src.database.connection import db

# ── Configuration ──────────────────────────────────────────────
NUM_CUSTOMERS = 500
NUM_PRODUCTS = 150
NUM_SESSIONS = 3000
NUM_CAMPAIGNS = 10

CATEGORIES = [
    ("Electronics", None),
    ("Smartphones", "Electronics"),
    ("Laptops", "Electronics"),
    ("Accessories", "Electronics"),
    ("Clothing", None),
    ("Men's Clothing", "Clothing"),
    ("Women's Clothing", "Clothing"),
    ("Footwear", "Clothing"),
    ("Home & Kitchen", None),
    ("Appliances", "Home & Kitchen"),
    ("Furniture", "Home & Kitchen"),
    ("Books", None),
    ("Health & Beauty", None),
    ("Sports & Outdoors", None),
    ("Toys & Games", None),
]

BRANDS = [
    "Samsung", "Apple", "OnePlus", "Xiaomi", "Realme", "HP", "Dell", "Lenovo",
    "Nike", "Adidas", "Puma", "Levi's", "H&M", "Zara", "Allen Solly",
    "Philips", "Prestige", "Godrej", "Bosch", "LG", "Sony",
    "Penguin", "HarperCollins", "Himalaya", "Mamaearth", "Boat", "Noise",
]

CITIES = [
    ("Mumbai", "Maharashtra"), ("Delhi", "Delhi"), ("Bangalore", "Karnataka"),
    ("Hyderabad", "Telangana"), ("Chennai", "Tamil Nadu"), ("Kolkata", "West Bengal"),
    ("Pune", "Maharashtra"), ("Ahmedabad", "Gujarat"), ("Jaipur", "Rajasthan"),
    ("Lucknow", "Uttar Pradesh"), ("Nagpur", "Maharashtra"), ("Indore", "Madhya Pradesh"),
    ("Chandigarh", "Punjab"), ("Kochi", "Kerala"), ("Bhopal", "Madhya Pradesh"),
]

PAYMENT_METHODS = ["UPI", "Credit Card", "Debit Card", "Net Banking", "COD", "Wallet"]
RETURN_REASONS = ["defective", "wrong_size", "not_as_described", "changed_mind", "late_delivery", "damaged"]
SEARCH_QUERIES = [
    "smartphone under 15000", "running shoes", "laptop for students", "wireless earbuds",
    "cotton shirts", "kitchen mixer", "bestseller books", "face cream", "gaming mouse",
    "yoga mat", "winter jacket", "smart watch", "protein powder", "backpack",
    "bluetooth speaker", "office chair", "water bottle", "phone case", "led tv",
]


def random_date(start_days_ago=365, end_days_ago=0):
    """Generate a random datetime within the given range."""
    start = datetime.now() - timedelta(days=start_days_ago)
    end = datetime.now() - timedelta(days=end_days_ago)
    delta = end - start
    random_seconds = random.randint(0, int(delta.total_seconds()))
    return start + timedelta(seconds=random_seconds)


def generate_product_name(category, brand):
    suffix = random.choice(["Pro", "Max", "Lite", "Plus", "Ultra", "X", "Neo", "Air", "SE", ""])
    model = ''.join(random.choices(string.ascii_uppercase + string.digits, k=3))
    return f"{brand} {category} {suffix} {model}".strip()


def seed_categories(cur):
    """Insert categories with hierarchy."""
    print("  Seeding categories...")
    cat_ids = {}
    for cat_name, parent_name in CATEGORIES:
        parent_id = cat_ids.get(parent_name)
        cur.execute(
            "INSERT INTO category (category_name, parent_category_id) VALUES (%s, %s) RETURNING category_id",
            (cat_name, parent_id)
        )
        cat_ids[cat_name] = cur.fetchone()["category_id"]
    return cat_ids


def seed_customers(cur):
    """Insert customer records."""
    print(f"  Seeding {NUM_CUSTOMERS} customers...")
    customer_ids = []
    for i in range(1, NUM_CUSTOMERS + 1):
        city, state = random.choice(CITIES)
        cur.execute("""
            INSERT INTO customer (customer_code, registration_date, age_group, gender, city, state, 
                                  country, preferred_channel, segment)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING customer_id
        """, (
            f"CUST{i:05d}",
            random_date(730, 30).date(),
            random.choice(["18-24", "25-34", "35-44", "45-54", "55+"]),
            random.choices(["M", "F", "Other", "Unknown"], weights=[45, 42, 3, 10])[0],
            city, state, "India",
            random.choice(["web", "mobile_app", "mobile_web"]),
            "New",
        ))
        customer_ids.append(cur.fetchone()["customer_id"])
    return customer_ids


def seed_products(cur, cat_ids):
    """Insert product records."""
    print(f"  Seeding {NUM_PRODUCTS} products...")
    product_ids = []
    leaf_cats = [name for name, parent in CATEGORIES if parent is not None]
    if not leaf_cats:
        leaf_cats = [name for name, _ in CATEGORIES]

    for i in range(1, NUM_PRODUCTS + 1):
        cat_name = random.choice(leaf_cats)
        cat_id = cat_ids[cat_name]
        brand = random.choice(BRANDS)
        price = round(random.uniform(99, 79999), 2)
        original_price = round(price * random.uniform(1.0, 1.4), 2)
        cur.execute("""
            INSERT INTO product (product_code, product_name, category_id, brand, price, original_price, 
                                 stock_quantity, is_active)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s) RETURNING product_id
        """, (
            f"PROD{i:05d}",
            generate_product_name(cat_name, brand),
            cat_id, brand, price, original_price,
            random.randint(0, 500),
            random.random() > 0.05,
        ))
        product_ids.append(cur.fetchone()["product_id"])
    return product_ids


def seed_sessions_and_events(cur, customer_ids, product_ids):
    """Generate sessions with realistic event sequences, carts, orders, reviews, returns."""
    print(f"  Seeding {NUM_SESSIONS} sessions with events, carts, orders...")
    
    total_orders = 0
    total_events = 0
    total_carts = 0
    total_reviews = 0
    total_returns = 0

    for _ in range(NUM_SESSIONS):
        cust_id = random.choice(customer_ids)
        session_start = random_date(180, 1)
        duration_min = random.randint(1, 60)
        session_end = session_start + timedelta(minutes=duration_min)
        device = random.choices(["mobile", "desktop", "tablet"], weights=[55, 35, 10])[0]
        channel = "mobile_app" if device == "mobile" else ("mobile_web" if device == "tablet" else "web")

        cur.execute("""
            INSERT INTO session (customer_id, session_start, session_end, device, channel, 
                                 session_duration_sec)
            VALUES (%s, %s, %s, %s, %s, %s) RETURNING session_id
        """, (cust_id, session_start, session_end, device, channel, duration_min * 60))
        session_id = cur.fetchone()["session_id"]

        viewed_products = random.sample(product_ids, min(random.randint(1, 8), len(product_ids)))
        event_time = session_start + timedelta(seconds=random.randint(5, 30))

        # ── Search ──
        if random.random() < 0.4:
            query = random.choice(SEARCH_QUERIES)
            cur.execute("""
                INSERT INTO event (session_id, customer_id, event_type, event_timestamp, event_data)
                VALUES (%s, %s, 'search', %s, %s)
            """, (session_id, cust_id, event_time, f'{{"query": "{query}"}}'))
            event_time += timedelta(seconds=random.randint(5, 30))
            total_events += 1

        # ── Product Views ──
        for prod_id in viewed_products:
            cur.execute("""
                INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                VALUES (%s, %s, %s, 'product_view', %s)
            """, (session_id, cust_id, prod_id, event_time))
            event_time += timedelta(seconds=random.randint(10, 120))
            total_events += 1

            # Compare
            if random.random() < 0.15 and len(viewed_products) > 1:
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                    VALUES (%s, %s, %s, 'compare', %s)
                """, (session_id, cust_id, prod_id, event_time))
                event_time += timedelta(seconds=random.randint(10, 60))
                total_events += 1

        # ── Cart ──
        if random.random() < 0.35:
            cart_products = random.sample(viewed_products, min(random.randint(1, 3), len(viewed_products)))

            cur.execute("""
                INSERT INTO cart (customer_id, session_id, created_at)
                VALUES (%s, %s, %s) RETURNING cart_id
            """, (cust_id, session_id, event_time))
            cart_id = cur.fetchone()["cart_id"]
            total_carts += 1

            for cp_id in cart_products:
                # Get product price
                cur.execute("SELECT price FROM product WHERE product_id = %s", (cp_id,))
                price_row = cur.fetchone()
                price = float(price_row["price"]) if price_row else 999.0
                qty = random.randint(1, 3)

                cur.execute("""
                    INSERT INTO cart_item (cart_id, product_id, quantity, unit_price, added_at)
                    VALUES (%s, %s, %s, %s, %s)
                """, (cart_id, cp_id, qty, price, event_time))
                
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                    VALUES (%s, %s, %s, 'add_to_cart', %s)
                """, (session_id, cust_id, cp_id, event_time))
                event_time += timedelta(seconds=random.randint(5, 30))
                total_events += 1

            # ── Remove from cart? ──
            if random.random() < 0.12 and len(cart_products) > 1:
                remove_prod = random.choice(cart_products)
                cur.execute("""
                    UPDATE cart_item SET removed_at = %s 
                    WHERE cart_id = %s AND product_id = %s AND removed_at IS NULL
                """, (event_time, cart_id, remove_prod))
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                    VALUES (%s, %s, %s, 'remove_from_cart', %s)
                """, (session_id, cust_id, remove_prod, event_time))
                event_time += timedelta(seconds=random.randint(5, 20))
                total_events += 1

            # ── Checkout / Purchase ──
            will_purchase = random.random() < 0.30  # 30% of carts convert
            if will_purchase:
                # Checkout start
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, event_type, event_timestamp)
                    VALUES (%s, %s, 'checkout_start', %s)
                """, (session_id, cust_id, event_time))
                event_time += timedelta(seconds=random.randint(30, 180))
                total_events += 1

                # Calculate cart total
                cur.execute("""
                    SELECT COALESCE(SUM(quantity * unit_price), 0) AS total 
                    FROM cart_item WHERE cart_id = %s AND removed_at IS NULL
                """, (cart_id,))
                cart_total = float(cur.fetchone()["total"])
                if cart_total <= 0:
                    cart_total = 999.0

                # Checkout complete
                cur.execute("""
                    INSERT INTO event (session_id, customer_id, event_type, event_timestamp)
                    VALUES (%s, %s, 'checkout_complete', %s)
                """, (session_id, cust_id, event_time))
                total_events += 1

                # Create order
                payment_method = random.choice(PAYMENT_METHODS)
                city, state = random.choice(CITIES)
                discount = round(cart_total * random.uniform(0, 0.15), 2)
                delivery_date = event_time + timedelta(days=random.randint(2, 10))

                cur.execute("""
                    INSERT INTO order_table (customer_id, cart_id, order_date, order_status, total_amount,
                                             discount_amount, payment_method, shipping_address_city, delivery_date)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s) RETURNING order_id
                """, (
                    cust_id, cart_id, event_time,
                    random.choices(["delivered", "shipped", "confirmed"], weights=[70, 20, 10])[0],
                    cart_total - discount, discount, payment_method, city, delivery_date,
                ))
                order_id = cur.fetchone()["order_id"]
                total_orders += 1

                # Order items
                cur.execute("""
                    SELECT product_id, quantity, unit_price FROM cart_item 
                    WHERE cart_id = %s AND removed_at IS NULL
                """, (cart_id,))
                for item in cur.fetchall():
                    subtotal = float(item["quantity"]) * float(item["unit_price"])
                    cur.execute("""
                        INSERT INTO order_item (order_id, product_id, quantity, unit_price, subtotal)
                        VALUES (%s, %s, %s, %s, %s)
                    """, (order_id, item["product_id"], item["quantity"], item["unit_price"], subtotal))

                # Payment
                cur.execute("""
                    INSERT INTO payment (order_id, payment_method, payment_status, amount, payment_date)
                    VALUES (%s, %s, 'completed', %s, %s)
                """, (order_id, payment_method, cart_total - discount, event_time))

                # Purchase events
                for cp_id in cart_products:
                    cur.execute("""
                        INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                        VALUES (%s, %s, %s, 'purchase', %s)
                    """, (session_id, cust_id, cp_id, event_time))
                    total_events += 1

                # Cart converted
                cur.execute("UPDATE cart SET cart_status = 'converted' WHERE cart_id = %s", (cart_id,))

                # ── Review (30% chance after purchase) ──
                if random.random() < 0.30:
                    review_date = event_time + timedelta(days=random.randint(1, 30))
                    review_prod = random.choice(cart_products)
                    rating = random.choices([1, 2, 3, 4, 5], weights=[5, 8, 15, 35, 37])[0]
                    review_texts = {
                        5: ["Excellent product!", "Highly recommended", "Amazing quality", "Love it!"],
                        4: ["Good product", "Value for money", "Happy with purchase", "Nice"],
                        3: ["Average quality", "Okay product", "Could be better", "Decent"],
                        2: ["Below expectations", "Not great", "Disappointing quality"],
                        1: ["Terrible product", "Waste of money", "Very poor quality", "Don't buy"],
                    }
                    text = random.choice(review_texts.get(rating, ["OK"]))
                    sentiment = round((rating - 3) / 2.0, 2)  # Simple mapping: 1→-1, 3→0, 5→1

                    cur.execute("""
                        INSERT INTO review (customer_id, product_id, order_id, rating, review_text, 
                                            sentiment_score, review_date, is_verified)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, TRUE)
                    """, (cust_id, review_prod, order_id, rating, text, sentiment, review_date))
                    
                    cur.execute("""
                        INSERT INTO event (session_id, customer_id, product_id, event_type, event_timestamp)
                        VALUES (%s, %s, %s, 'review', %s)
                    """, (session_id, cust_id, review_prod, review_date))
                    total_events += 1
                    total_reviews += 1

                # ── Return (8% chance) ──
                if random.random() < 0.08:
                    return_date = event_time + timedelta(days=random.randint(3, 30))
                    return_prod = random.choice(cart_products)
                    cur.execute("SELECT unit_price FROM cart_item WHERE cart_id = %s AND product_id = %s LIMIT 1",
                                (cart_id, return_prod))
                    refund_row = cur.fetchone()
                    refund_amt = float(refund_row["unit_price"]) if refund_row else 0

                    cur.execute("""
                        INSERT INTO return_table (order_id, product_id, customer_id, return_reason, 
                                                   return_date, refund_amount, return_status)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (order_id, return_prod, cust_id, random.choice(RETURN_REASONS),
                          return_date, refund_amt,
                          random.choices(["completed", "approved", "requested"], weights=[50, 30, 20])[0]))
                    total_returns += 1

            else:
                # Cart abandoned
                cur.execute("UPDATE cart SET cart_status = 'abandoned' WHERE cart_id = %s", (cart_id,))

    print(f"  Generated: {total_events} events, {total_carts} carts, {total_orders} orders, "
          f"{total_reviews} reviews, {total_returns} returns")


def seed_campaigns(cur, customer_ids):
    """Create sample campaigns and interactions."""
    print(f"  Seeding {NUM_CAMPAIGNS} campaigns...")
    campaign_ids = []
    segments = ["VIP", "Loyal", "New", "At Risk", "Regular", "All"]
    names = [
        "Summer Sale 2025", "New User Welcome", "Festival Bonanza", "Clearance Event",
        "VIP Exclusive", "Flash Sale", "Weekend Offers", "Back to School",
        "Electronics Week", "Fashion Fiesta",
    ]
    for i in range(NUM_CAMPAIGNS):
        start = random_date(120, 10).date()
        cur.execute("""
            INSERT INTO campaign (campaign_name, campaign_type, start_date, end_date, budget, 
                                  target_segment, status)
            VALUES (%s, %s, %s, %s, %s, %s, %s) RETURNING campaign_id
        """, (
            names[i], random.choice(["email", "sms", "push", "social", "display"]),
            start, start + timedelta(days=random.randint(3, 30)),
            round(random.uniform(5000, 100000), 2),
            random.choice(segments),
            random.choices(["completed", "active", "paused"], weights=[50, 40, 10])[0],
        ))
        campaign_ids.append(cur.fetchone()["campaign_id"])

    # Generate interactions
    interaction_count = 0
    for camp_id in campaign_ids:
        num_reached = random.randint(50, 300)
        reached_customers = random.sample(customer_ids, min(num_reached, len(customer_ids)))
        for cust_id in reached_customers:
            # Sent
            cur.execute("""
                INSERT INTO campaign_interaction (campaign_id, customer_id, interaction_type, interaction_date)
                VALUES (%s, %s, 'sent', %s)
            """, (camp_id, cust_id, random_date(60, 5)))
            interaction_count += 1

            # Opened (40%)
            if random.random() < 0.40:
                cur.execute("""
                    INSERT INTO campaign_interaction (campaign_id, customer_id, interaction_type, interaction_date)
                    VALUES (%s, %s, 'opened', %s)
                """, (camp_id, cust_id, random_date(60, 5)))
                interaction_count += 1

                # Clicked (25% of opened)
                if random.random() < 0.25:
                    cur.execute("""
                        INSERT INTO campaign_interaction (campaign_id, customer_id, interaction_type, interaction_date)
                        VALUES (%s, %s, 'clicked', %s)
                    """, (camp_id, cust_id, random_date(60, 5)))
                    interaction_count += 1

                    # Converted (15% of clicked)
                    if random.random() < 0.15:
                        cur.execute("""
                            INSERT INTO campaign_interaction (campaign_id, customer_id, interaction_type, interaction_date)
                            VALUES (%s, %s, 'converted', %s)
                        """, (camp_id, cust_id, random_date(60, 5)))
                        interaction_count += 1

    print(f"  Generated: {interaction_count} campaign interactions")


def run_seed():
    """Main seed function — run once to populate the database."""
    print("=" * 60)
    print("Starting database seed...")
    print("=" * 60)

    with db.transaction() as cur:
        cat_ids = seed_categories(cur)
        customer_ids = seed_customers(cur)
        product_ids = seed_products(cur, cat_ids)
        seed_sessions_and_events(cur, customer_ids, product_ids)
        seed_campaigns(cur, customer_ids)

    # Refresh materialized views
    print("  Refreshing materialized views...")
    try:
        with db.cursor() as cur:
            cur.execute("REFRESH MATERIALIZED VIEW mv_daily_sales")
            cur.execute("REFRESH MATERIALIZED VIEW mv_customer_rfm")
            cur.execute("REFRESH MATERIALIZED VIEW mv_product_performance")
            cur.execute("REFRESH MATERIALIZED VIEW mv_segment_kpis")
    except Exception as e:
        print(f"  Warning: Could not refresh views: {e}")

    # Update customer segments
    print("  Updating customer segments...")
    try:
        with db.cursor() as cur:
            cur.execute("""
                UPDATE customer c
                SET segment = CASE
                    WHEN rfm.r_score >= 4 AND rfm.f_score >= 4 AND rfm.m_score >= 4 THEN 'VIP'
                    WHEN rfm.r_score >= 4 AND rfm.f_score >= 3 THEN 'Loyal'
                    WHEN rfm.r_score >= 3 AND rfm.f_score >= 1 AND rfm.m_score >= 3 THEN 'Potential'
                    WHEN rfm.r_score >= 4 AND rfm.f_score <= 1 THEN 'New'
                    WHEN rfm.r_score <= 2 AND rfm.f_score >= 3 THEN 'At Risk'
                    WHEN rfm.r_score <= 2 AND rfm.f_score <= 2 THEN 'Churned'
                    ELSE 'Regular'
                END,
                lifetime_value = rfm.monetary,
                updated_at = NOW()
                FROM mv_customer_rfm rfm
                WHERE c.customer_id = rfm.customer_id
            """)
    except Exception as e:
        print(f"  Warning: Could not update segments: {e}")

    print("=" * 60)
    print("Database seed completed!")
    print("=" * 60)


if __name__ == "__main__":
    run_seed()
