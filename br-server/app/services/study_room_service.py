from sqlalchemy import func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.im import to_im_user_id
from app.domain.booking_status import BookingStatus
from app.models.booking import Booking
from app.models.city import City
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.study_room import (
    RoomAdminListResponse,
    RoomAdminResponse,
    StudyRoomListResponse,
    StudyRoomResponse,
)
from app.services.data_scope import readonly_creators, scope_condition
from app.services.tencent_map_service import geocode_address

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


async def _resolve_city_name(db: AsyncSession, city_id: int | None) -> str | None:
    if city_id is None:
        return None
    result = await db.execute(select(City.name).where(City.id == city_id))
    return result.scalar_one_or_none()


def _has_coordinates(data: dict) -> bool:
    return data.get("latitude") is not None and data.get("longitude") is not None


async def _apply_geocode_fallback(db: AsyncSession, data: dict) -> None:
    """Fill missing coordinates from the address; never raises."""
    if _has_coordinates(data):
        return
    address = (data.get("address") or "").strip()
    if not address:
        return
    city_name = await _resolve_city_name(db, data.get("city_id"))
    coordinates = await geocode_address(address, city_name)
    if coordinates:
        data["latitude"], data["longitude"] = coordinates


async def list_study_rooms(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    city_id: int | None = None,
    room_type: str | None = None,
    keyword: str | None = None,
) -> StudyRoomListResponse:
    """Return paginated list of open study rooms."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    filters = [StudyRoom.status == "open"]
    if city_id is not None:
        filters.append(or_(StudyRoom.city_id == city_id, StudyRoom.city_id.is_(None)))
    if room_type is not None:
        filters.append(StudyRoom.room_type == room_type)
    else:
        filters.append(StudyRoom.room_type.in_(["study", "comprehensive"]))
    if keyword:
        filters.append(or_(
            StudyRoom.name.ilike(f"%{keyword}%"),
            StudyRoom.address.ilike(f"%{keyword}%"),
        ))

    count_result = await db.execute(
        select(func.count()).select_from(StudyRoom).where(*filters)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(StudyRoom, City.name.label("city_name"))
        .outerjoin(City, StudyRoom.city_id == City.id)
        .where(*filters)
        .order_by(StudyRoom.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    items = []
    for room, city_name in result.all():
        item = StudyRoomResponse.model_validate(room)
        item.city_name = city_name
        items.append(item)

    return StudyRoomListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_study_room(db: AsyncSession, room_id: int) -> StudyRoomResponse:
    """Return an open study room by ID."""
    result = await db.execute(
        select(StudyRoom, City.name.label("city_name"))
        .outerjoin(City, StudyRoom.city_id == City.id)
        .where(StudyRoom.id == room_id, StudyRoom.status == "open")
    )
    row = result.one_or_none()
    if row is None:
        raise ValueError(f"Room {room_id} not found")
    room, city_name = row
    item = StudyRoomResponse.model_validate(room)
    item.city_name = city_name
    item.creator_username = to_im_user_id(room.created_by) if room.created_by else None
    return item


async def admin_list_rooms(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
    room_type: str | None = None,
    city_id: int | None = None,
    viewer=None,
) -> RoomAdminListResponse:
    """Return paginated list of all rooms, optionally filtered by status/type/city."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    filters = []
    condition = scope_condition(StudyRoom, viewer)
    if condition is not None:
        filters.append(condition)
    if status is not None:
        filters.append(StudyRoom.status == status)
    if room_type is not None:
        filters.append(StudyRoom.room_type == room_type)
    if city_id is not None:
        filters.append(StudyRoom.city_id == city_id)

    count_query = select(func.count()).select_from(StudyRoom)
    if filters:
        count_query = count_query.where(*filters)
    total = (await db.execute(count_query)).scalar_one()

    query = (
        select(StudyRoom, City.name.label("city_name"))
        .outerjoin(City, StudyRoom.city_id == City.id)
        .order_by(StudyRoom.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    if filters:
        query = query.where(*filters)

    result = await db.execute(query)
    rows = result.all()
    ro_creators = await readonly_creators(db, [room.created_by for room, _ in rows], viewer)
    items = []
    for room, city_name in rows:
        item = RoomAdminResponse.model_validate(room)
        item.city_name = city_name
        item.readonly = room.created_by in ro_creators
        items.append(item)

    return RoomAdminListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def admin_get_room(db: AsyncSession, room_id: int, viewer=None) -> RoomAdminResponse:
    """Get room by ID with seat counts."""
    stmt = (
        select(StudyRoom, City.name.label("city_name"))
        .outerjoin(City, StudyRoom.city_id == City.id)
        .where(StudyRoom.id == room_id)
    )
    condition = scope_condition(StudyRoom, viewer)
    if condition is not None:
        stmt = stmt.where(condition)
    result = await db.execute(stmt)
    row = result.one_or_none()
    if row is None:
        raise ValueError(f"Room {room_id} not found")
    room, city_name = row

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
        city_name=city_name,
        seat_count=seat_count,
        available_seat_count=available_seat_count,
        readonly=bool(await readonly_creators(db, [room.created_by], viewer)),
    )


async def create_room(db: AsyncSession, data: dict, created_by=None) -> RoomAdminResponse:
    """Create a new study room."""
    data = dict(data)
    await _apply_geocode_fallback(db, data)
    room = StudyRoom(**data, created_by=created_by)
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

    data = dict(data)
    if "address" in data:
        await _apply_geocode_fallback(db, data)

    for key, value in data.items():
        # 坐标允许显式传 null 清除；其余字段沿用“忽略 None”的既有语义
        if key in ("latitude", "longitude") or value is not None:
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
                Booking.room_id == room_id, Booking.status == BookingStatus.IN_PROGRESS.value
            )
        )
    ).scalar_one()

    if active_count > 0:
        raise ValueError("该学习室存在活跃预约，无法删除")

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
