from datetime import datetime, timedelta, timezone
from app.db.crud import create_attendance


# India Standard Time (UTC+05:30).
# Use a fixed offset so attendance timestamps do not depend on the server's timezone.
IST = timezone(timedelta(hours=5, minutes=30))


def mark_attendance(name, distance=None, threshold=None, blur=None, brightness=None):
    # Always record attendance using Indian Standard Time.
    now = datetime.now(IST)

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
