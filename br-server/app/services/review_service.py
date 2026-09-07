"""学员评价 C 端查询与发表。

事务契约：本模块不自行 commit，由 `get_db` 依赖统一提交/回滚；
需要拿到自增主键或默认值时用 flush + refresh。
关联数据（昵称/头像/课程名/老师名）一律批量 select 后在内存组装，
不声明 relationship，避免 async 序列化触发 MissingGreenlet。
"""

from __future__ import annotations

import uuid
from decimal import ROUND_HALF_UP, Decimal

from fastapi import HTTPException, status
from sqlalchemy import and_, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.booking_status import BookingStatus
from app.domain.review_status import ReviewStatus
from app.models.booking import Booking
from app.models.course import Course
from app.models.review import Review
from app.models.teacher import Teacher
from app.models.user import User
from app.schemas.review import (
    ReviewCreate,
    ReviewItem,
    ReviewListResponse,
    ReviewSummary,
)

DEFAULT_PAGE_SIZE = 20
MAX_PAGE_SIZE = 50
ANONYMOUS_NICKNAME = "匿名用户"
# 好评档位下限：4 星及以上计入好评率
POSITIVE_RATING_FLOOR = 4
# 评分档位 → rating 取值集合；"all" 不追加条件
RATING_BANDS: dict[str, tuple[int, ...]] = {
    "good": (4, 5),
    "mid": (3,),
    "bad": (1, 2),
}


def round_half_up(value: Decimal | float | int, places: str = "0.1") -> float:
    """四舍五入到指定小数位。

    Python 内置 round 是银行家舍入（round(4.25, 1) == 4.2），与 spec 约定的
    「平均分 5/5/4/3 → 4.3」不符，故评分聚合统一走本函数。
    """
    return float(Decimal(str(value)).quantize(Decimal(places), rounding=ROUND_HALF_UP))


def _base_conditions(
    *,
    course_id: int | None = None,
    teacher_id: int | None = None,
    booking_id: int | None = None,
    rating_band: str = "all",
    has_images: bool = False,
) -> list:
    conditions: list = []
    if course_id is not None:
        conditions.append(Review.course_id == course_id)
    if teacher_id is not None:
        conditions.append(Review.teacher_id == teacher_id)
    if booking_id is not None:
        conditions.append(Review.booking_id == booking_id)
    band = RATING_BANDS.get(rating_band)
    if band:
        conditions.append(Review.rating.in_(band))
    if has_images:
        # create_review 把空图片列表写成 NULL，故 IS NOT NULL 即等价于"有图"，
        # 无需依赖各方言的 JSON 数组长度函数
        conditions.append(Review.images.is_not(None))
    return conditions


def _order_by(sort: str):
    if sort == "score":
        return (Review.rating.desc(), Review.created_at.desc(), Review.id.desc())
    return (Review.created_at.desc(), Review.id.desc())


