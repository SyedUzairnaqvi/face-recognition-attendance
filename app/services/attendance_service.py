from datetime import datetime
from app.db.crud import create_attendance


def mark_attendance(name, distance=None, threshold=None, blur=None, brightness=None):
    now = datetime.now()
    inserted = create_attendance(
        name=name,
        date=now.strftime("%Y-%m-%d"),
        time=now.strftime("%H:%M:%S"),
        distance=distance,
        threshold=threshold,
        blur=blur,
        brightness=brightness,
    )
    return {
        "name": name,
        "date": now.strftime("%Y-%m-%d"),
        "time": now.strftime("%H:%M:%S"),
        "status": "marked" if inserted else "already_marked_today",
    }
