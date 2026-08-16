import sqlite3

from contextlib import contextmanager

from app.core.config import DB_PATH


def init_db():

    with sqlite3.connect(DB_PATH) as conn:

        conn.execute("""
        CREATE TABLE IF NOT EXISTS attendance (

            id INTEGER PRIMARY KEY AUTOINCREMENT,

            name TEXT NOT NULL,

            date TEXT NOT NULL,

            time TEXT NOT NULL,

            match_distance REAL,

            match_threshold REAL,

            quality_blur REAL,

            quality_brightness REAL,

            method TEXT NOT NULL
                DEFAULT 'Face Recognition',

            created_at TEXT NOT NULL
                DEFAULT CURRENT_TIMESTAMP,

            UNIQUE(name, date)

        )
        """)


        # ====================================================
        # MIGRATION
        # ====================================================

        columns = conn.execute(
            "PRAGMA table_info(attendance)"
        ).fetchall()


        column_names = {
            column[1]
            for column in columns
        }


        if "method" not in column_names:

            conn.execute("""
                ALTER TABLE attendance
                ADD COLUMN method TEXT
                NOT NULL
                DEFAULT 'Face Recognition'
            """)


        conn.commit()


@contextmanager
def get_connection():

    conn = sqlite3.connect(
        DB_PATH
    )

    conn.row_factory = sqlite3.Row

    try:

        yield conn

        conn.commit()

    finally:

        conn.close()