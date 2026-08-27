from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel


class FollowedRoomResponse(BaseModel):
    id: int
    name: str
    description: str | None = None
    cover_image: str | None = None
    address: str
    city_id: int | None = None
    city_name: str | None = None
    business_hours: str | None = None
    status: str
    min_price: Decimal
    room_type: str | None = None
    followed_at: datetime


class FollowedRoomListResponse(BaseModel):
    items: list[FollowedRoomResponse]
    total: int
