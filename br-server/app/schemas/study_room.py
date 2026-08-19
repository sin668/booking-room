from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class StudyRoomResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cover_image: str | None
    environment_images: list[str] | None = None
    address: str
    city_id: int | None = None
    city_name: str | None = None
    business_hours: str | None
    status: str
    room_type: str
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
    environment_images: list[str] = Field(default_factory=list, max_length=5)
    business_hours: str | None = Field(None, max_length=50)
    city_id: int | None = None
    room_type: str = Field("study", pattern="^(study|training|comprehensive)$")
    min_price: Decimal = Field(default=Decimal("0"), ge=0)
    status: str = Field("open", pattern="^(open|closed)$")


class RoomUpdate(BaseModel):
    name: str | None = Field(None, max_length=100)
    address: str | None = Field(None, max_length=255)
    description: str | None = Field(None, max_length=1000)
    cover_image: str | None = Field(None, max_length=512)
    environment_images: list[str] | None = Field(None, max_length=5)
    business_hours: str | None = Field(None, max_length=50)
    city_id: int | None = None
    room_type: str | None = Field(None, pattern="^(study|training|comprehensive)$")
    min_price: Decimal | None = Field(None, ge=0)
    status: str | None = Field(None, pattern="^(open|closed)$")


class RoomStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(open|closed)$")


class RoomAdminResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cover_image: str | None
    environment_images: list[str] | None = None
    address: str
    city_id: int | None = None
    city_name: str | None = None
    business_hours: str | None
    status: str
    room_type: str
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
