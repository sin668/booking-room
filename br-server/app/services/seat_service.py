from datetime import date, time

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.seat import SeatResponse, SeatWithAvailabilityResponse


async def _room_exists(db: AsyncSession, room_id: int) -> bool:
    result = await db.execute(select(StudyRoom.id).where(StudyRoom.id == room_id))
    return result.scalar_one_or_none() is not None


async def _get_booked_seat_ids(
    db: AsyncSession,
    seat_ids: list[int],
    target_date: date,
    start_time: time,
    end_time: time,
) -> set[int]:
    """Return set of seat_ids that have overlapping confirmed bookings."""
    if not seat_ids:
        return set()
    result = await db.execute(
        select(Booking.seat_id).where(
            Booking.seat_id.in_(seat_ids),
            Booking.date == target_date,
            Booking.start_time < end_time,
            Booking.end_time > start_time,
            Booking.status != "cancelled",
        )
    )
    return {row[0] for row in result.all()}


async def list_seats(
    db: AsyncSession,
    room_id: int,
    target_date: date | None = None,
    start_time: time | None = None,
    end_time: time | None = None,
) -> list[SeatResponse] | list[SeatWithAvailabilityResponse]:
    if not await _room_exists(db, room_id):
        raise ValueError(f"Room {room_id} not found")

    result = await db.execute(
        select(Seat).where(Seat.room_id == room_id).order_by(Seat.id.asc())
    )
    seats = result.scalars().all()

    with_availability = target_date is not None and start_time is not None and end_time is not None

    if not with_availability:
        return [SeatResponse.model_validate(s) for s in seats]

    booked_ids = await _get_booked_seat_ids(db, [s.id for s in seats], target_date, start_time, end_time)

    items: list[SeatWithAvailabilityResponse] = []
    for s in seats:
        base = SeatResponse.model_validate(s)
        is_available = base.status != "maintenance" and s.id not in booked_ids
        items.append(SeatWithAvailabilityResponse(**base.model_dump(), is_available=is_available))
    return items
