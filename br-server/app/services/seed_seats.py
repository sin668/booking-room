"""Seed seat data for existing study rooms."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.seat import Seat
from app.models.study_room import StudyRoom

ZONE_CONFIG = {
    "quiet": {"prefix": "A", "rows": 2, "cols_per_row": 7, "price": 6.00, "position": "靠窗"},
    "keyboard": {"prefix": "B", "rows": 2, "cols_per_row": 7, "price": 8.00, "position": "中间"},
    "vip": {"prefix": "D", "rows": 2, "cols_per_row": 6, "price": 12.00, "position": "独立"},
}


async def seed_seats_for_room(db: AsyncSession, room_id: int) -> int:
    """Generate seats for a study room. Returns number of seats created."""
    result = await db.execute(
        select(Seat).where(Seat.room_id == room_id).limit(1)
    )
    if result.scalar_one_or_none():
        return 0

    count = 0
    for zone, config in ZONE_CONFIG.items():
        for row_idx in range(config["rows"]):
            for col_idx in range(config["cols_per_row"]):
                seat_number = f"{config['prefix']}{row_idx + 1}-{col_idx + 1:02d}"
                position = config["position"] if row_idx == 0 else "中间"
                seat = Seat(
                    room_id=room_id,
                    seat_number=seat_number,
                    zone=zone,
                    position=position,
                    floor=3,
                    price_per_hour=config["price"],
                    status="available",
                    row=row_idx,
                    col=col_idx,
                )
                db.add(seat)
                count += 1
    return count


async def seed_all_rooms(db: AsyncSession) -> int:
    """Seed seats for all rooms. Returns total seats created."""
    result = await db.execute(select(StudyRoom))
    rooms = result.scalars().all()
    total = 0
    for room in rooms:
        total += await seed_seats_for_room(db, room.id)
    await db.flush()
    return total
