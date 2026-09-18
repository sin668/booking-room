"""教培供需 C 端查询与发布。

事务契约：本模块不自行 commit，由 `get_db` 依赖统一提交/回滚；
需要拿到自增主键或默认值时用 flush + refresh。
关联数据（发布者昵称/头像/认证状态）一律批量 select 后在内存组装，
不声明 relationship，避免 async 序列化触发 MissingGreenlet。

认证前置校验：发布 tutor 需学历认证、training 需教师资格认证、demand 需实名认证，
认证状态判断同时接受 approved 与 verified（与 certification.py 口径一致）。
"""

from __future__ import annotations

import uuid

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.edu_listing_status import EduListingStatus
from app.models.edu_listing import EduListing
from app.models.user import User
from app.models.user_identity_verification import UserIdentityVerification
from app.schemas.edu_listing import (
    EduListingCreate,
    EduListingItem,
    EduListingListResponse,
    EduListingUpdate,
)
from app.utils.timezone import booking_now

DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 50

# listing_type → 发布所需的认证类型（verification_type）
REQUIRED_CERTIFICATION: dict[str, str] = {
    "tutor": "education",
    "training": "teacher",
    "demand": "real_name",
}
CERTIFICATION_LABEL: dict[str, str] = {
    "education": "学历认证",
    "teacher": "教师资格认证",
    "real_name": "实名认证",
}
PASSED_CERT_STATUSES = ("approved", "verified")


def order_by_clauses(sort: str):
    if sort == "price_asc":
        return (EduListing.price.asc().nulls_last(), EduListing.created_at.desc(), EduListing.id.desc())
    if sort == "price_desc":
        return (EduListing.price.desc().nulls_last(), EduListing.created_at.desc(), EduListing.id.desc())
    return (EduListing.created_at.desc(), EduListing.id.desc())


async def _load_certification_map(
    db: AsyncSession, user_ids: set[uuid.UUID]
) -> dict[uuid.UUID, dict[str, bool]]:
    """批量查询用户的学历/教师资格认证是否通过。"""
    if not user_ids:
        return {}
    rows = (
        await db.execute(
            select(
                UserIdentityVerification.user_id,
                UserIdentityVerification.verification_type,
            ).where(
                UserIdentityVerification.user_id.in_(user_ids),
                UserIdentityVerification.verification_type.in_(("education", "teacher")),
                UserIdentityVerification.status.in_(PASSED_CERT_STATUSES),
            )
        )
    ).all()
    result: dict[uuid.UUID, dict[str, bool]] = {
        uid: {"education": False, "teacher": False} for uid in user_ids
    }
    for uid, vtype in rows:
        result[uid][vtype] = True
    return result


async def assemble_items(
    db: AsyncSession,
    listings: list[EduListing],
    *,
    with_certification: bool = False,
) -> list[EduListingItem]:
    """批量补齐发布者昵称/头像（及可选认证状态）并组装条目。"""
    if not listings:
        return []

    user_ids = {item.user_id for item in listings}
    users = (await db.execute(select(User).where(User.id.in_(user_ids)))).scalars().all()
    user_map: dict[uuid.UUID, User] = {u.id: u for u in users}

    cert_map: dict[uuid.UUID, dict[str, bool]] = {}
    if with_certification:
        cert_map = await _load_certification_map(db, user_ids)

    items: list[EduListingItem] = []
    for listing in listings:
        user = user_map.get(listing.user_id)
        cert = cert_map.get(listing.user_id, {})
        items.append(
            EduListingItem(
                id=listing.id,
                listing_type=listing.listing_type,
                title=listing.title,
                subject=listing.subject,
                teaching_mode=listing.teaching_mode,
                price=listing.price,
                price_unit=listing.price_unit,
                city_id=listing.city_id,
                area=listing.area,
                description=listing.description,
                images=listing.images,
                available_times=listing.available_times,
                status=listing.status,
                reject_reason=listing.reject_reason,
                view_count=listing.view_count,
                publisher_id=listing.user_id,
                publisher_nickname=user.nickname if user else None,
                publisher_avatar=user.avatar if user else None,
                publisher_phone=user.phone if user else None,
                publisher_education_verified=cert.get("education") if with_certification else None,
                publisher_teacher_verified=cert.get("teacher") if with_certification else None,
                created_at=listing.created_at,
            )
        )
    return items


