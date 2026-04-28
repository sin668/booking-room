"""Tests for the Booking model."""

import pytest
from datetime import date, time

from app.models.booking import Booking


class TestBookingDefaults:
    """Test default values."""

    async def test_status_defaults_to_confirmed(self, db_session):
        booking = Booking(
            seat_id=1,
            user_id="user-123",
            room_id=1,
            date=date(2026, 4, 27),
            start_time=time(9, 0),
            end_time=time(12, 0),
            total_price=30.00,
        )
        db_session.add(booking)
        await db_session.commit()
        result = await db_session.get(Booking, booking.id)
        assert result.status == "confirmed"


class TestBookingRequiredFields:
    """Test that required fields are enforced."""

    async def test_booking_creates_with_all_required_fields(self, db_session):
        booking = Booking(
            seat_id=1,
            user_id="user-123",
            room_id=1,
            date=date(2026, 4, 27),
            start_time=time(9, 0),
            end_time=time(12, 0),
            total_price=30.00,
        )
        db_session.add(booking)
        await db_session.commit()
        result = await db_session.get(Booking, booking.id)
        assert result is not None
        assert result.seat_id == 1
        assert result.user_id == "user-123"
        assert result.room_id == 1
        assert result.date == date(2026, 4, 27)
        assert result.start_time == time(9, 0)
        assert result.end_time == time(12, 0)
        assert result.total_price == 30.00
