from __future__ import annotations

import uuid

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.course_schedule import CourseSchedule
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.schemas.room_follow import FollowedRoomListResponse, FollowedRoomResponse


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


async def list_followed_rooms(
    db: AsyncSession,
    user_id: uuid.UUID,
    follow_type: str = "room",
) -> FollowedRoomListResponse:
    if follow_type == "teacher":
        # Teacher follows: join with teachers table
        count = (
            await db.execute(
                select(func.count())
                .select_from(RoomFollow)
                .join(Teacher, RoomFollow.room_id == Teacher.id)
                .where(
                    RoomFollow.user_id == user_id,
                    RoomFollow.follow_type == "teacher",
                )
            )
        ).scalar_one()

        result = await db.execute(
            select(RoomFollow, Teacher)
            .join(Teacher, RoomFollow.room_id == Teacher.id)
            .where(
                RoomFollow.user_id == user_id,
                RoomFollow.follow_type == "teacher",
            )
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
        # 只关联“进行中的固定班课”排课（schedule_type=fixed, schedule_status=in_progress），
        # 与 br-app 其他课程页面过滤口径一致；无进行中排课的课程仍展示但无排课数据
        count = (
            await db.execute(
                select(func.count())
                .select_from(RoomFollow)
                .join(Course, RoomFollow.room_id == Course.id)
                .where(
                    RoomFollow.user_id == user_id,
                    RoomFollow.follow_type == "course",
                    Course.status == "active",
                )
            )
        ).scalar_one()

        result = await db.execute(
            select(RoomFollow, Course, CourseSchedule)
            .join(Course, RoomFollow.room_id == Course.id)
            .outerjoin(
                CourseSchedule,
                and_(
                    Course.id == CourseSchedule.course_id,
                    CourseSchedule.schedule_type == "fixed",
                    CourseSchedule.schedule_status == "in_progress",
                ),
            )
            .where(
                RoomFollow.user_id == user_id,
                RoomFollow.follow_type == "course",
                Course.status == "active",
            )
            .order_by(RoomFollow.created_at.desc(), RoomFollow.id.desc())
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
                min_price=schedule.price if schedule else 0,
                room_type="course",
                followed_at=follow.created_at,
            )
            for follow, course, schedule in result.all()
        ]
        return FollowedRoomListResponse(items=items, total=count)

    count = (
        await db.execute(
            select(func.count())
            .select_from(RoomFollow)
            .join(StudyRoom, RoomFollow.room_id == StudyRoom.id)
            .where(
                RoomFollow.user_id == user_id,
                RoomFollow.follow_type == follow_type,
                StudyRoom.status == "open",
            )
        )
    ).scalar_one()

    result = await db.execute(
        select(RoomFollow, StudyRoom, City.name.label("city_name"))
        .join(StudyRoom, RoomFollow.room_id == StudyRoom.id)
        .outerjoin(City, StudyRoom.city_id == City.id)
        .where(
            RoomFollow.user_id == user_id,
            RoomFollow.follow_type == follow_type,
            StudyRoom.status == "open",
        )
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
        row = (
            await db.execute(
                select(Course, CourseSchedule)
                .outerjoin(CourseSchedule, Course.id == CourseSchedule.course_id)
                .where(Course.id == room_id, Course.status == "active")
            )
        ).one_or_none()
        if row is None:
            raise ValueError(f"Course {room_id} not found")
        course, schedule = row
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
