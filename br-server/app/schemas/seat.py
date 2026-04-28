from decimal import Decimal

from pydantic import BaseModel, ConfigDict


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
