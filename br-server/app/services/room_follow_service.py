from __future__ import annotations

import uuid

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
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
        followed_at=followed_at,
    )


async def list_followed_rooms(
    db: AsyncSession,
    user_id: uuid.UUID,
    follow_type: str = "room",
) -> FollowedRoomListResponse:
    # Current phase: course type returns empty list
    if follow_type == "course":
        return FollowedRoomListResponse(items=[], total=0)

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
    if follow_type == "course":
        # Validate against courses table
        row = (
            await db.execute(
                select(Course).where(Course.id == room_id, Course.status == "active")
            )
        ).scalar_one_or_none()
        if row is None:
            raise ValueError(f"Course {room_id} not found")
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
            id=row.id,
            name=row.name,
            description=row.description,
            cover_image=row.cover_image,
            address="",
            status=row.status,
            min_price=row.price,
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
