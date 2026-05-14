from __future__ import annotations

import uuid
from datetime import date, datetime, time
from decimal import Decimal, ROUND_HALF_UP
from typing import NamedTuple
from zoneinfo import ZoneInfo

from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.seat import Seat
from app.schemas.coupon import (
    AvailableCouponForBookingResponse,
    AvailableCouponsForBookingListResponse,
    CouponResponse,
)


class CouponError(ValueError):
    pass


class CouponNotFoundError(CouponError):
    pass


class CouponUnavailableError(CouponError):
    pass


class BookingCouponCalculation(NamedTuple):
    original_price: Decimal
    discount_amount: Decimal
    payable_amount: Decimal
    user_coupon: UserCoupon


CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


def _now() -> datetime:
    return datetime.now(CHINA_TIMEZONE)


def _now_for_db() -> datetime:
    return _now().replace(tzinfo=None)


def _ensure_aware(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=CHINA_TIMEZONE)
    return value.astimezone(CHINA_TIMEZONE)


def _money(value: Decimal | float | int | str) -> Decimal:
    return Decimal(str(value)).quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calculate_hours(start_time: time, end_time: time) -> Decimal:
    start_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_seconds = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
    hours = Decimal(end_seconds - start_seconds) / Decimal(3600)
    return hours.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP)


def _calculate_original_price(price_per_hour: Decimal, start_time: time, end_time: time) -> Decimal:
    return _money(Decimal(str(price_per_hour)) * _calculate_hours(start_time, end_time))


def calculate_original_price(price_per_hour: Decimal, start_time: time, end_time: time) -> Decimal:
    return _calculate_original_price(price_per_hour, start_time, end_time)


def _get_coupon_status(user_coupon: UserCoupon, coupon: Coupon, now: datetime | None = None) -> str:
    if user_coupon.status == "used":
        return "used"
    if not coupon.is_active:
        return "expired"
    now = _ensure_aware(now or _now())
    valid_from = _ensure_aware(coupon.valid_from)
    expires_at = _ensure_aware(coupon.expires_at)
    if valid_from > now or expires_at < now:
        return "expired"
    return "available"


def _calc_discount(coupon: Coupon, original_price: Decimal) -> Decimal:
    original_price = _money(original_price)
    if coupon.type == "amount_off":
        discount = Decimal(str(coupon.discount_amount or 0))
    elif coupon.type == "threshold_amount_off":
        if original_price < Decimal(str(coupon.min_order_amount or 0)):
            return Decimal("0.00")
        discount = Decimal(str(coupon.discount_amount or 0))
    elif coupon.type == "percentage_off":
        percent = Decimal(str(coupon.discount_percent or 100))
        discount = original_price * (Decimal("100") - percent) / Decimal("100")
    else:
        raise CouponUnavailableError("不支持的卡券类型")
    discount = min(_money(discount), original_price)
    return _money(discount)


async def _load_user_coupons(db: AsyncSession, user_id: str) -> list[tuple[UserCoupon, Coupon]]:
    result = await db.execute(
        select(UserCoupon, Coupon)
        .join(Coupon, Coupon.id == UserCoupon.coupon_id)
        .where(UserCoupon.user_id == user_id)
        .order_by(UserCoupon.id.asc())
    )
    return list(result.all())


def _to_response(user_coupon: UserCoupon, coupon: Coupon, now: datetime | None = None) -> CouponResponse:
    status = _get_coupon_status(user_coupon, coupon, now=now)
    return CouponResponse(
        id=user_coupon.id,
        coupon_id=coupon.id,
        name=coupon.name,
        description=coupon.description,
        type=coupon.type,
        scope=coupon.scope,
        status=status,
        discount_amount=coupon.discount_amount,
        discount_percent=coupon.discount_percent,
        min_order_amount=_money(coupon.min_order_amount),
        valid_from=_ensure_aware(coupon.valid_from),
        expires_at=_ensure_aware(coupon.expires_at),
        used_at=user_coupon.used_at,
        used_booking_id=user_coupon.used_booking_id,
        seat_zone=coupon.seat_zone,
    )


async def list_user_coupons(
    db: AsyncSession,
    user_id: str | uuid.UUID,
    status: str | None = None,
) -> list[CouponResponse]:
    rows = await _load_user_coupons(db, str(user_id))
    now = _now()
    items: list[CouponResponse] = []
    for user_coupon, coupon in rows:
        item = _to_response(user_coupon, coupon, now=now)
        if status is None or item.status == status:
            items.append(item)
    return items


