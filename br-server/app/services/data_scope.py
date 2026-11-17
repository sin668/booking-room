"""管理员数据权限：内容归属记录与可见性过滤。

规则（用户已确认）：
- 非超管可见「自己创建 + 创建人为空（存量/legacy）」的数据；超管不过滤。
- 判定一律用 is_super_admin；legacy X-Admin-Token 的 admin_id 为 UUID(int=0)，不落库。
"""
from __future__ import annotations

import uuid
from typing import TYPE_CHECKING

from sqlalchemy import and_, or_

if TYPE_CHECKING:
    from app.api.dependencies import AdminContext


def creator_id(context: AdminContext | None) -> uuid.UUID | None:
    if context is None or context.admin_id.int == 0:
        return None
    return context.admin_id


def scope_condition(model, viewer: AdminContext | None):
    """非超管的可见性条件；None 表示不过滤。"""
    if _unrestricted(viewer):
        return None
    return or_(model.created_by.is_(None), model.created_by == viewer.admin_id)


def _unrestricted(viewer: AdminContext | None) -> bool:
    return viewer is None or viewer.is_super_admin or viewer.admin_id.int == 0


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
            or_(Course.created_by.is_(None), Course.created_by == viewer.admin_id),
        ),
        and_(
            Booking.course_id.is_(None),
            or_(StudyRoom.created_by.is_(None), StudyRoom.created_by == viewer.admin_id),
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
            or_(Course.created_by.is_(None), Course.created_by == viewer.admin_id),
        ),
        and_(
            Review.course_id.is_(None),
            or_(StudyRoom.created_by.is_(None), StudyRoom.created_by == viewer.admin_id),
        ),
    )