async def list_edu_listings(
    db: AsyncSession,
    *,
    listing_type: str | None = None,
    subject: str | None = None,
    city_id: int | None = None,
    sort: str = "new",
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> EduListingListResponse:
    """综合广场列表：仅返回已通过信息，教与学混排。"""
    conditions: list = [EduListing.status == EduListingStatus.APPROVED.value]
    if listing_type:
        conditions.append(EduListing.listing_type == listing_type)
    if subject and subject.strip():
        conditions.append(EduListing.subject == subject.strip())
    if city_id:
        conditions.append(EduListing.city_id == city_id)

    total = (
        await db.execute(select(func.count()).select_from(EduListing).where(*conditions))
    ).scalar_one()
    result = await db.execute(
        select(EduListing)
        .where(*conditions)
        .order_by(*order_by_clauses(sort))
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = await assemble_items(db, list(result.scalars().all()), with_certification=True)
    return EduListingListResponse(items=items, total=total, page=page, page_size=page_size)


async def get_detail(db: AsyncSession, listing_id: int) -> EduListingItem:
    """供需信息详情：浏览数 +1，附带发布者认证状态。"""
    listing = await db.get(EduListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="供需信息不存在")

    listing.view_count = (listing.view_count or 0) + 1
    listing.updated_at = booking_now()
    await db.flush()

    return (await assemble_items(db, [listing], with_certification=True))[0]


async def list_mine(
    db: AsyncSession,
    user_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
) -> EduListingListResponse:
    """我发布的供需信息：全部状态，按创建时间倒序。"""
    conditions = [EduListing.user_id == user_id]
    total = (
        await db.execute(select(func.count()).select_from(EduListing).where(*conditions))
    ).scalar_one()
    result = await db.execute(
        select(EduListing)
        .where(*conditions)
        .order_by(EduListing.created_at.desc(), EduListing.id.desc())
        .offset((page - 1) * page_size)
        .limit(page_size)
    )
    items = await assemble_items(db, list(result.scalars().all()))
    return EduListingListResponse(items=items, total=total, page=page, page_size=page_size)


async def _ensure_certified(db: AsyncSession, user_id: uuid.UUID, listing_type: str) -> None:
    required = REQUIRED_CERTIFICATION.get(listing_type)
    if not required:
        return
    passed = (
        await db.execute(
            select(UserIdentityVerification.id).where(
                UserIdentityVerification.user_id == user_id,
                UserIdentityVerification.verification_type == required,
                UserIdentityVerification.status.in_(PASSED_CERT_STATUSES),
            )
        )
    ).first()
    if passed is None:
        label = CERTIFICATION_LABEL[required]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"发布该类信息需先完成{label}",
        )


async def create_edu_listing(
    db: AsyncSession, user_id: uuid.UUID, data: EduListingCreate
) -> EduListingItem:
    """发布供需信息：先做认证前置校验，通过后落库为 pending。"""
    await _ensure_certified(db, user_id, data.listing_type)

    listing = EduListing(
        user_id=user_id,
        listing_type=data.listing_type,
        title=data.title,
        subject=data.subject,
        teaching_mode=data.teaching_mode,
        price=data.price,
        price_unit=data.price_unit,
        city_id=data.city_id,
        area=data.area,
        description=data.description,
        images=data.images or None,
        available_times=data.available_times or None,
        status=EduListingStatus.PENDING.value,
        view_count=0,
    )
    db.add(listing)
    await db.flush()
    await db.refresh(listing)
    return (await assemble_items(db, [listing]))[0]


async def update_edu_listing(
    db: AsyncSession, listing_id: int, user_id: uuid.UUID, data: EduListingUpdate
) -> EduListingItem:
    """编辑供需信息：仅发布者本人可编辑，编辑后重置为 pending 重新审核。"""
    listing = await db.get(EduListing, listing_id)
    if listing is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="供需信息不存在")
    if listing.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="只能编辑自己发布的信息")

    update_data = data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(listing, field, value)

    if listing.status == EduListingStatus.REJECTED.value:
        listing.status = EduListingStatus.PENDING.value
        listing.reject_reason = None
    listing.updated_at = booking_now()

    await db.flush()
    await db.refresh(listing)
    return (await assemble_items(db, [listing]))[0]
