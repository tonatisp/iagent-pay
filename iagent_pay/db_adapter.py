import os
import re
import threading

# Global variables for connection pooling
_pg_pools = {}
_pool_lock = threading.Lock()

class DBAdapter:
    """
    A unified Database Adapter that translates standard sqlite3 connections
    into psycopg2 (PostgreSQL) connections transparently when DATABASE_URL is set.
    """
    def __init__(self, db_path):
        self.db_path = db_path
        self.db_url = os.environ.get("DATABASE_URL")
        self.is_postgres = bool(self.db_url and (self.db_url.startswith("postgres://") or self.db_url.startswith("postgresql://")))
        self._local = threading.local()

    def connect(self):
        if self.is_postgres:
            return self._connect_postgres()
        else:
            return self._connect_sqlite()

    def _connect_sqlite(self):
        import sqlite3
        import time
        import os
        
        try:
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            # Execute a test pragma command to verify database integrity
            conn.execute("PRAGMA journal_mode=WAL;")
            return conn
        except sqlite3.DatabaseError as e:
            try:
                conn.close()
            except Exception:
                pass
            
            # File is corrupted, rename it
            corrupt_suffix = f".corrupt_{int(time.time())}"
            corrupt_path = self.db_path + corrupt_suffix
            try:
                if os.path.exists(self.db_path):
                    os.rename(self.db_path, corrupt_path)
            except Exception as rename_err:
                print(f"⚠️ [iAgent-Pay DB recovery] Failed to rename corrupt database: {rename_err}")
                
            # Create a fresh database connection
            conn = sqlite3.connect(self.db_path, timeout=30.0)
            conn.row_factory = sqlite3.Row
            try:
                conn.execute("PRAGMA journal_mode=WAL;")
            except Exception:
                pass
                
            # Recreate schema dynamically based on the DB file name
            db_name = os.path.basename(self.db_path)
            c = conn.cursor()
            
            if "reputation" in db_name:
                c.execute("""
                    CREATE TABLE IF NOT EXISTS peer_ratings (
                        address       TEXT PRIMARY KEY,
                        score         REAL NOT NULL DEFAULT 3.0,
                        reviews_count INTEGER NOT NULL DEFAULT 0,
                        last_updated  REAL NOT NULL,
                        checksum      TEXT
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS rating_log (
                        id          INTEGER PRIMARY KEY AUTOINCREMENT,
                        address     TEXT NOT NULL,
                        score       REAL NOT NULL,
                        rated_at    REAL NOT NULL,
                        agent_addr  TEXT
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS custom_licenses (
                        address       TEXT PRIMARY KEY,
                        grace_days    INTEGER NOT NULL DEFAULT 730,
                        fee_rate      REAL NOT NULL DEFAULT 0.001,
                        last_updated  REAL NOT NULL
                    )
                """)
            elif "marketplace" in db_name:
                c.execute("""
                    CREATE TABLE IF NOT EXISTS bounties (
                        id TEXT PRIMARY KEY,
                        title TEXT,
                        reward_usd REAL,
                        status TEXT,
                        created_at REAL
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS escrow_contracts (
                        id TEXT PRIMARY KEY,
                        recipient TEXT,
                        amount_usd REAL,
                        status TEXT,
                        task_description TEXT,
                        created_at REAL,
                        resolved_at REAL
                    )
                """)
            elif "receipt" in db_name:
                c.execute("""
                    CREATE TABLE IF NOT EXISTS used_receipts (
                        receipt     TEXT PRIMARY KEY,
                        path        TEXT,
                        amount_usdc REAL,
                        used_at     REAL NOT NULL,
                        expires_at  REAL NOT NULL
                    )
                """)
                c.execute("""
                    CREATE INDEX IF NOT EXISTS idx_expires ON used_receipts(expires_at)
                """)
            else:
                # Default to history db schema (transactions, paid_invoices)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS transactions (
                        timestamp REAL,
                        tx_hash TEXT,
                        recipient TEXT,
                        amount REAL,
                        status TEXT,
                        symbol TEXT,
                        fee_paid INTEGER DEFAULT 0
                    )
                """)
                c.execute("""
                    CREATE TABLE IF NOT EXISTS paid_invoices (
                        invoice_id TEXT PRIMARY KEY,
                        timestamp REAL,
                        recipient TEXT,
                        amount REAL
                    )
                """)
                
            conn.commit()
            return conn

    def _connect_postgres(self):
        import psycopg2
        import psycopg2.extras
        from psycopg2 import pool
        
        # Replace postgres:// with postgresql:// for SQLAlchemy/psycopg2 compatibility just in case
        url = self.db_url
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
            
        with _pool_lock:
            if url not in _pg_pools:
                # Limit to 25 connections max to prevent Postgres connection exhaustion
                _pg_pools[url] = pool.ThreadedConnectionPool(1, 25, url)
                
        pg_pool = _pg_pools[url]
        
        # Retry logic for getting a connection from the pool gracefully
        import time
        max_retries = 50
        conn = None
        for attempt in range(max_retries):
            try:
                conn = pg_pool.getconn()
                break
            except pool.PoolError:
                if attempt < max_retries - 1:
                    time.sleep(0.1) # Wait 100ms before retrying
                else:
                    raise Exception("Database connection pool exhausted. Please increase pool size or try again later.")
                    
        conn.autocommit = False
        return PostgresWrapper(conn, pg_pool)

class PostgresWrapper:
    """Wraps psycopg2 to look and behave like sqlite3 for this project."""
    def __init__(self, pg_conn, pool=None):
        self.conn = pg_conn
        self.pool = pool

    def _translate_sql(self, sql):
        """Translates sqlite ? parameters to psycopg2 %s parameters."""
        return sql.replace("?", "%s")

    def cursor(self):
        """Return self to act as both a Connection and a Cursor."""
        return self

    def execute(self, sql, parameters=None):
        import psycopg2.extras
        sql = self._translate_sql(sql)
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        if parameters is not None:
            cur.execute(sql, parameters)
        else:
            cur.execute(sql)
        self._last_cur = cur
        return self

    def executemany(self, sql, seq_of_parameters):
        import psycopg2.extras
        sql = self._translate_sql(sql)
        cur = self.conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.executemany(sql, seq_of_parameters)
        self._last_cur = cur
        return self

    def fetchone(self):
        return self._last_cur.fetchone()

    def fetchall(self):
        return self._last_cur.fetchall()

    @property
    def rowcount(self):
        return self._last_cur.rowcount

    def commit(self):
        self.conn.commit()

    def close(self):
        if self.pool:
            self.pool.putconn(self.conn)
        else:
            self.conn.close()

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is None:
            self.commit()
        else:
            self.conn.rollback()
        self.close()
