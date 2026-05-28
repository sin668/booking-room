from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


NotificationTypeValue = Literal["booking", "activity", "report", "arrival"]


class NotificationResponse(BaseModel):
    id: UUID
    type: NotificationTypeValue
    title: str
    content: str
    target_url: str | None = None
    target_type: str | None = None
    target_id: str | None = None
    is_read: bool
    created_at: datetime
    read_at: datetime | None = None

    model_config = ConfigDict(from_attributes=True)


class NotificationListResponse(BaseModel):
    items: list[NotificationResponse]
    total: int
    page: int
    page_size: int
    has_more: bool


class NotificationUnreadSummaryResponse(BaseModel):
    total_unread: int
    booking_count: int
    activity_count: int
    report_count: int
    arrival_count: int


class NotificationPreferenceResponse(BaseModel):
    booking_enabled: bool
    activity_enabled: bool
    report_enabled: bool
    arrival_enabled: bool
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class NotificationPreferenceUpdate(BaseModel):
    booking_enabled: bool | None = None
    activity_enabled: bool | None = None
    report_enabled: bool | None = None
    arrival_enabled: bool | None = None


class NotificationReadAllResponse(BaseModel):
    updated_count: int


class NotificationCreate(BaseModel):
    user_id: UUID
    type: NotificationTypeValue
    title: str = Field(min_length=1, max_length=100)
    content: str = Field(min_length=1, max_length=1000)
    target_url: str | None = Field(default=None, max_length=512)
    target_type: str | None = Field(default=None, max_length=50)
    target_id: str | None = Field(default=None, max_length=64)
