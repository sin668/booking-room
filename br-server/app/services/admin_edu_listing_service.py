"""后台教培供需审核。

可见性契约：后台返回全部状态，每条携带发布者昵称与认证状态摘要。
事务契约：不自行 commit，由 `get_db` 依赖统一提交/回滚。
审核幂等：重复流转到同一目标状态不报错。
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.edu_listing_status import EduListingStatus
from app.models.edu_listing import EduListing
from app.schemas.admin_edu_listing import (
    AdminEduListingItem,
    AdminEduListingListResponse,
    EduListingStatusUpdate,
)
from app.services.edu_listing_service import assemble_items
from app.utils.timezone import booking_now

# 后台分页默认 20、上限 100（沿用既有 admin 口径），比 C 端宽
ADMIN_DEFAULT_PAGE_SIZE = 20
ADMIN_MAX_PAGE_SIZE = 100


async def _to_admin_items(
    db: AsyncSession, listings: list[EduListing]
) -> list[AdminEduListingItem]:
    """复用 C 端的批量关联查询（含认证状态），再补上后台独有的审核元数据。"""
    base_items = await assemble_items(db, listings, with_certification=True)
    return [
        AdminEduListingItem(
            **base.model_dump(),
            reviewed_by=listing.reviewed_by,
            reviewed_at=listing.reviewed_at,
        )
        for base, listing in zip(base_items, listings)
    ]


async def _get_listing_or_404(db: AsyncSession, listing_id: int) -> EduListing:
    listing = await db.get(EduListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="供需信息不存在")
    return listing


async def list_edu_listings(
    db: AsyncSession,
    *,
    keyword: str | None = None,
    listing_type: str | None = None,
    listing_status: str | None = None,
    page: int = 1,
    page_size: int = ADMIN_DEFAULT_PAGE_SIZE,
) -> AdminEduListingListResponse:
    """后台审核列表：返回全部状态，支持关键词（标题模糊）/类型/状态筛选。"""
    conditions: list = []
    if listing_type:
        conditions.append(EduListing.listing_type == listing_type)
    if listing_status:
        conditions.append(EduListing.status == listing_status)
    trimmed = (keyword or "").strip()
    if trimmed:
        conditions.append(EduListing.title.ilike(f"%{trimmed}%"))

    count_stmt = select(func.count()).select_from(EduListing)
    stmt = select(EduListing)
    if conditions:
        count_stmt = count_stmt.where(*conditions)
        stmt = stmt.where(*conditions)

    total = (await db.execute(count_stmt)).scalar_one()
    result = await db.execute(
        stmt.order_by(EduListing.created_at.desc(), EduListing.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = await _to_admin_items(db, list(result.scalars().all()))
    return AdminEduListingListResponse(items=items, total=total, page=page, page_size=page_size)


async def update_status(
    db: AsyncSession,
    listing_id: int,
    data: EduListingStatusUpdate,
    *,
    admin_id: uuid.UUID | None = None,
) -> AdminEduListingItem:
    """审核通过 / 拒绝 / 下架。重复流转到同一目标状态是幂等的。"""
    listing = await _get_listing_or_404(db, listing_id)

    rejected = data.status is EduListingStatus.REJECTED
    if rejected and not data.reject_reason:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="拒绝必须填写理由",
        )

    listing.status = data.status.value
    # 仅拒绝保留理由，通过/下架清空历史理由
    listing.reject_reason = data.reject_reason if rejected else None
    listing.reviewed_by = admin_id
    listing.reviewed_at = booking_now()
    await db.flush()

    return (await _to_admin_items(db, [listing]))[0]
