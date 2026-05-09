from datetime import date, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StudyRecordItem(BaseModel):
    id: int
    room_name: str
    seat_number: str
    date: date
    start_time: time
    end_time: time
    hours: float
    total_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class StudyRecordListResponse(BaseModel):
    items: list[StudyRecordItem]
    total: int
    page: int
    page_size: int


class CalendarMark(BaseModel):
    date: date
    studied: bool

    model_config = ConfigDict(from_attributes=True)


class StudyRecordSummaryResponse(BaseModel):
    monthly_hours: float
    monthly_bookings: int
    max_streak_days: int
    total_hours: float
    calendar_mark: list[CalendarMark]

    model_config = ConfigDict(from_attributes=True)