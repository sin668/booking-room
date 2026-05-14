from datetime import date, datetime
from decimal import Decimal
from typing import Literal

from pydantic import BaseModel, ConfigDict

CouponType = Literal["amount_off", "threshold_amount_off", "percentage_off"]
CouponScope = Literal["all", "first_booking", "seat_zone"]
CouponStatus = Literal["available", "used", "expired"]


class CouponBaseResponse(BaseModel):
    id: int
    coupon_id: int
    name: str
    description: str | None
    type: CouponType
    scope: CouponScope
    status: CouponStatus
    discount_amount: Decimal | None
    discount_percent: int | None
    min_order_amount: Decimal
    valid_from: datetime
    expires_at: datetime
    used_at: datetime | None
    used_booking_id: int | None
    seat_zone: str | None

    model_config = ConfigDict(from_attributes=True)


class CouponResponse(CouponBaseResponse):
    pass


class AvailableCouponForBookingResponse(CouponBaseResponse):
    payable_amount: Decimal


class AvailableCouponsForBookingListResponse(BaseModel):
    original_price: Decimal
    items: list[AvailableCouponForBookingResponse]

    model_config = ConfigDict(from_attributes=True)

