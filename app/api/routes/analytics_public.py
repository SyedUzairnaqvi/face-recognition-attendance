from datetime import date

from fastapi import APIRouter

router = APIRouter(prefix="/analytics", tags=["Analytics"])


@router.get("/dashboard")
def dashboard():
    """Return a public analytics payload without opening the local MySQL database.

    This endpoint is intentionally independent from the database so the public
    Render frontend can load safely even when MySQL remains local.
    """
    return {
        "status": "ok",
        "source": "live_attendance_api",
        "database_connected": False,
        "message": "Public analytics endpoint is available. Detailed database analytics remain local.",
        "date": date.today().isoformat(),
        "registered_people": 0,
        "attendance_records": 0,
        "recognition_events": 0,
        "recognition_rate": 0.0,
        "daily_attendance": [],
        "recognition_by_source": [],
        "person_attendance": [],
        "video_analytics": [],
    }
