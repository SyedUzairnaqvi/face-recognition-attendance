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
    """
    Mark attendance for a recognized person.

    The database layer handles:
    - Person creation
    - Duplicate attendance prevention
    - MySQL insertion
    """

    # Get current time in India Standard Time
    now = datetime.now(IST)

    # --------------------------------------------------------
    # Save attendance in MySQL
    # --------------------------------------------------------

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

    # --------------------------------------------------------
    # Return existing API response format
    # --------------------------------------------------------

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