from datetime import (
    datetime,
    timedelta,
    timezone,
)

from app.db.crud import create_attendance


# ============================================================
# INDIA STANDARD TIME
# ============================================================

IST = timezone(
    timedelta(hours=5, minutes=30)
)


# ============================================================
# MARK ATTENDANCE
# ============================================================

def mark_attendance(
    name,
    distance=None,
    threshold=None,
    blur=None,
    brightness=None,
    method="Face Recognition",
):

    now = datetime.now(IST)


    inserted = create_attendance(
        name=name,

        date=now.strftime(
            "%Y-%m-%d"
        ),

        time=now.strftime(
            "%H:%M:%S"
        ),

        distance=distance,

        threshold=threshold,

        blur=blur,

        brightness=brightness,

        method=method,
    )


    return {

        "name": name,

        "date": now.strftime(
            "%Y-%m-%d"
        ),

        "time": now.strftime(
            "%H:%M:%S"
        ),

        "status": (
            "marked"
            if inserted
            else "already_marked_today"
        ),

        "method": method,
    }