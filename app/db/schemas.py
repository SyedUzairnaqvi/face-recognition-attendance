from pydantic import BaseModel, Field
from typing import Optional


class RecognitionResult(BaseModel):
    name: str
    matched: bool
    distance: Optional[float] = None
    threshold: Optional[float] = None
    match_score: Optional[float] = Field(default=None, description="Threshold-relative score; not a calibrated probability.")


class AttendanceRecord(BaseModel):
    name: str
    date: str
    time: str
    match_distance: Optional[float] = None
    match_threshold: Optional[float] = None
    quality_blur: Optional[float] = None
    quality_brightness: Optional[float] = None
