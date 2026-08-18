import os
from contextlib import contextmanager

from dotenv import load_dotenv
import mysql.connector
from mysql.connector import pooling


# ============================================================
# LOAD ENVIRONMENT VARIABLES
# ============================================================
# Loads MYSQL_HOST, MYSQL_PORT, MYSQL_DATABASE,
# MYSQL_USER and MYSQL_PASSWORD from the local .env file.

load_dotenv()


# ============================================================
# MYSQL CONFIGURATION
# ============================================================

MYSQL_CONFIG = {
    "host": os.getenv("MYSQL_HOST", "127.0.0.1"),
    "port": int(os.getenv("MYSQL_PORT", "3306")),
    "database": os.getenv("MYSQL_DATABASE", "secure_vision"),
    "user": os.getenv("MYSQL_USER", "secure_vision_app"),
    "password": os.getenv("MYSQL_PASSWORD", ""),
}


# ============================================================
# CONNECTION POOL
# ============================================================
# IMPORTANT:
# The pool is created lazily.
#
# Previously the pool was created immediately when this module
# was imported. On Render, that caused the entire FastAPI
# application to fail because Render does not have MySQL running
# at 127.0.0.1:3306.
#
# Lazy creation keeps the application bootable when MySQL is
# unavailable while preserving normal local MySQL behavior.

connection_pool = None


# ============================================================
# GET / CREATE CONNECTION POOL
# ============================================================

def _get_connection_pool():
    """
    Create the MySQL connection pool only when it is needed.

    Returns:
        MySQLConnectionPool
    """

    global connection_pool

    if connection_pool is None:

        connection_pool = pooling.MySQLConnectionPool(
            pool_name="secure_vision_pool",
            pool_size=5,
            pool_reset_session=True,
            **MYSQL_CONFIG,
        )

    return connection_pool


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Verify that the MySQL database is reachable.

    The connection pool is created here when the application
    explicitly performs a database startup check.

    If MySQL is unavailable, the caller can catch the exception
    and allow the API to continue running.
    """

    pool = _get_connection_pool()

    conn = pool.get_connection()

    try:

        cursor = conn.cursor()

        # Simple connectivity test
        cursor.execute("SELECT 1")

        cursor.fetchone()

        cursor.close()

    finally:

        conn.close()


# ============================================================
# DATABASE CONNECTION
# ============================================================

@contextmanager
def get_connection():
    """
    Provide a connection from the MySQL connection pool.

    The pool is created only when a database operation actually
    needs it.

    Successful operations are committed automatically.
    Failed operations are rolled back automatically.
    """

    pool = _get_connection_pool()

    conn = pool.get_connection()

    try:

        yield conn

        # Commit successful database operations
        conn.commit()

    except Exception:

        # Roll back failed operations
        conn.rollback()

        raise

    finally:

        # Return the connection to the pool
        conn.close()