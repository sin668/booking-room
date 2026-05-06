from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class SeatResponse(BaseModel):
    id: int
    room_id: int
    seat_number: str
    zone: str
    position: str | None
    floor: int
    price_per_hour: Decimal
    status: str
    row: int
    col: int

    model_config = ConfigDict(from_attributes=True)


class SeatWithAvailabilityResponse(SeatResponse):
    is_available: bool


class SeatCreate(BaseModel):
    seat_number: str = Field(..., max_length=10)
    zone: str = Field(..., pattern="^(quiet|keyboard|vip)$")
    position: str | None = Field(None, max_length=20)
    floor: int = Field(default=3, ge=1)
    price_per_hour: Decimal = Field(..., ge=0)
    row: int = Field(..., ge=0)
    col: int = Field(..., ge=0)


class SeatBulkZoneConfig(BaseModel):
    zone: str = Field(..., pattern="^(quiet|keyboard|vip)$")
    rows: int = Field(..., ge=1)
    cols: int = Field(..., ge=1)
    prefix: str = Field(..., max_length=5)
    start_number: int = Field(default=1, ge=1)
    price_per_hour: Decimal = Field(..., ge=0)
    floor: int = Field(default=3, ge=1)


class SeatBulkCreate(BaseModel):
    seats: list[SeatBulkZoneConfig] = Field(..., min_length=1)


class SeatUpdate(BaseModel):
    seat_number: str | None = Field(None, max_length=10)
    zone: str | None = Field(None, pattern="^(quiet|keyboard|vip)$")
    position: str | None = Field(None, max_length=20)
    floor: int | None = Field(None, ge=1)
    price_per_hour: Decimal | None = Field(None, ge=0)
    row: int | None = Field(None, ge=0)
    col: int | None = Field(None, ge=0)


class SeatStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(available|maintenance)$")


class SeatAdminResponse(BaseModel):
    id: int
    room_id: int
    seat_number: str
    zone: str
    position: str | None
    floor: int
    price_per_hour: Decimal
    status: str
    row: int
    col: int
    created_at: datetime
    updated_at: datetime
    room_name: str = ""

    model_config = ConfigDict(from_attributes=True)
