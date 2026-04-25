"""
PostgreSQL Connection Pool Manager
Handles database connections efficiently for 20,000+ users
"""

import os
import streamlit as st
from psycopg2 import pool, sql, extensions
from psycopg2.extras import RealDictCursor
from contextlib import contextmanager
from loguru import logger
from dotenv import load_dotenv

load_dotenv()


class PostgreSQLManager:
    """Manages PostgreSQL connection pool"""

    def __init__(self):
        self.min_connections = 5
        self.max_connections = int(os.getenv('DATABASE_POOL_SIZE', 20))
        self.connection_pool = None
        self._initialize_pool()

    def _initialize_pool(self):
        """Initialize connection pool"""
        try:
            self.connection_pool = pool.SimpleConnectionPool(
                self.min_connections,
                self.max_connections,
                dsn=os.getenv('DATABASE_URL'),
                sslmode='require',  # Required for Supabase
                cursor_factory=RealDictCursor
            )
            logger.info(
                f"✅ Database connection pool initialized: {self.min_connections}-{self.max_connections} connections")
        except Exception as e:
            logger.error(f"❌ Failed to initialize connection pool: {e}")
            raise

    @contextmanager
    def get_connection(self):
        """Get connection from pool (auto-returns on context exit)"""
        conn = None
        try:
            conn = self.connection_pool.getconn()
            yield conn
        except Exception as e:
            logger.error(f"Database error: {e}")
            raise
        finally:
            if conn:
                self.connection_pool.putconn(conn)

    @contextmanager
    def get_cursor(self, commit=False):
        """Get cursor for database operations"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            try:
                yield cursor
                if commit:
                    conn.commit()
            except Exception as e:
                conn.rollback()
                logger.error(f"Transaction error: {e}")
                raise
            finally:
                cursor.close()

    def execute_query(self, query, params=None, fetch_one=False, fetch_all=False):
        """Execute query and return results"""
        with self.get_cursor(commit=not (fetch_one or fetch_all)) as cursor:
            cursor.execute(query, params or ())
            if fetch_one:
                return cursor.fetchone()
            elif fetch_all:
                return cursor.fetchall()
            return None

    def close_all_connections(self):
        """Close all connections in the pool"""
        if self.connection_pool:
            self.connection_pool.closeall()
            logger.info("All database connections closed")

# Singleton instance


@st.cache_resource
def get_db_manager():
    """Create single instance of database manager (cached by Streamlit)"""
    return PostgreSQLManager()


# Global database manager
db_manager = get_db_manager()
