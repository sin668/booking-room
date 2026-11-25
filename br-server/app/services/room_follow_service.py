from __future__ import annotations

import uuid

from sqlalchemy import exists, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.edu_listing import EduListing
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.teacher_room import TeacherRoom
from app.schemas.room_follow import FollowedRoomListResponse, FollowedRoomResponse
from app.services.training_service import (
    _get_first_schedule_for_courses,
    _has_in_progress_fixed_schedule,
)


def _to_followed_room(
    room: StudyRoom,
    followed_at,
    city_name: str | None = None,
) -> FollowedRoomResponse:
    return FollowedRoomResponse(
        id=room.id,
        name=room.name,
        description=room.description,
        cover_image=room.cover_image,
        address=room.address,
        city_id=room.city_id,
        city_name=city_name,
        business_hours=room.business_hours,
        status=room.status,
        min_price=room.min_price,
        room_type=room.room_type,
        followed_at=followed_at,
    )


def _city_or_null_condition(city_id: int):
    """城市匹配；未设置城市的房间在任何城市过滤下都可见。"""
    return or_(StudyRoom.city_id == city_id, StudyRoom.city_id.is_(None))


def _to_followed_listing(listing: EduListing, followed_at) -> FollowedRoomResponse:
    images = listing.images or []
    return FollowedRoomResponse(
        id=listing.id,
        name=listing.title,
        description=listing.description or "",
        cover_image=images[0] if images else None,
        address=listing.area or "",
        city_id=listing.city_id,
        city_name=None,
        business_hours=None,
        status="active",
        min_price=listing.price or 0,
        room_type="listing",
        followed_at=followed_at,
    )


