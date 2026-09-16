from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.domain.edu_listing_status import EduListingStatus

# 图片是上传接口回传的 URL（object key 上限 512），可授课时间取自前端固定选项
MAX_IMAGE_URL_LENGTH = 512
MAX_TIME_SLOT_LENGTH = 50
LISTING_TYPES = ("tutor", "training", "demand")


class EduListingCreate(BaseModel):
    """发布供需信息请求。"""

    listing_type: str = Field(..., pattern="^(tutor|training|demand)$")
    title: str = Field(..., min_length=1, max_length=100)
    subject: str | None = Field(None, max_length=50)
    teaching_mode: str | None = Field(None, max_length=50)
    price: Decimal | None = Field(None, ge=0)
    price_unit: str | None = Field(None, max_length=20)
    city_id: int | None = Field(None, ge=1, description="城市ID")
    area: str | None = Field(None, max_length=100, description="详细区域（如朝阳区、浦东新区）")
    description: str | None = Field(None, max_length=2000)
    images: list[str] = Field(default_factory=list, max_length=3)
    available_times: list[str] = Field(default_factory=list, max_length=20)

    @field_validator("title")
    @classmethod
    def strip_title(cls, v: str) -> str:
        stripped = v.strip()
        if not stripped:
            raise ValueError("标题不能为空")
        return stripped

    @field_validator("images", "available_times")
    @classmethod
    def bound_item_length(cls, v: list[str], info) -> list[str]:
        limit = MAX_IMAGE_URL_LENGTH if info.field_name == "images" else MAX_TIME_SLOT_LENGTH
        if any(len(item) > limit for item in v):
            raise ValueError("单项长度超出限制")
        return [item.strip() for item in v if item.strip()]


class EduListingItem(BaseModel):
    """供需信息条目。

    发布者昵称/头像/认证状态不在 EduListing 模型上，由 service 批量查询后显式构造。
    认证状态字段仅在详情场景填充，列表中保持 None。
    """

    id: int
    listing_type: str
    title: str
    subject: str | None = None
    teaching_mode: str | None = None
    price: Decimal | None = None
    price_unit: str | None = None
    city_id: int | None = None
    area: str | None = None
    description: str | None = None
    images: list[str] = Field(default_factory=list)
    available_times: list[str] = Field(default_factory=list)
    status: str
    reject_reason: str | None = None
    view_count: int = 0
    publisher_id: UUID | None = None
    publisher_nickname: str | None = None
    publisher_avatar: str | None = None
    publisher_education_verified: bool | None = None
    publisher_teacher_verified: bool | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)

    @field_validator("images", "available_times", mode="before")
    @classmethod
    def none_to_empty_list(cls, v):
        # 数据库列可空，契约要求序列化为 [] 而非 null
        return v or []


class EduListingListResponse(BaseModel):
    items: list[EduListingItem]
    total: int
    page: int
    page_size: int
