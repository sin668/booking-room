import math
import uuid
from dataclasses import dataclass
from datetime import datetime
from html import escape
from html.parser import HTMLParser
from zoneinfo import ZoneInfo

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity, ActivityCoupon
from app.models.coupon import Coupon, UserCoupon
from app.schemas.activity import (
    ActivityAdminResponse,
    ActivityCouponAdminResponse,
    ActivityCouponClaimResponse,
    ActivityCouponClaimUserCouponResponse,
    ActivityCouponPublicResponse,
    ActivityCouponTemplateResponse,
    ActivityDetailResponse,
)


CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")


class ActivityCouponError(ValueError):
    pass


class ActivityCouponClaimError(ActivityCouponError):
    pass


class ActivityCouponPublishError(ActivityCouponError):
    pass


@dataclass
class ActivityCouponClaimResult:
    user_coupon: UserCoupon
    activity_coupon: ActivityCoupon
    coupon: Coupon


class _RichTextSanitizer(HTMLParser):
    allowed_tags = {
        "p",
        "br",
        "strong",
        "b",
        "em",
        "i",
        "u",
        "s",
        "ul",
        "ol",
        "li",
        "blockquote",
        "h1",
        "h2",
        "h3",
        "h4",
        "span",
        "div",
        "a",
        "img",
    }
    allowed_attrs = {
        "a": {"href", "title", "target", "rel"},
        "img": {"src", "alt", "title"},
        "span": {"style"},
        "div": {"style"},
        "p": {"style"},
    }
    safe_protocols = ("http://", "https://", "/", "#")
    void_tags = {"br", "img"}

    def __init__(self) -> None:
        super().__init__(convert_charrefs=True)
        self.parts: list[str] = []
        self.skip_depth = 0

    def handle_starttag(self, tag: str, attrs):
        tag = tag.lower()
        if tag in {"script", "style", "iframe", "object"}:
            self.skip_depth += 1
            return
        if self.skip_depth or tag not in self.allowed_tags:
            return

        clean_attrs: list[str] = []
        allowed_attrs = self.allowed_attrs.get(tag, set())
        for raw_name, raw_value in attrs:
            name = raw_name.lower()
            value = raw_value or ""
            if name.startswith("on") or name not in allowed_attrs:
                continue
            if name in {"href", "src"} and not self._is_safe_url(value):
                continue
            if name == "style" and not self._is_safe_style(value):
                continue
            if tag == "a" and name == "target" and value not in {"_blank", "_self"}:
                continue
            clean_attrs.append(f'{name}="{escape(value, quote=True)}"')

        if tag == "a" and any(attr.startswith("target=\"_blank\"") for attr in clean_attrs):
            clean_attrs.append('rel="noopener noreferrer"')

        attr_text = f" {' '.join(clean_attrs)}" if clean_attrs else ""
        self.parts.append(f"<{tag}{attr_text}>")

    def handle_endtag(self, tag: str):
        tag = tag.lower()
        if tag in {"script", "style", "iframe", "object"} and self.skip_depth:
            self.skip_depth -= 1
            return
        if self.skip_depth or tag not in self.allowed_tags or tag in self.void_tags:
            return
        self.parts.append(f"</{tag}>")

    def handle_data(self, data: str):
        if not self.skip_depth:
            self.parts.append(escape(data, quote=False))

    def handle_entityref(self, name: str):
        if not self.skip_depth:
            self.parts.append(f"&{name};")

    def handle_charref(self, name: str):
        if not self.skip_depth:
            self.parts.append(f"&#{name};")

    def _is_safe_url(self, value: str) -> bool:
        lower_value = value.strip().lower()
        return lower_value.startswith(self.safe_protocols)

    def _is_safe_style(self, value: str) -> bool:
        lower_value = value.lower()
        return "expression" not in lower_value and "javascript:" not in lower_value


def sanitize_activity_content(content_html: str | None) -> str:
    if not content_html or not content_html.strip():
        return ""
    sanitizer = _RichTextSanitizer()
    sanitizer.feed(content_html)
    sanitizer.close()
    return "".join(sanitizer.parts).strip()


def _now() -> datetime:
    return datetime.now(CHINA_TIMEZONE).replace(tzinfo=None)


