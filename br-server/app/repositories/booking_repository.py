from __future__ import annotations

from datetime import date, time

from sqlalchemy import and_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking


class BookingRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def has_time_conflict(
        self,
        *,
        seat_id: int,
        booking_date: date,
        start_time: time,
        end_time: time,
    ) -> bool:
        stmt = select(Booking.id).where(
            Booking.seat_id == seat_id,
            Booking.date == booking_date,
            Booking.status != "cancelled",
            and_(
                Booking.start_time < end_time,
                Booking.end_time > start_time,
            ),
        )
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None