async def list_followed_rooms(
    db: AsyncSession,
    user_id: uuid.UUID,
    follow_type: str = "room",
    city_id: int | None = None,
) -> FollowedRoomListResponse:
    if follow_type == "listing":
        listing_filters = [
            RoomFollow.user_id == user_id,
            RoomFollow.follow_type == "listing",
            EduListing.status == "approved",
        ]
        if city_id is not None:
            listing_filters.append(
                or_(EduListing.city_id == city_id, EduListing.city_id.is_(None))
            )
        count = (
            await db.execute(
                select(func.count())
                .select_from(RoomFollow)
                .join(EduListing, RoomFollow.room_id == EduListing.id)
                .where(*listing_filters)
            )
        ).scalar_one()
        result = await db.execute(
            select(RoomFollow, EduListing)
            .join(EduListing, RoomFollow.room_id == EduListing.id)
            .where(*listing_filters)
            .order_by(RoomFollow.created_at.desc(), RoomFollow.id.desc())
        )
        items = [
            _to_followed_listing(listing, follow.created_at)
            for follow, listing in result.all()
        ]
        return FollowedRoomListResponse(items=items, total=count)

    if follow_type == "teacher":
        # Teacher follows: join with teachers table
        teacher_filters = [
            RoomFollow.user_id == user_id,
            RoomFollow.follow_type == "teacher",
        ]
        if city_id is not None:
            # 教师任一归属房间城市匹配即可见；无任何房间关联的教师始终可见
            has_city_room = exists(
                select(1)
                .select_from(TeacherRoom)
                .join(StudyRoom, TeacherRoom.room_id == StudyRoom.id)
                .where(
                    TeacherRoom.teacher_id == Teacher.id,
                    _city_or_null_condition(city_id),
                )
            )
            has_any_room = exists(
                select(1)
                .select_from(TeacherRoom)
                .where(TeacherRoom.teacher_id == Teacher.id)
            )
            teacher_filters.append(or_(has_city_room, ~has_any_room))

        count = (
            await db.execute(
                select(func.count())
                .select_from(RoomFollow)
                .join(Teacher, RoomFollow.room_id == Teacher.id)
                .where(*teacher_filters)
            )
        ).scalar_one()

        result = await db.execute(
            select(RoomFollow, Teacher)
            .join(Teacher, RoomFollow.room_id == Teacher.id)
            .where(*teacher_filters)
            .order_by(RoomFollow.created_at.desc(), RoomFollow.id.desc())
        )
        items = [
            FollowedRoomResponse(
                id=teacher.id,
                name=teacher.name,
                description=teacher.bio or "",
                cover_image=teacher.avatar,
                address="",
                city_id=None,
                city_name=None,
                business_hours=None,
                status="active",
                min_price=0,
                room_type="teacher",
                followed_at=follow.created_at,
            )
            for follow, teacher in result.all()
        ]
        return FollowedRoomListResponse(items=items, total=count)

    if follow_type == "course":
        # Course follows: join with courses table
        # 与 C 端其他课程页面口径一致：仅展示存在「进行中的固定班课」排课
        # (schedule_type=fixed, schedule_status=in_progress) 的关注课程
        course_filters = [
            RoomFollow.user_id == user_id,
            RoomFollow.follow_type == "course",
            Course.status == "active",
            _has_in_progress_fixed_schedule(),
        ]
        # city_id 条件引用 StudyRoom，count/列表都需显式 JOIN，否则隐式笛卡尔积放大 total
        count_stmt = (
            select(func.count())
            .select_from(RoomFollow)
            .join(Course, RoomFollow.room_id == Course.id)
            .where(*course_filters)
        )
        list_stmt = (
            select(RoomFollow, Course)
            .join(Course, RoomFollow.room_id == Course.id)
            .where(*course_filters)
            .order_by(RoomFollow.created_at.desc(), RoomFollow.id.desc())
        )
        if city_id is not None:
            city_cond = _city_or_null_condition(city_id)
            count_stmt = count_stmt.join(
                StudyRoom, Course.room_id == StudyRoom.id
            ).where(city_cond)
            list_stmt = list_stmt.join(
                StudyRoom, Course.room_id == StudyRoom.id
            ).where(city_cond)

        count = (await db.execute(count_stmt)).scalar_one()

        result = await db.execute(list_stmt)
        rows = result.all()
        schedule_map = await _get_first_schedule_for_courses(
            db, [course.id for _, course in rows]
        )
        items = [
            FollowedRoomResponse(
                id=course.id,
                name=course.name,
                description=course.description,
                cover_image=course.cover_image,
                address="",
                city_id=None,
                city_name=None,
                business_hours=None,
                status=course.status,
                min_price=schedule_map[course.id].price
                if schedule_map.get(course.id)
                else 0,
                room_type="course",
                followed_at=follow.created_at,
            )
            for follow, course in rows
        ]
        return FollowedRoomListResponse(items=items, total=count)

    room_filters = [
        RoomFollow.user_id == user_id,
        RoomFollow.follow_type == follow_type,
        StudyRoom.status == "open",
    ]
    if city_id is not None:
        room_filters.append(_city_or_null_condition(city_id))

    count = (
        await db.execute(
            select(func.count())
            .select_from(RoomFollow)
            .join(StudyRoom, RoomFollow.room_id == StudyRoom.id)
            .where(*room_filters)
        )
    ).scalar_one()

    result = await db.execute(
        select(RoomFollow, StudyRoom, City.name.label("city_name"))
        .join(StudyRoom, RoomFollow.room_id == StudyRoom.id)
        .outerjoin(City, StudyRoom.city_id == City.id)
        .where(*room_filters)
        .order_by(RoomFollow.created_at.desc(), RoomFollow.id.desc())
    )
    items = [
        _to_followed_room(room, follow.created_at, city_name)
        for follow, room, city_name in result.all()
    ]
    return FollowedRoomListResponse(items=items, total=count)