def _normalize_activity_coupon_time(value: datetime | None) -> datetime | None:
    if value is None:
        return None
    if value.tzinfo is None:
        return value
    return value.astimezone(CHINA_TIMEZONE).replace(tzinfo=None)


def _coupon_to_response(coupon: Coupon) -> ActivityCouponTemplateResponse:
    return ActivityCouponTemplateResponse(
        id=coupon.id,
        name=coupon.name,
        description=coupon.description,
        type=coupon.type,
        discount_amount=coupon.discount_amount,
        discount_percent=coupon.discount_percent,
        min_order_amount=coupon.min_order_amount,
        scope=coupon.scope,
        seat_zone=coupon.seat_zone,
        valid_from=coupon.valid_from,
        expires_at=coupon.expires_at,
        is_active=coupon.is_active,
    )


def _admin_coupon_to_response(activity_coupon: ActivityCoupon, coupon: Coupon | None) -> ActivityCouponAdminResponse:
    return ActivityCouponAdminResponse(
        id=activity_coupon.id,
        activity_id=activity_coupon.activity_id,
        coupon_id=activity_coupon.coupon_id,
        total_quantity=activity_coupon.total_quantity,
        claimed_quantity=activity_coupon.claimed_quantity,
        remaining_quantity=max(activity_coupon.total_quantity - activity_coupon.claimed_quantity, 0),
        per_user_limit=activity_coupon.per_user_limit,
        claim_starts_at=activity_coupon.claim_starts_at,
        claim_ends_at=activity_coupon.claim_ends_at,
        is_active=activity_coupon.is_active,
        sort_order=activity_coupon.sort_order,
        display_title=activity_coupon.display_title,
        display_description=activity_coupon.display_description,
        coupon=_coupon_to_response(coupon) if coupon else None,
    )


def _activity_to_admin_response(
    activity: Activity,
    activity_coupon_rows: list[tuple[ActivityCoupon, Coupon]] | None = None,
) -> ActivityAdminResponse:
    rows = activity_coupon_rows or []
    activity_coupons = [_admin_coupon_to_response(activity_coupon, coupon) for activity_coupon, coupon in rows]
    return ActivityAdminResponse(
        id=activity.id,
        title=activity.title,
        description=activity.description,
        content_html=activity.content_html or "",
        cover_image=activity.cover_image,
        participant_count=activity.participant_count,
        sort_order=activity.sort_order,
        is_active=activity.is_active,
        created_at=activity.created_at,
        updated_at=activity.updated_at,
        activity_coupons=activity_coupons,
        activity_coupon_count=len(activity_coupons),
        activity_coupon_claimed_count=sum(item.claimed_quantity for item in activity_coupons),
    )


async def _load_activity_coupon_rows(
    db: AsyncSession,
    activity_id: int,
    include_inactive: bool = True,
) -> list[tuple[ActivityCoupon, Coupon]]:
    statement = (
        select(ActivityCoupon, Coupon)
        .join(Coupon, Coupon.id == ActivityCoupon.coupon_id)
        .where(ActivityCoupon.activity_id == activity_id)
        .order_by(ActivityCoupon.sort_order.asc(), ActivityCoupon.id.asc())
    )
    if not include_inactive:
        now = _now()
        statement = statement.where(
            ActivityCoupon.is_active.is_(True),
            Coupon.is_active.is_(True),
            (ActivityCoupon.claim_ends_at.is_(None) | (ActivityCoupon.claim_ends_at >= now)),
        )
    return list((await db.execute(statement)).all())