async def _has_booking_history(db: AsyncSession, user_id: str) -> bool:
    statement = select(
        exists().where(
            Booking.user_id == user_id,
            Booking.status.in_(["confirmed", "completed"]),
        )
    )
    return bool(await db.scalar(statement))


def _scope_allows(coupon: Coupon, seat: Seat, has_history: bool) -> bool:
    if coupon.scope == "all":
        return True
    if coupon.scope == "first_booking":
        return not has_history
    if coupon.scope == "seat_zone":
        return coupon.seat_zone == seat.zone
    raise CouponUnavailableError("不支持的适用范围")


async def list_available_coupons_for_booking(
    db: AsyncSession,
    user_id: str | uuid.UUID,
    seat_id: int,
    date: date,
    start_time: time,
    end_time: time,
) -> AvailableCouponsForBookingListResponse:
    seat_result = await db.execute(select(Seat).where(Seat.id == seat_id))
    seat = seat_result.scalar_one_or_none()
    if seat is None:
        raise CouponNotFoundError("座位不存在")

    original_price = _calculate_original_price(Decimal(str(seat.price_per_hour)), start_time, end_time)
    has_history = await _has_booking_history(db, str(user_id))
    rows = await _load_user_coupons(db, str(user_id))
    now = _now()

    items: list[AvailableCouponForBookingResponse] = []
    for user_coupon, coupon in rows:
        if not coupon.is_active:
            continue
        status = _get_coupon_status(user_coupon, coupon, now=now)
        if status != "available":
            continue
        if not _scope_allows(coupon, seat, has_history):
            continue
        discount_amount = _calc_discount(coupon, original_price)
        if discount_amount <= Decimal("0.00"):
            continue
        if coupon.type == "threshold_amount_off" and original_price < _money(coupon.min_order_amount):
            continue
        items.append(
            AvailableCouponForBookingResponse(
                id=user_coupon.id,
                coupon_id=coupon.id,
                name=coupon.name,
                description=coupon.description,
                type=coupon.type,
                scope=coupon.scope,
                status=status,
                discount_amount=discount_amount,
                discount_percent=coupon.discount_percent,
                min_order_amount=_money(coupon.min_order_amount),
                valid_from=_ensure_aware(coupon.valid_from),
                expires_at=_ensure_aware(coupon.expires_at),
                used_at=user_coupon.used_at,
                used_booking_id=user_coupon.used_booking_id,
                seat_zone=coupon.seat_zone,
                payable_amount=_money(original_price - discount_amount),
            )
        )

    return AvailableCouponsForBookingListResponse(original_price=original_price, items=items)


async def validate_coupon_for_booking(
    db: AsyncSession,
    user_id: str | uuid.UUID,
    user_coupon_id: int,
    seat: Seat,
    start_time: time,
    end_time: time,
) -> BookingCouponCalculation:
    result = await db.execute(
        select(UserCoupon, Coupon)
        .join(Coupon, Coupon.id == UserCoupon.coupon_id)
        .where(UserCoupon.id == user_coupon_id)
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise CouponUnavailableError("卡券不可用")

    user_coupon, coupon = row
    original_price = _calculate_original_price(
        Decimal(str(seat.price_per_hour)), start_time, end_time
    )

    if user_coupon.user_id != str(user_id):
        raise CouponUnavailableError("卡券不可用")
    if not coupon.is_active:
        raise CouponUnavailableError("卡券不可用")
    if _get_coupon_status(user_coupon, coupon) != "available":
        raise CouponUnavailableError("卡券不可用")

    has_history = await _has_booking_history(db, str(user_id))
    if not _scope_allows(coupon, seat, has_history):
        raise CouponUnavailableError("卡券不可用")

    discount_amount = _calc_discount(coupon, original_price)
    if discount_amount <= Decimal("0.00"):
        raise CouponUnavailableError("卡券不可用")

    payable_amount = _money(original_price - discount_amount)
    return BookingCouponCalculation(
        original_price=original_price,
        discount_amount=discount_amount,
        payable_amount=payable_amount,
        user_coupon=user_coupon,
    )


def mark_coupon_used(user_coupon: UserCoupon, booking_id: int) -> None:
    user_coupon.status = "used"
    user_coupon.used_booking_id = booking_id
    user_coupon.used_at = _now_for_db()


async def restore_user_coupon_for_booking(db: AsyncSession, booking: Booking) -> None:
    if booking.coupon_id is None:
        return

    result = await db.execute(select(UserCoupon).where(UserCoupon.id == booking.coupon_id))
    user_coupon = result.scalar_one_or_none()
    if user_coupon is None or user_coupon.used_booking_id != booking.id:
        return

    user_coupon.status = "available"
    user_coupon.used_booking_id = None
    user_coupon.used_at = None
