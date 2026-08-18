from fastapi import APIRouter

from app.db.database import get_connection


router = APIRouter(prefix="/analytics", tags=["Analytics"])


def _fetch_all(cursor, query):
    cursor.execute(query)
    return cursor.fetchall()


@router.get("/dashboard")
def get_dashboard_analytics():
    """Return the datasets used by the web analytics dashboard."""

    with get_connection() as conn:
        cursor = conn.cursor(dictionary=True)

        daily_attendance = _fetch_all(
            cursor,
            """
            SELECT attendance_date,
                   COUNT(DISTINCT person_id) AS people_present,
                   COUNT(*) AS attendance_records,
                   COUNT(DISTINCT method) AS methods_used
            FROM attendance
            GROUP BY attendance_date
            ORDER BY attendance_date ASC
            """,
        )

        person_attendance = _fetch_all(
            cursor,
            """
            SELECT p.person_id, p.name, p.is_active,
                   COUNT(DISTINCT a.attendance_date) AS attendance_days,
                   MAX(a.attendance_date) AS last_attendance_date,
                   MAX(a.attendance_time) AS last_attendance_time
            FROM persons p
            LEFT JOIN attendance a ON a.person_id = p.person_id
            GROUP BY p.person_id, p.name, p.is_active
            ORDER BY attendance_days DESC, p.name
            """,
        )

        recognition_performance = _fetch_all(
            cursor,
            """
            SELECT COUNT(*) AS total_events,
                   SUM(CASE WHEN result = 'matched' THEN 1 ELSE 0 END) AS matched_events,
                   SUM(CASE WHEN result = 'unknown' THEN 1 ELSE 0 END) AS unknown_events,
                   ROUND(100.0 * SUM(CASE WHEN result = 'matched' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS recognition_rate,
                   ROUND(AVG(distance), 4) AS avg_distance,
                   ROUND(AVG(CASE WHEN result = 'matched' THEN distance END), 4) AS avg_matched_distance
            FROM recognition_events
            """,
        )

        recognition_by_source = _fetch_all(
            cursor,
            """
            SELECT source,
                   COUNT(*) AS total_events,
                   SUM(CASE WHEN result = 'matched' THEN 1 ELSE 0 END) AS matched_events,
                   SUM(CASE WHEN result = 'unknown' THEN 1 ELSE 0 END) AS unknown_events,
                   ROUND(100.0 * SUM(CASE WHEN result = 'matched' THEN 1 ELSE 0 END) / NULLIF(COUNT(*), 0), 2) AS recognition_rate,
                   ROUND(AVG(distance), 4) AS avg_distance
            FROM recognition_events
            GROUP BY source
            ORDER BY total_events DESC
            """,
        )

        video_analytics = _fetch_all(
            cursor,
            """
            SELECT video_id, filename, duration_seconds, frames_sampled,
                   faces_detected, recognized_faces, unknown_faces,
                   processing_status, processed_at,
                   ROUND(100.0 * recognized_faces / NULLIF(faces_detected, 0), 2) AS recognition_rate
            FROM video_sessions
            ORDER BY processed_at DESC
            """,
        )

        cursor.close()

    return {
        "daily_attendance": daily_attendance,
        "person_attendance": person_attendance,
        "recognition_performance": recognition_performance,
        "recognition_by_source": recognition_by_source,
        "video_analytics": video_analytics,
    }
