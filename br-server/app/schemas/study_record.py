from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class CalendarMark(BaseModel):
    date: date
    studied: bool = False
    upcoming: bool = False

    model_config = ConfigDict(from_attributes=True)


class StudyRecordSummaryResponse(BaseModel):
    monthly_hours: float
    monthly_bookings: int
    max_streak_days: int
    total_hours: float
    calendar_mark: list[CalendarMark]
    monthly_upcoming_hours: float = 0.0
    monthly_upcoming_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class StudyRecordItem(BaseModel):
    id: int
    record_type: str = "seat"  # "seat" | "course"
    status: str = "completed"  # "completed" | "upcoming"
    room_name: str | None = None
    seat_number: str | None = None
    course_name: str | None = None
    lesson_title: str | None = None
    date: date
    start_time: time
    end_time: time
    hours: float
    total_price: Decimal = Decimal("0")

    model_config = ConfigDict(from_attributes=True)


class StudyRecordListResponse(BaseModel):
    items: list[StudyRecordItem]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)
