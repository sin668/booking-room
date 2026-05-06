from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.study_room import (
    RoomAdminListResponse,
    RoomAdminResponse,
    StudyRoomListResponse,
    StudyRoomResponse,
)

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


async def list_study_rooms(
    db: AsyncSession, page: int = 1, page_size: int = DEFAULT_PAGE_SIZE
) -> StudyRoomListResponse:
    """Return paginated list of open study rooms."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    count_result = await db.execute(
        select(func.count()).select_from(StudyRoom).where(StudyRoom.status == "open")
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(StudyRoom)
        .where(StudyRoom.status == "open")
        .order_by(StudyRoom.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    items = [StudyRoomResponse.model_validate(room) for room in result.scalars().all()]

    return StudyRoomListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def admin_list_rooms(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
) -> RoomAdminListResponse:
    """Return paginated list of all rooms, optionally filtered by status."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    query = select(StudyRoom)
    count_query = select(func.count()).select_from(StudyRoom)
    if status is not None:
        query = query.where(StudyRoom.status == status)
        count_query = count_query.where(StudyRoom.status == status)

    total = (await db.execute(count_query)).scalar_one()

    result = await db.execute(
        query.order_by(StudyRoom.id.asc()).offset(offset).limit(page_size)
    )
    items = [RoomAdminResponse.model_validate(room) for room in result.scalars().all()]

    return RoomAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def admin_get_room(db: AsyncSession, room_id: int) -> RoomAdminResponse:
    """Get room by ID with seat counts."""
    result = await db.execute(
        select(StudyRoom).where(StudyRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise ValueError(f"Room {room_id} not found")

    seat_count = (
        await db.execute(
            select(func.count()).where(Seat.room_id == room_id)
        )
    ).scalar_one()

    available_seat_count = (
        await db.execute(
            select(func.count()).where(
                Seat.room_id == room_id, Seat.status == "available"
            )
        )
    ).scalar_one()

    return RoomAdminResponse(
        **{c.name: getattr(room, c.name) for c in room.__table__.columns},
        seat_count=seat_count,
        available_seat_count=available_seat_count,
    )


async def create_room(db: AsyncSession, data: dict) -> RoomAdminResponse:
    """Create a new study room."""
    room = StudyRoom(**data)
    db.add(room)
    await db.commit()
    await db.refresh(room)
    return RoomAdminResponse.model_validate(room)


async def update_room(
    db: AsyncSession, room_id: int, data: dict
) -> RoomAdminResponse:
    """Update an existing study room."""
    result = await db.execute(
        select(StudyRoom).where(StudyRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise ValueError(f"Room {room_id} not found")

    for key, value in data.items():
        if value is not None:
            setattr(room, key, value)

    await db.commit()
    await db.refresh(room)
    return RoomAdminResponse.model_validate(room)


async def delete_room(db: AsyncSession, room_id: int) -> None:
    """Delete a study room if it has no active bookings."""
    result = await db.execute(
        select(StudyRoom).where(StudyRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise ValueError(f"Room {room_id} not found")

    active_count = (
        await db.execute(
            select(func.count()).where(
                Booking.room_id == room_id, Booking.status == "confirmed"
            )
        )
    ).scalar_one()

    if active_count > 0:
        raise ValueError("该自习室存在活跃预约，无法删除")

    await db.delete(room)
    await db.commit()


async def toggle_room_status(
    db: AsyncSession, room_id: int, new_status: str
) -> RoomAdminResponse:
    """Toggle a room's open/closed status."""
    result = await db.execute(
        select(StudyRoom).where(StudyRoom.id == room_id)
    )
    room = result.scalar_one_or_none()
    if room is None:
        raise ValueError(f"Room {room_id} not found")

    room.status = new_status
    await db.commit()
    await db.refresh(room)
    return RoomAdminResponse.model_validate(room)