async def _replace_activity_coupons(
    db: AsyncSession,
    activity: Activity,
    activity_coupons: list[dict],
) -> None:
    existing_rows = (
        await db.execute(select(ActivityCoupon).where(ActivityCoupon.activity_id == activity.id))
    ).scalars().all()
    existing_by_id = {item.id: item for item in existing_rows}
    seen_ids: set[int] = set()

    for item in activity_coupons:
        coupon = await db.get(Coupon, item["coupon_id"])
        if coupon is None:
            raise ActivityCouponError("卡券模板不存在")

        claim_starts_at = _normalize_activity_coupon_time(item.get("claim_starts_at"))
        claim_ends_at = _normalize_activity_coupon_time(item.get("claim_ends_at"))
        if claim_starts_at and claim_ends_at and claim_ends_at < claim_starts_at:
            raise ActivityCouponError("领取结束时间不能早于开始时间")
        item_id = item.get("id")
        if item_id is not None and item_id in existing_by_id:
            activity_coupon = existing_by_id[item_id]
            seen_ids.add(item_id)
            if item["total_quantity"] < activity_coupon.claimed_quantity:
                raise ActivityCouponError("总库存不能小于已领取数量")
        else:
            activity_coupon = ActivityCoupon(activity_id=activity.id, claimed_quantity=0)
            db.add(activity_coupon)

        activity_coupon.coupon_id = item["coupon_id"]
        activity_coupon.total_quantity = item["total_quantity"]
        activity_coupon.per_user_limit = item.get("per_user_limit", 1)
        activity_coupon.claim_starts_at = claim_starts_at
        activity_coupon.claim_ends_at = claim_ends_at
        activity_coupon.is_active = item.get("is_active", True)
        activity_coupon.sort_order = item.get("sort_order", 0)
        activity_coupon.display_title = item.get("display_title")
        activity_coupon.display_description = item.get("display_description")

    for activity_coupon in existing_rows:
        if activity_coupon.id not in seen_ids and activity_coupon.claimed_quantity == 0:
            await db.delete(activity_coupon)
        elif activity_coupon.id not in seen_ids:
            activity_coupon.is_active = False


async def _validate_publishable_activity_coupons(db: AsyncSession, activity_id: int) -> None:
    activity_coupons = (
        await db.execute(select(ActivityCoupon).where(ActivityCoupon.activity_id == activity_id))
    ).scalars().all()
    for activity_coupon in activity_coupons:
        if not activity_coupon.is_active:
            continue
        coupon = await db.get(Coupon, activity_coupon.coupon_id)
        if coupon is None:
            raise ActivityCouponPublishError("卡券模板不存在")
        if coupon is None or not coupon.is_active:
            raise ActivityCouponPublishError("启用的活动卡券必须关联启用的卡券模板")
        if activity_coupon.total_quantity < activity_coupon.claimed_quantity:
            raise ActivityCouponPublishError("总库存不能小于已领取数量")
        if activity_coupon.per_user_limit < 1:
            raise ActivityCouponPublishError("每人限领数量必须大于 0")


async def list_active_activities(db: AsyncSession) -> list[Activity]:
    """Return all active activities ordered by sort_order ascending."""
    result = await db.execute(
        select(Activity)
        .where(Activity.is_active.is_(True))
        .order_by(Activity.sort_order.asc())
    )
    return list(result.scalars().all())


async def list_activities(
    db: AsyncSession,
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    is_active: bool | None = None,
) -> dict:
    """Return paginated activity list with optional keyword search and status filter."""
    query = select(Activity)
    count_query = select(func.count(Activity.id))

    if keyword:
        pattern = f"%{keyword}%"
        query = query.where(
            Activity.title.ilike(pattern) | Activity.description.ilike(pattern)
        )
        count_query = count_query.where(
            Activity.title.ilike(pattern) | Activity.description.ilike(pattern)
        )

    if is_active is not None:
        query = query.where(Activity.is_active.is_(is_active))
        count_query = count_query.where(Activity.is_active.is_(is_active))

    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    total_pages = math.ceil(total / page_size) if total > 0 else 0
    offset = (page - 1) * page_size
    if offset > total and total > 0:
        offset = (total_pages - 1) * page_size

    query = query.order_by(Activity.created_at.desc()).offset(offset).limit(page_size)
    result = await db.execute(query)
    items = list(result.scalars().all())
    response_items: list[ActivityAdminResponse] = []
    for activity in items:
        rows = await _load_activity_coupon_rows(db, activity.id)
        response_items.append(_activity_to_admin_response(activity, rows))

    return {"total": total, "page": page, "page_size": page_size, "items": response_items}


async def get_activity_by_id(db: AsyncSession, activity_id: int) -> Activity | None:
    """Return a single activity by ID, or None if not found."""
    result = await db.execute(select(Activity).where(Activity.id == activity_id))
    return result.scalar_one_or_none()


