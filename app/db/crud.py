from app.db.database import get_connection


def attendance_exists(name: str, date: str) -> bool:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT 1 FROM attendance WHERE name = ? AND date = ? LIMIT 1",
            (name, date),
        ).fetchone()
        return row is not None


def create_attendance(name, date, time, distance=None, threshold=None, blur=None, brightness=None):
    with get_connection() as conn:
        cur = conn.execute(
            """INSERT OR IGNORE INTO attendance
               (name, date, time, match_distance, match_threshold, quality_blur, quality_brightness)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            (name, date, time, distance, threshold, blur, brightness),
        )
        return cur.rowcount == 1


def list_attendance(date=None, limit=100):
    with get_connection() as conn:
        if date:
            rows = conn.execute(
                "SELECT * FROM attendance WHERE date = ? ORDER BY time DESC LIMIT ?",
                (date, limit),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM attendance ORDER BY date DESC, time DESC LIMIT ?",
                (limit,),
            ).fetchall()
        return [dict(r) for r in rows]
