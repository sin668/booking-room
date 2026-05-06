from datetime import date, time

from sqlalchemy import and_, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.schemas.seat import SeatAdminResponse, SeatResponse, SeatWithAvailabilityResponse


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


# ---- Admin functions ----


async def admin_list_seats(
    db: AsyncSession,
    room_id: int,
    zone: str | None = None,
    status: str | None = None,
) -> list[SeatAdminResponse]:
    if not await _room_exists(db, room_id):
        raise ValueError(f"Room {room_id} not found")

    stmt = select(Seat).where(Seat.room_id == room_id)
    if zone is not None:
        stmt = stmt.where(Seat.zone == zone)
    if status is not None:
        stmt = stmt.where(Seat.status == status)
    stmt = stmt.order_by(Seat.id.asc())

    result = await db.execute(stmt)
    seats = result.scalars().all()
    return [SeatAdminResponse.model_validate(s) for s in seats]


async def admin_get_seat(db: AsyncSession, seat_id: int) -> SeatAdminResponse:
    stmt = select(Seat, StudyRoom.name).join(StudyRoom, Seat.room_id == StudyRoom.id).where(Seat.id == seat_id)
    result = await db.execute(stmt)
    row = result.one_or_none()
    if row is None:
        raise ValueError(f"Seat {seat_id} not found")
    seat, room_name = row
    resp = SeatAdminResponse.model_validate(seat)
    return resp.model_copy(update={"room_name": room_name})


async def create_seat(db: AsyncSession, room_id: int, data: dict) -> SeatAdminResponse:
    if not await _room_exists(db, room_id):
        raise ValueError(f"Room {room_id} not found")

    existing = await db.execute(
        select(Seat.id).where(Seat.room_id == room_id, Seat.seat_number == data["seat_number"])
    )
    if existing.scalar_one_or_none() is not None:
        raise ValueError("该房间已存在相同编号的座位")

    room_result = await db.execute(select(StudyRoom.name).where(StudyRoom.id == room_id))
    room_name = room_result.scalar_one()

    seat = Seat(room_id=room_id, **data)
    db.add(seat)
    await db.commit()
    await db.refresh(seat)
    resp = SeatAdminResponse.model_validate(seat)
    return resp.model_copy(update={"room_name": room_name})


async def bulk_create_seats(
    db: AsyncSession,
    room_id: int,
    zone_configs: list[dict],
) -> int:
    if not await _room_exists(db, room_id):
        raise ValueError(f"Room {room_id} not found")

    if not zone_configs:
        return 0

    # Build all seats and collect seat_numbers
    all_seat_data: list[dict] = []
    all_new_numbers: list[str] = []
    for config in zone_configs:
        prefix = config["prefix"]
        start = config["start_number"]
        num = 0
        for r in range(1, config["rows"] + 1):
            for c in range(1, config["cols"] + 1):
                seat_number = f"{prefix}-{start + num:02d}"
                all_seat_data.append({
                    "seat_number": seat_number,
                    "zone": config["zone"],
                    "row": r,
                    "col": c,
                    "price_per_hour": config["price_per_hour"],
                    "floor": config["floor"],
                    "position": None,
                })
                all_new_numbers.append(seat_number)
                num += 1

    # Check for duplicates within the new batch
    seen: set[str] = set()
    batch_dupes: list[str] = []
    for sn in all_new_numbers:
        if sn in seen:
            batch_dupes.append(sn)
        seen.add(sn)

    # Check for conflicts with existing seats
    existing_result = await db.execute(
        select(Seat.seat_number).where(
            Seat.room_id == room_id, Seat.seat_number.in_(all_new_numbers)
        )
    )
    db_conflicts = {row[0] for row in existing_result.all()}

    all_conflicts = sorted(set(batch_dupes) | db_conflicts)
    if all_conflicts:
        raise ValueError(f"以下座位编号已存在: {', '.join(all_conflicts)}")

    seat_objects = [Seat(room_id=room_id, **d) for d in all_seat_data]
    db.add_all(seat_objects)
    await db.commit()
    return len(seat_objects)


async def update_seat(db: AsyncSession, seat_id: int, data: dict) -> SeatAdminResponse:
    result = await db.execute(select(Seat).where(Seat.id == seat_id))
    seat = result.scalar_one_or_none()
    if seat is None:
        raise ValueError(f"Seat {seat_id} not found")

    if "seat_number" in data and data["seat_number"] is not None and data["seat_number"] != seat.seat_number:
        existing = await db.execute(
            select(Seat.id).where(Seat.room_id == seat.room_id, Seat.seat_number == data["seat_number"])
        )
        if existing.scalar_one_or_none() is not None:
            raise ValueError("该房间已存在相同编号的座位")

    for key, value in data.items():
        if value is not None:
            setattr(seat, key, value)

    await db.commit()
    await db.refresh(seat)

    room_result = await db.execute(select(StudyRoom.name).where(StudyRoom.id == seat.room_id))
    room_name = room_result.scalar_one()
    resp = SeatAdminResponse.model_validate(seat)
    return resp.model_copy(update={"room_name": room_name})


async def delete_seat(db: AsyncSession, seat_id: int) -> None:
    result = await db.execute(select(Seat).where(Seat.id == seat_id))
    seat = result.scalar_one_or_none()
    if seat is None:
        raise ValueError(f"Seat {seat_id} not found")

    count_result = await db.execute(
        select(func.count()).where(Booking.seat_id == seat_id, Booking.status == "confirmed")
    )
    if count_result.scalar() > 0:
        raise ValueError("该座位存在活跃预约，无法删除")

    await db.delete(seat)
    await db.commit()


async def toggle_seat_status(db: AsyncSession, seat_id: int, new_status: str) -> SeatAdminResponse:
    result = await db.execute(select(Seat).where(Seat.id == seat_id))
    seat = result.scalar_one_or_none()
    if seat is None:
        raise ValueError(f"Seat {seat_id} not found")

    seat.status = new_status
    await db.commit()
    await db.refresh(seat)

    room_result = await db.execute(select(StudyRoom.name).where(StudyRoom.id == seat.room_id))
    room_name = room_result.scalar_one()
    resp = SeatAdminResponse.model_validate(seat)
    return resp.model_copy(update={"room_name": room_name})
