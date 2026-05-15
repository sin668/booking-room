from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class StudyRoomResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cover_image: str | None
    address: str
    city_id: int | None = None
    city_name: str | None = None
    business_hours: str | None
    status: str
    min_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class StudyRoomListResponse(BaseModel):
    items: list[StudyRoomResponse]
    total: int
    page: int
    page_size: int


class RoomCreate(BaseModel):
    name: str = Field(..., max_length=100)
    address: str = Field(..., max_length=255)
    description: str | None = Field(None, max_length=1000)
    cover_image: str | None = Field(None, max_length=512)
    business_hours: str | None = Field(None, max_length=50)
    min_price: Decimal = Field(default=Decimal("0"), ge=0)


class RoomUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    cover_image: str | None = Field(None, max_length=512)
    business_hours: str | None = Field(None, max_length=50)
    min_price: Decimal | None = Field(None, ge=0)


class RoomStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|closed)$")


class RoomAdminResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cover_image: str | None
    address: str
    business_hours: str | None
    status: str
    min_price: Decimal
    created_at: datetime
    updated_at: datetime
    seat_count: int = 0
    available_seat_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class RoomAdminListResponse(BaseModel):
    items: list[RoomAdminResponse]
    total: int
    page: int
    page_size: int
