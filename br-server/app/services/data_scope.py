"""管理员数据权限：内容归属记录与可见性过滤。

规则（用户已确认）：
- 非超管可见「自己创建 + 创建人为空（存量/legacy）+ 创建人当前为超管」的数据；超管不过滤。
- 超管创建的数据对非超管只读：写操作 403，列表/详情带 readonly 标志。
- 判定一律用 is_super_admin；legacy X-Admin-Token 的 admin_id 为 UUID(int=0)，不落库。
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from fastapi import HTTPException
from sqlalchemy import and_, or_, select

if TYPE_CHECKING:
    from app.api.dependencies import AdminContext

READONLY_DETAIL = "超级管理员创建的数据仅可查看，不能修改"


def creator_id(context: AdminContext | None) -> uuid.UUID | None:
    if context is None or context.admin_id.int == 0:
        return None
    return context.admin_id


def scope_condition(model, viewer: AdminContext | None):
    """非超管的可见性条件；None 表示不过滤。"""
    if _unrestricted(viewer):
        return None
    return _visible_creator_condition(model.created_by, viewer)


def _visible_creator_condition(column, viewer: AdminContext):
    from app.models.user import User

    return or_(
        column.is_(None),
        column == viewer.admin_id,
        column.in_(select(User.id).where(User.user_type == "super-admin")),
    )


def _unrestricted(viewer: AdminContext | None) -> bool:
    return viewer is None or viewer.is_super_admin or viewer.admin_id.int == 0


async def readonly_creators(db, creator_ids, viewer: AdminContext | None) -> set[uuid.UUID]:
    """给定创建人中当前为超管的 id 子集；不受限的查看者返回空集。"""
    ids = {cid for cid in creator_ids if cid is not None}
    if not ids or _unrestricted(viewer):
        return set()
    from app.models.user import User

    rows = await db.execute(
        select(User.id).where(User.id.in_(ids), User.user_type == "super-admin")
    )
    return set(rows.scalars())


async def ensure_writable(db, model, obj_id, viewer: AdminContext | None) -> None:
    """非超管写「创建人当前为超管」的内容时抛 403；目标不存在/存量/他人数据不在此拦截。"""
    if _unrestricted(viewer):
        return
    created_by = (
        await db.execute(select(model.created_by).where(model.id == obj_id))
    ).scalar_one_or_none()
    if created_by is not None and created_by in await readonly_creators(db, [created_by], viewer):
        raise HTTPException(status_code=403, detail=READONLY_DETAIL)


async def ensure_seat_writable(db, seat_id, viewer: AdminContext | None) -> None:
    if _unrestricted(viewer):
        return
    from app.models.seat import Seat
    from app.models.study_room import StudyRoom

    room_id = (
        await db.execute(select(Seat.room_id).where(Seat.id == seat_id))
    ).scalar_one_or_none()
    if room_id is not None:
        await ensure_writable(db, StudyRoom, room_id, viewer)


async def ensure_booking_writable(db, booking_id, viewer: AdminContext | None) -> None:
    if _unrestricted(viewer):
        return
    from app.models.booking import Booking
    from app.models.course import Course
    from app.models.study_room import StudyRoom

    row = (
        await db.execute(
            select(Booking.course_id, Booking.room_id).where(Booking.id == booking_id)
        )
    ).first()
    if row is None:
        return
    course_id, room_id = row
    if course_id is not None:
        await ensure_writable(db, Course, course_id, viewer)
    elif room_id is not None:
        await ensure_writable(db, StudyRoom, room_id, viewer)


async def ensure_review_writable(db, review_id, viewer: AdminContext | None) -> None:
    if _unrestricted(viewer):
        return
    from app.models.course import Course
    from app.models.review import Review

    row = (
        await db.execute(
            select(Review.course_id, Review.booking_id).where(Review.id == review_id)
        )
    ).first()
    if row is None:
        return
    course_id, booking_id = row
    if course_id is not None:
        await ensure_writable(db, Course, course_id, viewer)
    elif booking_id is not None:
        await ensure_booking_writable(db, booking_id, viewer)


def booking_scope_condition(viewer: AdminContext | None):
    """预约随关联内容归属：课程订单随课程创建人，座位订单随自习室创建人。

    调用方需先 outerjoin Course（Booking.course_id）与 StudyRoom（Booking.room_id）。
    """
    if _unrestricted(viewer):
        return None
    from app.models.booking import Booking
    from app.models.course import Course
    from app.models.study_room import StudyRoom

    return or_(
        and_(
            Booking.course_id.is_not(None),
            _visible_creator_condition(Course.created_by, viewer),
        ),
        and_(
            Booking.course_id.is_(None),
            _visible_creator_condition(StudyRoom.created_by, viewer),
        ),
    )


def review_scope_condition(viewer: AdminContext | None):
    """评价随关联内容归属：有课程随课程创建人，否则随订单所属自习室创建人。

    调用方需先 outerjoin Course（Review.course_id）、Booking（Review.booking_id）
    与 StudyRoom（Booking.room_id）。
    """
    if _unrestricted(viewer):
        return None
    from app.models.booking import Booking
    from app.models.course import Course
    from app.models.review import Review
    from app.models.study_room import StudyRoom

    return or_(
        and_(
            Review.course_id.is_not(None),
            _visible_creator_condition(Course.created_by, viewer),
        ),
        and_(
            Review.course_id.is_(None),
            _visible_creator_condition(StudyRoom.created_by, viewer),
        ),
    )