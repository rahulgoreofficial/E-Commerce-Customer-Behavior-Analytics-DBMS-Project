"""
Setup Script — Creates the PostgreSQL database and seeds it with data.
Run this once before starting the application.
"""
import os
import sys

# Ensure UTF-8 output if supported
if hasattr(sys.stdout, 'reconfigure'):
    try:
        sys.stdout.reconfigure(encoding='utf-8')
    except Exception:
        pass

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.database.connection import db
from src.config import DB_NAME, DB_PORT, DB_USER


def run_sql_file(filepath):
    """Execute a SQL file against the database."""
    with open(filepath, 'r', encoding='utf-8') as f:
        sql = f.read()
    
    with db.cursor(dict_cursor=False) as cur:
        cur.execute(sql)
    print(f"  [+] Executed: {os.path.basename(filepath)}")


def main():
    print("=" * 60)
    print("  E-Commerce Analytics — Database Setup")
    print("=" * 60)

    # Test connection
    print("\n1. Testing database connection...")
    if not db.test_connection():
        print("  [-] Cannot connect to PostgreSQL!")
        print(f"     Database: {DB_NAME}, Port: {DB_PORT}, User: {DB_USER}")
        print(f"     Make sure PostgreSQL is running and the database exists.")
        print(f"\n     To create the database:")
        print(f'     > psql -U postgres -c "CREATE DATABASE {DB_NAME};"')
        sys.exit(1)
    print("  [+] Connected to PostgreSQL successfully")

    # Run DDL scripts
    sql_dir = os.path.join(os.path.dirname(__file__), "database")
    sql_files = [
        "01_create_tables.sql",
        "02_views.sql",
        "03_procedures_triggers.sql",
        "05_security.sql",
    ]

    print("\n2. Creating database schema (tables, views, triggers, security)...")
    for sql_file in sql_files:
        filepath = os.path.join(sql_dir, sql_file)
        if os.path.exists(filepath):
            try:
                run_sql_file(filepath)
            except Exception as e:
                print(f"  [!] Note in {sql_file}: {e}")

    # Seed data
    print("\n3. Seeding data (500 customers, 150 products, 3000 sessions)...")
    try:
        from src.database.seed_data import run_seed
        run_seed()
    except Exception as e:
        print(f"  [-] Seed error: {e}")
        import traceback
        traceback.print_exc()

    print("\n" + "=" * 60)
    print("  Setup Complete!")
    print("=" * 60)
    print("\n  Next steps:")
    print("    1. Run the application: python main.py")
    print("    2. Dashboard will load with seeded data")
    print("    3. Use the Simulator page to generate live events")
    print("    4. Use the Predictions page to train ML models")
    print("    5. Use the Problems page to detect business issues")


if __name__ == "__main__":
    main()
