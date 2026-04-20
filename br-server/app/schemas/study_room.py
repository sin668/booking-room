from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class StudyRoomResponse(BaseModel):
    id: int
    name: str
    description: str | None
    cover_image: str | None
    address: str
    business_hours: str | None
    status: str
    min_price: Decimal

    model_config = ConfigDict(from_attributes=True)


class StudyRoomListResponse(BaseModel):
    items: list[StudyRoomResponse]
    total: int
    page: int
    page_size: int