async def create_activity(db: AsyncSession, data: dict) -> ActivityAdminResponse:
    """Create a new activity."""
    activity_coupons = data.pop("activity_coupons", [])
    data["content_html"] = sanitize_activity_content(data.get("content_html"))
    activity = Activity(**data)
    db.add(activity)
    await db.flush()
    await _replace_activity_coupons(db, activity, activity_coupons)
    if activity.is_active:
        await _validate_publishable_activity_coupons(db, activity.id)
    await db.flush()
    await db.refresh(activity)
    return _activity_to_admin_response(activity, await _load_activity_coupon_rows(db, activity.id))


async def update_activity(db: AsyncSession, activity: Activity, data: dict) -> ActivityAdminResponse:
    """Update an existing activity with the given fields."""
    activity_coupons = data.pop("activity_coupons", None)
    if "content_html" in data:
        data["content_html"] = sanitize_activity_content(data.get("content_html"))
    for key, value in data.items():
        if value is not None:
            setattr(activity, key, value)
    if activity_coupons is not None:
        await _replace_activity_coupons(db, activity, activity_coupons)
    if activity.is_active:
        await _validate_publishable_activity_coupons(db, activity.id)
    await db.flush()
    await db.refresh(activity)
    return _activity_to_admin_response(activity, await _load_activity_coupon_rows(db, activity.id))


async def delete_activity(db: AsyncSession, activity: Activity) -> None:
    """Delete an activity."""
    await db.delete(activity)
    await db.flush()


async def toggle_activity_status(db: AsyncSession, activity: Activity, is_active: bool) -> ActivityAdminResponse:
    """Toggle activity active status."""
    if is_active:
        await _validate_publishable_activity_coupons(db, activity.id)
    activity.is_active = is_active
    await db.flush()
    await db.refresh(activity)
    return _activity_to_admin_response(activity, await _load_activity_coupon_rows(db, activity.id))


async def get_admin_activity_response(db: AsyncSession, activity_id: int) -> ActivityAdminResponse | None:
    activity = await get_activity_by_id(db, activity_id)
    if activity is None:
        return None
    return _activity_to_admin_response(activity, await _load_activity_coupon_rows(db, activity.id))


async def _count_user_claims(
    db: AsyncSession,
    user_id: str | uuid.UUID,
    activity_coupon_id: int,
) -> int:
    return int(
        await db.scalar(
            select(func.count(UserCoupon.id)).where(
                UserCoupon.user_id == str(user_id),
                UserCoupon.source_type == "activity",
                UserCoupon.source_activity_coupon_id == activity_coupon_id,
            )
        )
        or 0
    )


def _public_coupon_status(
    activity: Activity,
    activity_coupon: ActivityCoupon,
    coupon: Coupon,
    user_claim_count: int | None,
    now: datetime,
) -> tuple[str, bool, int | None]:
    remaining_quantity = max(activity_coupon.total_quantity - activity_coupon.claimed_quantity, 0)
    remaining_user_claims = (
        None if user_claim_count is None else max(activity_coupon.per_user_limit - user_claim_count, 0)
    )
    if not activity.is_active or not activity_coupon.is_active or not coupon.is_active:
        return "disabled", False, remaining_user_claims
    if activity_coupon.claim_starts_at and activity_coupon.claim_starts_at > now:
        return "not_started", False, remaining_user_claims
    if activity_coupon.claim_ends_at and activity_coupon.claim_ends_at < now:
        return "ended", False, remaining_user_claims
    if remaining_quantity <= 0:
        return "sold_out", False, remaining_user_claims
    if user_claim_count is not None and user_claim_count >= activity_coupon.per_user_limit:
        return "limit_reached", False, remaining_user_claims
    if user_claim_count and user_claim_count > 0:
        return "claimed", True, remaining_user_claims
    return "available", True, remaining_user_claims


async def _activity_coupon_to_public_response(
    db: AsyncSession,
    activity: Activity,
    activity_coupon: ActivityCoupon,
    coupon: Coupon,
    user_id: str | uuid.UUID | None,
    now: datetime | None = None,
) -> ActivityCouponPublicResponse:
    now = now or _now()
    user_claim_count = None
    if user_id is not None:
        user_claim_count = await _count_user_claims(db, user_id, activity_coupon.id)
    status, is_claimable, remaining_user_claims = _public_coupon_status(
        activity, activity_coupon, coupon, user_claim_count, now
    )
    return ActivityCouponPublicResponse(
        id=activity_coupon.id,
        coupon_id=coupon.id,
        display_title=activity_coupon.display_title,
        display_description=activity_coupon.display_description,
        coupon=_coupon_to_response(coupon),
        total_quantity=activity_coupon.total_quantity,
        claimed_quantity=activity_coupon.claimed_quantity,
        remaining_quantity=max(activity_coupon.total_quantity - activity_coupon.claimed_quantity, 0),
        per_user_limit=activity_coupon.per_user_limit,
        remaining_user_claims=remaining_user_claims,
        claim_starts_at=activity_coupon.claim_starts_at,
        claim_ends_at=activity_coupon.claim_ends_at,
        claim_status=status,
        is_claimable=is_claimable,
    )


