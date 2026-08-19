import os
from contextlib import contextmanager
from pathlib import Path

from dotenv import load_dotenv

try:
    from mysql.connector import pooling
except ImportError:  # Database features report unavailable instead of breaking API startup.
    pooling = None


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
# The pool is created lazily so a remote deployment without a local
# MySQL server can still boot and expose health/error responses.

connection_pool = None


# ============================================================
# GET / CREATE CONNECTION POOL
# ============================================================

def _get_connection_pool():
    """Create the MySQL connection pool only when it is needed."""
    global connection_pool

    if pooling is None:
        raise RuntimeError(
            "mysql-connector-python is not installed. Install requirements.txt."
        )

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
    Verify MySQL connectivity and initialize the application schema.

    Schema creation is idempotent (CREATE TABLE IF NOT EXISTS), so a fresh
    deployment can boot without requiring a manually prepared schema.
    Existing tables/data are preserved.
    """
    pool = _get_connection_pool()
    conn = pool.get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("SELECT 1")
        cursor.fetchone()

        schema_path = Path(__file__).resolve().parents[2] / "docs" / "schema.sql"
        if not schema_path.exists():
            raise FileNotFoundError(f"Database schema not found: {schema_path}")

        statements = [
            statement.strip()
            for statement in schema_path.read_text(encoding="utf-8").split(";")
            if statement.strip()
        ]
        for statement in statements:
            cursor.execute(statement)
        conn.commit()
        cursor.close()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def database_is_available() -> bool:
    """Return True only when the configured MySQL database is reachable."""
    try:
        init_db()
        return True
    except Exception:
        return False


# ============================================================
# DATABASE CONNECTION
# ============================================================

@contextmanager
def get_connection():
    """
    Provide a connection from the MySQL connection pool.

    Successful operations are committed automatically; failed operations
    are rolled back and re-raised.
    """
    pool = _get_connection_pool()
    conn = pool.get_connection()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()
