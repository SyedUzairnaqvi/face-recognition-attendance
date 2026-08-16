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
# Keeps a small pool of reusable MySQL connections.
# This is better than opening a new connection for every
# attendance request.

connection_pool = pooling.MySQLConnectionPool(
    pool_name="secure_vision_pool",
    pool_size=5,
    pool_reset_session=True,
    **MYSQL_CONFIG,
)


# ============================================================
# DATABASE INITIALIZATION
# ============================================================

def init_db():
    """
    Verify that the MySQL database is reachable.

    Tables are managed separately inside the secure_vision
    MySQL database.
    """

    conn = connection_pool.get_connection()

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

    Successful operations are committed automatically.
    Failed operations are rolled back automatically.
    """

    conn = connection_pool.get_connection()

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