async def get_activity_detail(
    db: AsyncSession,
    activity_id: int,
    user_id: str | uuid.UUID | None = None,
) -> ActivityDetailResponse | None:
    activity = await get_activity_by_id(db, activity_id)
    if activity is None or not activity.is_active:
        return None
    rows = await _load_activity_coupon_rows(db, activity.id, include_inactive=False)
    coupons = [
        await _activity_coupon_to_public_response(db, activity, activity_coupon, coupon, user_id)
        for activity_coupon, coupon in rows
    ]
    return ActivityDetailResponse(
        id=activity.id,
        title=activity.title,
        description=activity.description,
        content_html=activity.content_html or "",
        cover_image=activity.cover_image,
        participant_count=activity.participant_count,
        is_active=activity.is_active,
        activity_coupons=coupons,
    )


async def claim_activity_coupon(
    db: AsyncSession,
    activity_id: int,
    activity_coupon_id: int,
    user_id: str | uuid.UUID,
    now: datetime | None = None,
) -> ActivityCouponClaimResult:
    now = now or _now()
    result = await db.execute(
        select(ActivityCoupon, Activity, Coupon)
        .join(Activity, Activity.id == ActivityCoupon.activity_id)
        .join(Coupon, Coupon.id == ActivityCoupon.coupon_id)
        .where(ActivityCoupon.id == activity_coupon_id, ActivityCoupon.activity_id == activity_id)
        .with_for_update()
    )
    row = result.one_or_none()
    if row is None:
        raise ActivityCouponClaimError("活动卡券不存在")
    activity_coupon, activity, coupon = row

    claim_count = await _count_user_claims(db, user_id, activity_coupon.id)
    status, _, _ = _public_coupon_status(activity, activity_coupon, coupon, claim_count, now)
    if status == "disabled":
        raise ActivityCouponClaimError("活动或卡券未启用")
    if status == "not_started":
        raise ActivityCouponClaimError("活动卡券尚未开始领取")
    if status == "ended":
        raise ActivityCouponClaimError("活动卡券已结束领取")
    if status == "sold_out":
        raise ActivityCouponClaimError("活动卡券库存不足")
    if status == "limit_reached":
        raise ActivityCouponClaimError("已达到领取上限")

    user_coupon = UserCoupon(
        user_id=str(user_id),
        coupon_id=coupon.id,
        status="available",
        source_type="activity",
        source_activity_id=activity.id,
        source_activity_coupon_id=activity_coupon.id,
    )
    activity_coupon.claimed_quantity += 1
    db.add(user_coupon)
    await db.flush()
    await db.refresh(user_coupon)
    return ActivityCouponClaimResult(
        user_coupon=user_coupon,
        activity_coupon=activity_coupon,
        coupon=coupon,
    )


async def claim_activity_coupon_response(
    db: AsyncSession,
    activity_id: int,
    activity_coupon_id: int,
    user_id: str | uuid.UUID,
) -> ActivityCouponClaimResponse:
    result = await claim_activity_coupon(db, activity_id, activity_coupon_id, user_id)
    activity = await get_activity_by_id(db, activity_id)
    public_coupon = await _activity_coupon_to_public_response(
        db,
        activity,
        result.activity_coupon,
        result.coupon,
        user_id,
    )
    return ActivityCouponClaimResponse(
        user_coupon=ActivityCouponClaimUserCouponResponse(
            id=result.user_coupon.id,
            coupon_id=result.user_coupon.coupon_id,
            status=result.user_coupon.status,
            source_type=result.user_coupon.source_type,
            source_activity_id=result.user_coupon.source_activity_id,
            source_activity_coupon_id=result.user_coupon.source_activity_coupon_id,
        ),
        activity_coupon=public_coupon,
    )
