from datetime import date, datetime, time
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class BookingVerificationBookingSummary(BaseModel):
    id: int
    user_id: str
    user_nickname: str
    user_phone: str
    room_id: int
    room_name: str
    room_address: str
    seat_id: int
    seat_number: str
    seat_zone: str
    seat_position: str | None
    date: date
    start_time: time
    end_time: time
    total_price: Decimal
    status: str
    can_verify: bool

    model_config = ConfigDict(from_attributes=True)


class BookingVerificationTokenResponse(BaseModel):
    token: str
    expires_at: datetime
    verify_url: str
    booking: BookingVerificationBookingSummary

    model_config = ConfigDict(from_attributes=True)


class BookingVerificationDetailResponse(BaseModel):
    booking: BookingVerificationBookingSummary

    model_config = ConfigDict(from_attributes=True)


class BookingVerificationConfirmResponse(BaseModel):
    booking: BookingVerificationBookingSummary

    model_config = ConfigDict(from_attributes=True)
