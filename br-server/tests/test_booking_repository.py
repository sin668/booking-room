from datetime import date, time
from decimal import Decimal

import pytest

from app.models.booking import Booking
from app.repositories.booking_repository import BookingRepository


@pytest.mark.asyncio
async def test_has_time_conflict_returns_true_for_overlapping_confirmed_booking(db_session):
    existing = Booking(
        user_id="00000000-0000-0000-0000-000000000001",
        seat_id=1,
        room_id=1,
        date=date(2026, 5, 30),
        start_time=time(9, 0),
        end_time=time(11, 0),
        status="confirmed",
        payment_status="paid",
        original_price=Decimal("10.00"),
        discount_amount=Decimal("0.00"),
        total_price=Decimal("10.00"),
    )
    db_session.add(existing)
    await db_session.flush()

    repository = BookingRepository(db_session)

    result = await repository.has_time_conflict(
        seat_id=1,
        booking_date=date(2026, 5, 30),
        start_time=time(10, 0),
        end_time=time(12, 0),
    )

    assert result is True
