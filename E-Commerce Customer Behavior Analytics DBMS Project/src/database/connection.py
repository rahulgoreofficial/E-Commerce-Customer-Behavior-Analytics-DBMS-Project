"""
Database connection manager using psycopg2.
Provides a centralized connection pool for the application.
"""
import psycopg2
import psycopg2.extras
from contextlib import contextmanager
from src.config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD


class DatabaseManager:
    """Manages PostgreSQL connections for the application."""

    def __init__(self):
        self._conn = None

    def connect(self):
        """Establish database connection."""
        if self._conn is None or self._conn.closed:
            self._conn = psycopg2.connect(
                host=DB_HOST,
                port=DB_PORT,
                dbname=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD,
            )
            self._conn.autocommit = False
        return self._conn

    def close(self):
        """Close the database connection."""
        if self._conn and not self._conn.closed:
            self._conn.close()
            self._conn = None

    @contextmanager
    def cursor(self, dict_cursor=True):
        """Context manager for database cursor.
        
        Usage:
            with db.cursor() as cur:
                cur.execute("SELECT * FROM customer LIMIT 5")
                rows = cur.fetchall()
        """
        conn = self.connect()
        factory = psycopg2.extras.RealDictCursor if dict_cursor else None
        cur = conn.cursor(cursor_factory=factory)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    @contextmanager
    def transaction(self):
        """Context manager for explicit ACID transactions.
        
        Usage:
            with db.transaction() as cur:
                cur.execute("INSERT INTO ...")
                cur.execute("UPDATE ...")
                # auto-commits on exit, rolls back on exception
        """
        conn = self.connect()
        cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        try:
            yield cur
            conn.commit()
        except Exception:
            conn.rollback()
            raise
        finally:
            cur.close()

    def execute_query(self, query, params=None):
        """Execute a SELECT query and return results as list of dicts."""
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.fetchall()

    def execute_scalar(self, query, params=None):
        """Execute a query and return the first column of the first row."""
        with self.cursor(dict_cursor=False) as cur:
            cur.execute(query, params)
            row = cur.fetchone()
            return row[0] if row else None

    def execute_update(self, query, params=None):
        """Execute an INSERT/UPDATE/DELETE and return row count."""
        with self.cursor() as cur:
            cur.execute(query, params)
            return cur.rowcount

    def call_procedure(self, proc_name):
        """Call a stored procedure."""
        with self.cursor() as cur:
            cur.execute(f"CALL {proc_name}()")

    def test_connection(self):
        """Test if the database connection works."""
        try:
            result = self.execute_scalar("SELECT 1")
            return result == 1
        except Exception as e:
            return False


# Global singleton
db = DatabaseManager()
