from src.database.connection import db
import pandas as pd
import numpy as np

tables = ['customer', 'category', 'product', 'session', 'event', 'cart', 'cart_item', 'order_table', 'order_item', 'review', 'payment', 'return_table', 'campaign', 'campaign_interaction']
print("=== DATABASE TABLE ROW COUNTS ===")
for t in tables:
    try:
        res = db.execute_query(f"SELECT count(*) as c FROM {t}")
        print(f"{t:25s}: {res[0]['c']} rows")
    except Exception as e:
        print(f"{t:25s}: Error - {e}")