async def _assemble_items(
    db: AsyncSession,
    reviews: list[Review],
    *,
    mask_anonymous: bool,
) -> list[ReviewItem]:
    """批量补齐昵称/头像/课程名/老师名并组装条目。"""
    if not reviews:
        return []

    user_ids = {r.user_id for r in reviews}
    course_ids = {r.course_id for r in reviews if r.course_id is not None}
    teacher_ids = {r.teacher_id for r in reviews if r.teacher_id is not None}

    users = (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
    user_map: dict[uuid.UUID, User] = {u.id: u for u in users}
    course_map: dict[int, str] = {}
    if course_ids:
        courses = (await db.execute(select(Course).where(Course.id.in_(course_ids)))).scalars().all()
        course_map = {c.id: c.name for c in courses}
    teacher_map: dict[int, str] = {}
    if teacher_ids:
        teachers = (await db.execute(select(Teacher).where(Teacher.id.in_(teacher_ids)))).scalars().all()
        teacher_map = {t.id: t.name for t in teachers}

    items: list[ReviewItem] = []
    for review in reviews:
        user = user_map.get(review.user_id)
        anonymous = mask_anonymous and review.is_anonymous
        items.append(
            ReviewItem(
                id=review.id,
                booking_id=review.booking_id,
                user_nickname=ANONYMOUS_NICKNAME if anonymous else (user.nickname if user else None),
                user_avatar=None if anonymous else (user.avatar if user else None),
                rating=review.rating,
                content=review.content,
                images=review.images,
                tags=review.tags,
                is_anonymous=review.is_anonymous,
                course_id=review.course_id,
                course_name=course_map.get(review.course_id) if review.course_id else None,
                teacher_id=review.teacher_id,
                teacher_name=teacher_map.get(review.teacher_id) if review.teacher_id else None,
                reply_content=review.reply_content,
                reply_at=review.reply_at,
                status=review.status,
                reject_reason=review.reject_reason,
                created_at=review.created_at,
            )
        )
    return items


async def list_reviews(
    db: AsyncSession,
    *,
    user_id: uuid.UUID | None = None,
    course_id: int | None = None,
    teacher_id: int | None = None,
    booking_id: int | None = None,
    mine: bool = False,
    rating_band: str = "all",
    has_images: bool = False,
    sort: str = "new",
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> ReviewListResponse:
    """评价列表。

    `mine=True` 返回本人全部状态的评价（含 pending / rejected），不做匿名脱敏；
    否则只返回 approved，并对匿名评价脱敏。
    """
    conditions = _base_conditions(
        course_id=course_id,
        teacher_id=teacher_id,
        booking_id=booking_id,
        rating_band=rating_band,
        has_images=has_images,
    )
    if mine:
        conditions.append(Review.user_id == user_id)
    else:
        conditions.append(Review.status == ReviewStatus.APPROVED.value)
    where = and_(*conditions)

    total = (
        await db.execute(select(func.count()).select_from(Review).where(where))
    ).scalar_one()

    result = await db.execute(
        select(Review)
        .where(where)
        .order_by(*_order_by(sort))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = await _assemble_items(db, list(result.scalars().all()), mask_anonymous=not mine)
    return ReviewListResponse(items=items, total=total, page=page, page_size=page_size)


async def get_summary(
    db: AsyncSession,
    *,
    course_id: int | None = None,
    teacher_id: int | None = None,
) -> ReviewSummary:
    """评价概览。只统计 approved；无数据时返回全 0，不抛 404。"""
    conditions = [Review.status == ReviewStatus.APPROVED.value]
    conditions.extend(
        _base_conditions(course_id=course_id, teacher_id=teacher_id)
    )

    rows = (
        await db.execute(
            select(Review.rating, func.count())
            .where(and_(*conditions))
            .group_by(Review.rating)
        )
    ).all()

    distribution = {str(star): 0 for star in range(5, 0, -1)}
    count = 0
    rating_sum = 0
    positive = 0
    for rating, bucket_count in rows:
        # rating 由 schema 约束在 1-5，脏数据不会落到这里
        distribution[str(rating)] = bucket_count
        count += bucket_count
        rating_sum += rating * bucket_count
        if rating >= POSITIVE_RATING_FLOOR:
            positive += bucket_count

    if count == 0:
        return ReviewSummary(distribution=distribution)

    return ReviewSummary(
        average=round_half_up(Decimal(rating_sum) / Decimal(count)),
        count=count,
        # places="1" 即量化到整数，避免 Python 内置 round 的银行家舍入
        positive_rate=int(round_half_up(Decimal(positive * 100) / Decimal(count), "1")),
        distribution=distribution,
    )


async def create_review(
    db: AsyncSession,
    user_id: uuid.UUID,
    data: ReviewCreate,
) -> ReviewItem:
    """发表评价。一单一评由 reviews.booking_id 唯一约束强制。"""
    booking = await db.get(Booking, data.booking_id)
    # 订单不存在与订单归属他人统一 404，避免被用来枚举他人订单
    if booking is None or booking.user_id != str(user_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="订单不存在")
    if booking.status != BookingStatus.COMPLETED.value:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="只有已完成的订单才能评价",
        )

    review = Review(
        booking_id=booking.id,
        user_id=user_id,
        # 课程/老师标识从订单冗余而来，支撑两个维度的单表索引过滤
        course_id=booking.course_id,
        teacher_id=booking.teacher_id,
        rating=data.rating,
        content=data.content,
        images=data.images or None,
        tags=data.tags or None,
        is_anonymous=data.is_anonymous,
    )
    db.add(review)
    try:
        await db.flush()
    except IntegrityError as exc:
        await db.rollback()
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="该订单已评价"
        ) from exc
    await db.refresh(review)

    items = await _assemble_items(db, [review], mask_anonymous=False)
    return items[0]
