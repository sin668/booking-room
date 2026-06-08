from datetime import datetime
from decimal import Decimal
from typing import Any
from zoneinfo import ZoneInfo

from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import ActivityCoupon
from app.models.coupon import Coupon, UserCoupon
from app.schemas.coupon_admin import AdminCouponListResponse, AdminCouponResponse

CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


def _now_for_db() -> datetime:
    return datetime.now(CHINA_TIMEZONE).replace(tzinfo=None)


class AdminCouponError(ValueError):
    pass


class AdminCouponNotFoundError(AdminCouponError):
    pass


def _normalize_datetime(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(CHINA_TIMEZONE).replace(tzinfo=None)


def _validate_coupon_rule(data: dict[str, Any]) -> None:
    coupon_type = data.get("type")
    discount_amount = data.get("discount_amount")
    discount_percent = data.get("discount_percent")
    min_order_amount = Decimal(str(data.get("min_order_amount") or 0))

    if coupon_type == "threshold_amount_off":
        if discount_amount is None:
            raise AdminCouponError("满减券必须填写优惠金额")
        if min_order_amount <= Decimal("0"):
            raise AdminCouponError("满减券门槛金额必须大于0")
    elif coupon_type == "amount_off":
        if discount_amount is None:
            raise AdminCouponError("立减券必须填写优惠金额")
    elif coupon_type == "percentage_off":
        if discount_percent is None:
            raise AdminCouponError("折扣券必须填写折扣比例")
    else:
        raise AdminCouponError("不支持的卡券类型")


def _validate_time_range(data: dict[str, Any]) -> None:
    valid_from = data.get("valid_from")
    expires_at = data.get("expires_at")
    if valid_from and expires_at and expires_at <= valid_from:
        raise AdminCouponError("卡券结束时间必须晚于开始时间")


def _clean_coupon_data(data: dict[str, Any]) -> dict[str, Any]:
    cleaned = dict(data)
    if cleaned.get("scope") != "seat_zone":
        cleaned["seat_zone"] = None
    if "valid_from" in cleaned:
        cleaned["valid_from"] = _normalize_datetime(cleaned["valid_from"])
    if "expires_at" in cleaned:
        cleaned["expires_at"] = _normalize_datetime(cleaned["expires_at"])
    return cleaned


async def _is_linked_to_activity(db: AsyncSession, coupon_id: int) -> bool:
    return bool(
        await db.scalar(
            select(func.count())
            .select_from(ActivityCoupon)
            .where(ActivityCoupon.coupon_id == coupon_id)
        )
    )


async def _has_user_coupons(db: AsyncSession, coupon_id: int) -> bool:
    return bool(
        await db.scalar(
            select(func.count())
            .select_from(UserCoupon)
            .where(UserCoupon.coupon_id == coupon_id)
        )
    )


async def list_coupons(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    type: str | None = None,
    scope: str | None = None,
    is_active: bool | None = None,
) -> AdminCouponListResponse:
    page = max(page, 1)
    page_size = min(max(page_size, 1), 100)
    conditions = []
    if keyword:
        like = f"%{keyword.strip()}%"
        conditions.append(or_(Coupon.name.ilike(like), Coupon.description.ilike(like)))
    if type:
        conditions.append(Coupon.type == type)
    if scope:
        conditions.append(Coupon.scope == scope)
    if is_active is not None:
        conditions.append(Coupon.is_active == is_active)

    stmt = select(Coupon).where(*conditions)
    total = int(await db.scalar(select(func.count()).select_from(stmt.subquery())) or 0)
    result = await db.execute(
        stmt.order_by(Coupon.created_at.desc(), Coupon.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    return AdminCouponListResponse(
        total=total,
        page=page,
        page_size=page_size,
        items=[AdminCouponResponse.model_validate(item) for item in result.scalars().all()],
    )


async def get_coupon(db: AsyncSession, coupon_id: int) -> AdminCouponResponse | None:
    coupon = await db.get(Coupon, coupon_id)
    return AdminCouponResponse.model_validate(coupon) if coupon else None


async def _get_coupon_model(db: AsyncSession, coupon_id: int) -> Coupon:
    coupon = await db.get(Coupon, coupon_id)
    if coupon is None:
        raise AdminCouponNotFoundError("卡券不存在")
    return coupon


async def create_coupon(db: AsyncSession, data: dict[str, Any]) -> AdminCouponResponse:
    data = _clean_coupon_data(data)
    _validate_coupon_rule(data)
    _validate_time_range(data)
    coupon = Coupon(**data)
    db.add(coupon)
    await db.flush()
    await db.refresh(coupon)
    return AdminCouponResponse.model_validate(coupon)


async def update_coupon(db: AsyncSession, coupon_id: int, data: dict[str, Any]) -> AdminCouponResponse:
    coupon = await _get_coupon_model(db, coupon_id)
    data = _clean_coupon_data(data)
    merged = {
        "type": coupon.type,
        "discount_amount": coupon.discount_amount,
        "discount_percent": coupon.discount_percent,
        "min_order_amount": coupon.min_order_amount,
        "valid_from": coupon.valid_from,
        "expires_at": coupon.expires_at,
        **data,
    }
    if "type" in data and data["type"] != coupon.type and await _is_linked_to_activity(db, coupon_id):
        raise AdminCouponError("已关联活动的卡券禁止修改类型")
    _validate_coupon_rule(merged)
    _validate_time_range(merged)
    for key, value in data.items():
        setattr(coupon, key, value)
    await db.flush()
    await db.refresh(coupon)
    return AdminCouponResponse.model_validate(coupon)


async def toggle_status(db: AsyncSession, coupon_id: int, is_active: bool) -> AdminCouponResponse:
    coupon = await _get_coupon_model(db, coupon_id)
    if is_active and coupon.expires_at < _now_for_db():
        raise AdminCouponError("已过期卡券禁止启用")
    coupon.is_active = is_active
    await db.flush()
    await db.refresh(coupon)
    return AdminCouponResponse.model_validate(coupon)


async def delete_coupon(db: AsyncSession, coupon_id: int) -> None:
    coupon = await _get_coupon_model(db, coupon_id)
    if await _is_linked_to_activity(db, coupon_id) or await _has_user_coupons(db, coupon_id):
        raise AdminCouponError("已关联或已发放的卡券禁止删除")
    await db.delete(coupon)
    await db.flush()
