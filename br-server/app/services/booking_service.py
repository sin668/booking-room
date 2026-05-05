import uuid
from datetime import date, time
from decimal import Decimal

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.booking import (
    BookingCreate,
    BookingListResponse,
    BookingResponse,
    RoomBrief,
    SeatBrief,
)

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


class BookingError(ValueError):
    """Base exception for booking operations."""


class SeatNotFoundError(BookingError):
    pass


class SeatMaintenanceError(BookingError):
    pass


class BookingConflictError(BookingError):
    pass


class InvalidTimeRangeError(BookingError):
    pass


class BookingNotFoundError(BookingError):
    pass


class BookingAlreadyCancelledError(BookingError):
    pass


def _calculate_hours(start_time: time, end_time: time) -> float:
    start_seconds = start_time.hour * 3600 + start_time.minute * 60 + start_time.second
    end_seconds = end_time.hour * 3600 + end_time.minute * 60 + end_time.second
    return (end_seconds - start_seconds) / 3600.0


def _build_booking_response(booking: Booking, seat: Seat, room: StudyRoom) -> BookingResponse:
    return BookingResponse(
        id=booking.id,
        seat_id=booking.seat_id,
        user_id=booking.user_id,
        room_id=booking.room_id,
        date=booking.date,
        start_time=booking.start_time,
        end_time=booking.end_time,
        status=booking.status,
        total_price=booking.total_price,
        created_at=booking.created_at,
        seat=SeatBrief.model_validate(seat),
        room=RoomBrief.model_validate(room),
    )


async def create_booking(
    db: AsyncSession, user_id: uuid.UUID, data: BookingCreate
) -> BookingResponse:
    """Create a booking with conflict detection.

    Note: For MVP, conflict detection uses a SELECT without FOR UPDATE.
    Under high concurrency, a database-level unique constraint on
    (seat_id, date, start_time, end_time) should be added as a safety net.
    See proposal.md risks section for details.
    """
    seat_result = await db.execute(select(Seat).where(Seat.id == data.seat_id))
    seat = seat_result.scalar_one_or_none()

    if seat is None:
        raise SeatNotFoundError("座位不存在")

    if seat.status == "maintenance":
        raise SeatMaintenanceError("该座位正在维护中")

    if data.end_time <= data.start_time:
        raise InvalidTimeRangeError("结束时间必须晚于开始时间")

    conflict = await db.execute(
        select(Booking).where(
            Booking.seat_id == data.seat_id,
            Booking.date == data.date,
            Booking.start_time < data.end_time,
            Booking.end_time > data.start_time,
            Booking.status != "cancelled",
        )
    )
    if conflict.scalars().first() is not None:
        raise BookingConflictError("该座位该时段已被预约")

    room_result = await db.execute(select(StudyRoom).where(StudyRoom.id == seat.room_id))
    room = room_result.scalar_one()

    hours = _calculate_hours(data.start_time, data.end_time)
    total_price = Decimal(str(seat.price_per_hour)) * Decimal(str(round(hours, 2)))

    booking = Booking(
        seat_id=data.seat_id,
        user_id=str(user_id),
        room_id=seat.room_id,
        date=data.date,
        start_time=data.start_time,
        end_time=data.end_time,
        status="confirmed",
        total_price=total_price,
    )
    db.add(booking)
    await db.flush()

    return _build_booking_response(booking, seat, room)


async def list_bookings(
    db: AsyncSession,
    user_id: uuid.UUID,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
) -> BookingListResponse:
    """List bookings for the current user with pagination."""
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    conditions = [Booking.user_id == str(user_id)]
    if status is not None:
        conditions.append(Booking.status == status)

    where_clause = and_(*conditions)

    count_result = await db.execute(
        select(func.count()).select_from(Booking).where(where_clause)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Booking)
        .where(where_clause)
        .order_by(Booking.id.desc())
        .offset(offset)
        .limit(page_size)
    )
    bookings = result.scalars().all()

    seat_ids = {b.seat_id for b in bookings}
    room_ids = {b.room_id for b in bookings}

    seats_result = await db.execute(select(Seat).where(Seat.id.in_(seat_ids))) if seat_ids else None
    rooms_result = await db.execute(select(StudyRoom).where(StudyRoom.id.in_(room_ids))) if room_ids else None
    seat_map = {s.id: s for s in seats_result.scalars().all()} if seats_result else {}
    room_map = {r.id: r for r in rooms_result.scalars().all()} if rooms_result else {}

    items: list[BookingResponse] = []
    for b in bookings:
        items.append(_build_booking_response(b, seat_map[b.seat_id], room_map[b.room_id]))

    return BookingListResponse(
        items=items,
        total=total,
        page=page,
        page_size=page_size,
    )


async def get_booking(
    db: AsyncSession, booking_id: int, user_id: uuid.UUID
) -> BookingResponse:
    """Get a booking detail. Only own bookings are visible."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None or booking.user_id != str(user_id):
        raise BookingNotFoundError("预约不存在")

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()

    return _build_booking_response(booking, seat, room)


async def cancel_booking(
    db: AsyncSession, booking_id: int, user_id: uuid.UUID
) -> BookingResponse:
    """Cancel own booking. Only confirmed bookings can be cancelled."""
    result = await db.execute(select(Booking).where(Booking.id == booking_id))
    booking = result.scalar_one_or_none()

    if booking is None or booking.user_id != str(user_id):
        raise BookingNotFoundError("预约不存在")

    if booking.status != "confirmed":
        raise BookingAlreadyCancelledError("该预约已取消")

    booking.status = "cancelled"
    await db.flush()

    seat = (await db.execute(select(Seat).where(Seat.id == booking.seat_id))).scalar_one()
    room = (await db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))).scalar_one()

    return _build_booking_response(booking, seat, room)
