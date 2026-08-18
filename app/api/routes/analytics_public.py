from datetime import date

from fastapi import APIRouter, HTTPException

from app.db.database import get_connection


router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard():
    """Return live analytics from the configured MySQL database.

    The endpoint fails explicitly when MySQL is unavailable. Returning
    fabricated zero-valued analytics would make a dashboard look healthy
    while hiding a database/configuration failure.
    """

    today = date.today().isoformat()

    try:
        with get_connection() as conn:
            cursor = conn.cursor(dictionary=True)

            # --------------------------------------------------------
            # KPI: active registered people
            # --------------------------------------------------------
            cursor.execute(
                """
                SELECT COUNT(*) AS total
                FROM persons
                WHERE is_active = 1
                """
            )
            registered_people = int(cursor.fetchone()["total"] or 0)

            # --------------------------------------------------------
            # KPI: total attendance records
            # --------------------------------------------------------
            cursor.execute("SELECT COUNT(*) AS total FROM attendance")
            attendance_records = int(cursor.fetchone()["total"] or 0)

            # --------------------------------------------------------
            # KPI: total recognition events
            # --------------------------------------------------------
            cursor.execute(
                "SELECT COUNT(*) AS total FROM recognition_events"
            )
            recognition_events = int(cursor.fetchone()["total"] or 0)

            # --------------------------------------------------------
            # KPI: recognition match rate
            # --------------------------------------------------------
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total,
                    SUM(CASE WHEN result = 'matched' THEN 1 ELSE 0 END) AS matched
                FROM recognition_events
                """
            )
            recognition_summary = cursor.fetchone()
            total_events = int(recognition_summary["total"] or 0)
            matched_events = int(recognition_summary["matched"] or 0)

            recognition_rate = (
                round((matched_events / total_events) * 100, 2)
                if total_events
                else 0.0
            )

            # --------------------------------------------------------
            # Chart: daily attendance
            # --------------------------------------------------------
            cursor.execute(
                """
                SELECT
                    attendance_date AS date,
                    COUNT(*) AS attendance_records,
                    COUNT(DISTINCT person_id) AS people_present
                FROM attendance
                GROUP BY attendance_date
                ORDER BY attendance_date
                """
            )
            daily_attendance = cursor.fetchall()

            # --------------------------------------------------------
            # Chart: recognition by source
            # --------------------------------------------------------
            cursor.execute(
                """
                SELECT
                    source,
                    COUNT(*) AS total_events,
                    SUM(CASE WHEN result = 'matched' THEN 1 ELSE 0 END)
                        AS matched_events,
                    SUM(CASE WHEN result = 'unknown' THEN 1 ELSE 0 END)
                        AS unknown_events
                FROM recognition_events
                GROUP BY source
                ORDER BY total_events DESC
                """
            )
            recognition_by_source = cursor.fetchall()

            # --------------------------------------------------------
            # Table: attendance by person
            # --------------------------------------------------------
            cursor.execute(
                """
                SELECT
                    p.name,
                    COUNT(a.attendance_id) AS attendance_count,
                    MAX(a.attendance_date) AS last_attendance
                FROM persons p
                LEFT JOIN attendance a
                    ON a.person_id = p.person_id
                WHERE p.is_active = 1
                GROUP BY p.person_id, p.name
                ORDER BY attendance_count DESC, p.name
                """
            )
            person_attendance = cursor.fetchall()

            # --------------------------------------------------------
            # Video KPI summary
            # --------------------------------------------------------
            cursor.execute(
                """
                SELECT
                    COUNT(*) AS total_videos,
                    COALESCE(SUM(faces_detected), 0) AS total_faces_detected,
                    COALESCE(SUM(recognized_faces), 0) AS total_recognized_faces,
                    COALESCE(SUM(unknown_faces), 0) AS total_unknown_faces
                FROM video_sessions
                """
            )
            video_summary = cursor.fetchone()

            cursor.close()

        return {
            "status": "ok",
            "source": "mysql",
            "database_connected": True,
            "message": "Analytics loaded from secure_vision MySQL.",
            "date": today,
            "registered_people": registered_people,
            "attendance_records": attendance_records,
            "recognition_events": recognition_events,
            "recognition_rate": recognition_rate,
            "daily_attendance": daily_attendance,
            "recognition_by_source": recognition_by_source,
            "person_attendance": person_attendance,
            "video_analytics": video_summary,
        }

    except Exception as exc:
        # Do not expose database credentials, connection strings, or secrets.
        print(
            "Analytics database unavailable: "
            f"{type(exc).__name__}: {exc}"
        )

        raise HTTPException(
            status_code=503,
            detail="Analytics database is unavailable.",
        ) from exc