async def follow_room(
    db: AsyncSession,
    user_id: uuid.UUID,
    room_id: int,
    follow_type: str = "room",
) -> tuple[FollowedRoomResponse, bool]:
    if follow_type == "listing":
        listing = await db.get(EduListing, room_id)
        if listing is None or listing.status != "approved":
            raise ValueError(f"Listing {room_id} not found")
        follow = (
            await db.execute(
                select(RoomFollow).where(
                    RoomFollow.user_id == user_id,
                    RoomFollow.room_id == room_id,
                    RoomFollow.follow_type == follow_type,
                )
            )
        ).scalar_one_or_none()
        created = follow is None
        if follow is None:
            follow = RoomFollow(user_id=user_id, room_id=room_id, follow_type=follow_type)
            db.add(follow)
            await db.flush()
        await db.commit()
        await db.refresh(follow)
        return _to_followed_listing(listing, follow.created_at), created

    if follow_type == "teacher":
        # Validate against teachers table
        teacher = await db.get(Teacher, room_id)
        if teacher is None:
            raise ValueError(f"Teacher {room_id} not found")
        # Check for existing follow
        follow = (
            await db.execute(
                select(RoomFollow).where(
                    RoomFollow.user_id == user_id,
                    RoomFollow.room_id == room_id,
                    RoomFollow.follow_type == follow_type,
                )
            )
        ).scalar_one_or_none()
        created = follow is None
        if follow is None:
            follow = RoomFollow(user_id=user_id, room_id=room_id, follow_type=follow_type)
            db.add(follow)
            await db.flush()
        await db.commit()
        await db.refresh(follow)
        return FollowedRoomResponse(
            id=teacher.id,
            name=teacher.name,
            description=teacher.bio or "",
            cover_image=teacher.avatar,
            address="",
            status="active",
            min_price=0,
            room_type="teacher",
            followed_at=follow.created_at,
        ), created

    if follow_type == "course":
        # Validate against courses table
        course = await db.get(Course, room_id)
        if course is None or course.status != "active":
            raise ValueError(f"Course {room_id} not found")
        # 一门课程可能有多条排课，取第一条进行中的固定班课，避免多行结果抛错
        schedule_map = await _get_first_schedule_for_courses(db, [course.id])
        schedule = schedule_map.get(course.id)
        # For course type, create follow record and return basic response
        follow = (
            await db.execute(
                select(RoomFollow).where(
                    RoomFollow.user_id == user_id,
                    RoomFollow.room_id == room_id,
                    RoomFollow.follow_type == follow_type,
                )
            )
        ).scalar_one_or_none()
        created = follow is None
        if follow is None:
            follow = RoomFollow(user_id=user_id, room_id=room_id, follow_type=follow_type)
            db.add(follow)
            await db.flush()
        await db.commit()
        await db.refresh(follow)
        return FollowedRoomResponse(
            id=course.id,
            name=course.name,
            description=course.description,
            cover_image=course.cover_image,
            address="",
            status=course.status,
            min_price=schedule.price if schedule else 0,
            room_type="course",
            followed_at=follow.created_at,
        ), created

    # Default: room type — validate against study_rooms table
    row = (
        await db.execute(
            select(StudyRoom, City.name.label("city_name"))
            .outerjoin(City, StudyRoom.city_id == City.id)
            .where(StudyRoom.id == room_id, StudyRoom.status == "open")
        )
    ).one_or_none()
    if row is None:
        raise ValueError(f"Room {room_id} not found")
    room, city_name = row

    follow = (
        await db.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == user_id,
                RoomFollow.room_id == room_id,
                RoomFollow.follow_type == follow_type,
            )
        )
    ).scalar_one_or_none()
    created = follow is None
    if follow is None:
        follow = RoomFollow(user_id=user_id, room_id=room_id, follow_type=follow_type)
        db.add(follow)
        await db.flush()

    await db.commit()
    await db.refresh(follow)
    return _to_followed_room(room, follow.created_at, city_name), created


async def unfollow_room(
    db: AsyncSession,
    user_id: uuid.UUID,
    room_id: int,
    follow_type: str = "room",
) -> None:
    follow = (
        await db.execute(
            select(RoomFollow).where(
                RoomFollow.user_id == user_id,
                RoomFollow.room_id == room_id,
                RoomFollow.follow_type == follow_type,
            )
        )
    ).scalar_one_or_none()
    if follow is not None:
        await db.delete(follow)
        await db.commit()
