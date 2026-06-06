from datetime import datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.upload import UploadResponse


class ActivityResponse(BaseModel):
    id: int
    title: str
    description: str | None
    content_html: str = ""
    cover_image: str | None
    participant_count: int

    model_config = ConfigDict(from_attributes=True)


class ActivityCouponInput(BaseModel):
    id: int | None = Field(None, description="活动卡券配置 ID，更新时传入")
    coupon_id: int = Field(..., ge=1, description="卡券模板 ID")
    total_quantity: int = Field(..., ge=0, description="总库存")
    per_user_limit: int = Field(default=1, ge=1, description="每人限领数量")
    claim_starts_at: datetime | None = Field(None, description="领取开始时间")
    claim_ends_at: datetime | None = Field(None, description="领取结束时间")
    is_active: bool = Field(default=True, description="是否启用")
    sort_order: int = Field(default=0, description="排序值")
    display_title: str | None = Field(None, max_length=100, description="展示标题")
    display_description: str | None = Field(None, max_length=255, description="展示说明")


class ActivityCouponTemplateResponse(BaseModel):
    id: int
    name: str
    description: str | None
    type: str
    discount_amount: Decimal | None
    discount_percent: int | None
    min_order_amount: Decimal
    scope: str
    seat_zone: str | None
    valid_from: datetime
    expires_at: datetime
    is_active: bool


class ActivityCouponAdminResponse(BaseModel):
    id: int
    activity_id: int
    coupon_id: int
    total_quantity: int
    claimed_quantity: int
    remaining_quantity: int
    per_user_limit: int
    claim_starts_at: datetime | None
    claim_ends_at: datetime | None
    is_active: bool
    sort_order: int
    display_title: str | None
    display_description: str | None
    coupon: ActivityCouponTemplateResponse | None = None


ActivityCouponClaimStatus = Literal[
    "available",
    "claimed",
    "limit_reached",
    "not_started",
    "ended",
    "sold_out",
    "disabled",
]


class ActivityCouponPublicResponse(BaseModel):
    id: int
    coupon_id: int
    display_title: str | None
    display_description: str | None
    coupon: ActivityCouponTemplateResponse
    total_quantity: int
    claimed_quantity: int
    remaining_quantity: int
    per_user_limit: int
    remaining_user_claims: int | None
    claim_starts_at: datetime | None
    claim_ends_at: datetime | None
    claim_status: ActivityCouponClaimStatus
    is_claimable: bool


class ActivityCreate(BaseModel):
    title: str = Field(..., max_length=100, description="活动标题")
    description: str | None = Field(None, max_length=500, description="活动描述")
    content_html: str | None = Field(None, description="活动详情富文本正文")
    cover_image: str | None = Field(None, max_length=512, description="封面图 URL")
    participant_count: int = Field(default=0, ge=0, description="参与人数")
    sort_order: int = Field(default=0, description="排序值")
    is_active: bool = Field(default=True, description="是否上架")
    activity_coupons: list[ActivityCouponInput] = Field(default_factory=list, description="活动卡券配置")


class ActivityUpdate(BaseModel):
    title: str | None = Field(None, max_length=100)
    description: str | None = Field(None, max_length=500)
    content_html: str | None = None
    cover_image: str | None = Field(None, max_length=512)
    participant_count: int | None = Field(None, ge=0)
    sort_order: int | None = None
    is_active: bool | None = None
    activity_coupons: list[ActivityCouponInput] | None = None


class ActivityAdminResponse(BaseModel):
    id: int
    title: str
    description: str | None
    content_html: str = ""
    cover_image: str | None
    participant_count: int
    sort_order: int
    is_active: bool
    created_at: datetime
    updated_at: datetime
    activity_coupons: list[ActivityCouponAdminResponse] = Field(default_factory=list)
    activity_coupon_count: int = 0
    activity_coupon_claimed_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class ActivityListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[ActivityAdminResponse]


class ActivityStatusUpdate(BaseModel):
    is_active: bool


class ActivityDetailResponse(ActivityResponse):
    is_active: bool
    activity_coupons: list[ActivityCouponPublicResponse] = Field(default_factory=list)


class ActivityCouponClaimUserCouponResponse(BaseModel):
    id: int
    coupon_id: int
    status: str
    source_type: str | None
    source_activity_id: int | None
    source_activity_coupon_id: int | None


class ActivityCouponClaimResponse(BaseModel):
    user_coupon: ActivityCouponClaimUserCouponResponse
    activity_coupon: ActivityCouponPublicResponse
