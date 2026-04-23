from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ActivityResponse(BaseModel):
    id: int
    title: str
    description: str | None
    cover_image: str | None
    participant_count: int

    model_config = ConfigDict(from_attributes=True)


class ActivityCreate(BaseModel):
    title: str = Field(..., max_length=100, description="活动标题")
    description: str | None = Field(None, max_length=500, description="活动描述")
    cover_image: str | None = Field(None, max_length=512, description="封面图 URL")
    participant_count: int = Field(default=0, ge=0, description="参与人数")
    sort_order: int = Field(default=0, description="排序值")
    is_active: bool = Field(default=True, description="是否上架")


class ActivityUpdate(BaseModel):
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    cover_image: str | None = Field(None, max_length=512)
    participant_count: int | None = Field(None, ge=0)
    sort_order: int | None = None
    is_active: bool | None = None


class ActivityAdminResponse(BaseModel):
    id: int
    title: str
    description: str | None
    cover_image: str | None
    participant_count: int
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ActivityAdminResponse]


class ActivityStatusUpdate(BaseModel):
    is_active: bool


class UploadResponse(BaseModel):
    url: str
