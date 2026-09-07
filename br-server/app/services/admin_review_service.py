"""后台评价审核。

可见性契约：后台永不脱敏，匿名评价同样返回真实昵称与头像，并携带匿名标记。
事务契约：不自行 commit，由 `get_db` 依赖统一提交/回滚。
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.review_status import ReviewStatus
from app.models.review import Review
from app.models.user import User
from app.schemas.admin_review import (
    AdminReviewItem,
    AdminReviewListResponse,
    ReviewReplyUpdate,
    ReviewStatusUpdate,
)
from app.services.review_service import (
    DEFAULT_PAGE_SIZE,
    RATING_BANDS,
    assemble_items,
    order_by_clauses,
    refresh_rating_aggregates,
)
from app.utils.timezone import booking_now


async def _to_admin_items(db: AsyncSession, reviews: list[Review]) -> list[AdminReviewItem]:
    """复用 C 端的批量关联查询，再补上后台独有的审核元数据。"""
    base_items = await assemble_items(db, reviews, mask_anonymous=False)
    return [
        AdminReviewItem(
            **base.model_dump(),
            reviewed_by=review.reviewed_by,
            reviewed_at=review.reviewed_at,
        )
        for base, review in zip(base_items, reviews)
    ]


async def _get_review_or_404(db: AsyncSession, review_id: int) -> Review:
    review = await db.get(Review, review_id)
    if review is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="评价不存在"
        )
    return review


async def list_reviews(
    db: AsyncSession,
    *,
    review_status: str | None = None,
    rating_band: str = "all",
    keyword: str | None = None,
    sort: str = "new",
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> AdminReviewListResponse:
    """后台评价列表：返回全部状态，支持状态/评分档位/关键词筛选。"""
    conditions: list = []
    if review_status:
        conditions.append(Review.status == review_status)
    band = RATING_BANDS.get(rating_band)
    if band:
        conditions.append(Review.rating.in_(band))

    trimmed = (keyword or "").strip()
    if trimmed:
        # 关键词同时匹配评价内容与发表者昵称，故需要 join users
        pattern = f"%{trimmed}%"
        conditions.append(or_(Review.content.ilike(pattern), User.nickname.ilike(pattern)))

    stmt = select(Review)
    count_stmt = select(func.count()).select_from(Review)
    if trimmed:
        stmt = stmt.join(User, Review.user_id == User.id)
        count_stmt = count_stmt.join(User, Review.user_id == User.id)
    if conditions:
        stmt = stmt.where(*conditions)
        count_stmt = count_stmt.where(*conditions)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.order_by(*order_by_clauses(sort))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = await _to_admin_items(db, list(result.scalars().all()))
    return AdminReviewListResponse(items=items, total=total, page=page, page_size=page_size)


async def update_status(
    db: AsyncSession,
    review_id: int,
    data: ReviewStatusUpdate,
    *,
    admin_id: uuid.UUID | None = None,
) -> AdminReviewItem:
    """审核通过或驳回。重复审核同一目标状态是幂等的。"""
    review = await _get_review_or_404(db, review_id)

    rejected = data.status is ReviewStatus.REJECTED
    if rejected and not data.reject_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="驳回必须填写理由",
        )

    review.status = data.status.value
    # 通过时清空历史驳回理由，避免旧理由残留在「我的评价」里
    review.reject_reason = data.reject_reason if rejected else None
    review.reviewed_by = admin_id
    review.reviewed_at = booking_now()
    await db.flush()

    # 审核状态变化会改变聚合口径，故重算受影响课程与老师的评分
    await refresh_rating_aggregates(
        db, course_id=review.course_id, teacher_id=review.teacher_id
    )

    return (await _to_admin_items(db, [review]))[0]


async def update_reply(
    db: AsyncSession,
    review_id: int,
    data: ReviewReplyUpdate,
) -> AdminReviewItem:
    """写入或更新机构回复；空白内容视为清空。"""
    review = await _get_review_or_404(db, review_id)

    content = data.reply_content.strip()
    if content:
        review.reply_content = content
        review.reply_at = booking_now()
    else:
        review.reply_content = None
        review.reply_at = None
    await db.flush()

    return (await _to_admin_items(db, [review]))[0]
