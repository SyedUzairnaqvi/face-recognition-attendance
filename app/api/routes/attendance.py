from datetime import datetime, timedelta, timezone
from fastapi import APIRouter, Query
from app.db.crud import list_attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


# India Standard Time (UTC+05:30).
IST = timezone(timedelta(hours=5, minutes=30))


@router.get("")
def get_attendance(date_filter: str | None = Query(default=None, alias="date")):
    return {"records": list_attendance(date_filter)}


@router.get("/today")
def get_today_attendance():
    # Use the Indian calendar date instead of the Render server's UTC date.
    today_ist = datetime.now(IST).date()
    return {"date": str(today_ist), "records": list_attendance(str(today_ist))}
