from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class AdminCouponCreate(BaseModel):
    name: str = Field(max_length=100)
    description: str | None = Field(default=None, max_length=255)
    type: str = Field(pattern="^(threshold_amount_off|amount_off|percentage_off)$")
    discount_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    discount_percent: int | None = Field(default=None, ge=1, le=99)
    min_order_amount: Decimal = Field(default=Decimal("0"), ge=0, decimal_places=2)
    scope: str = Field(default="all", pattern="^(all|first_booking|vip_only|seat_zone)$")
    seat_zone: str | None = Field(default=None, max_length=20)
    valid_from: datetime
    expires_at: datetime
    is_active: bool = True


class AdminCouponUpdate(BaseModel):
    name: str | None = Field(default=None, max_length=100)
    description: str | None = Field(default=None, max_length=255)
    type: str | None = Field(default=None, pattern="^(threshold_amount_off|amount_off|percentage_off)$")
    discount_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    discount_percent: int | None = Field(default=None, ge=1, le=99)
    min_order_amount: Decimal | None = Field(default=None, ge=0, decimal_places=2)
    scope: str | None = Field(default=None, pattern="^(all|first_booking|vip_only|seat_zone)$")
    seat_zone: str | None = Field(default=None, max_length=20)
    valid_from: datetime | None = None
    expires_at: datetime | None = None
    is_active: bool | None = None


class AdminCouponResponse(BaseModel):
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
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminCouponListResponse(BaseModel):
    total: int
    page: int
    page_size: int
    items: list[AdminCouponResponse]


class AdminCouponStatusUpdate(BaseModel):
    is_active: bool
