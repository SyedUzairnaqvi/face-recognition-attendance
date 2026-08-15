from datetime import date
from fastapi import APIRouter, Query
from app.db.crud import list_attendance

router = APIRouter(prefix="/attendance", tags=["Attendance"])


@router.get("")
def get_attendance(date_filter: str | None = Query(default=None, alias="date")):
    return {"records": list_attendance(date_filter)}


@router.get("/today")
def get_today_attendance():
    return {"date": str(date.today()), "records": list_attendance(str(date.today()))}
