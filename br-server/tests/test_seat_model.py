"""Tests for the Seat model."""

import pytest
from datetime import date, time

from app.models.seat import Seat


class TestSeatZone:
    """Test that zone accepts valid values."""

    @pytest.mark.parametrize("zone", ["quiet", "keyboard", "vip"])
    async def test_zone_accepts_valid_values(self, db_session, zone):
        seat = Seat(
            room_id=1,
            seat_number="A1",
            zone=zone,
            price_per_hour=10.00,
            row=1,
            col=1,
        )
        db_session.add(seat)
        await db_session.commit()
        result = await db_session.get(Seat, seat.id)
        assert result is not None
        assert result.zone == zone


class TestSeatDefaults:
    """Test default values."""

    async def test_status_defaults_to_available(self, db_session):
        seat = Seat(
            room_id=1,
            seat_number="A1",
            zone="quiet",
            price_per_hour=10.00,
            row=1,
            col=1,
        )
        db_session.add(seat)
        await db_session.commit()
        result = await db_session.get(Seat, seat.id)
        assert result.status == "available"

    async def test_floor_defaults_to_3(self, db_session):
        seat = Seat(
            room_id=1,
            seat_number="A1",
            zone="quiet",
            price_per_hour=10.00,
            row=1,
            col=1,
        )
        db_session.add(seat)
        await db_session.commit()
        result = await db_session.get(Seat, seat.id)
        assert result.floor == 3


class TestSeatRequiredFields:
    """Test that required fields are enforced."""

    async def test_seat_creates_with_all_required_fields(self, db_session):
        seat = Seat(
            room_id=1,
            seat_number="A1",
            zone="quiet",
            price_per_hour=10.00,
            row=1,
            col=1,
        )
        db_session.add(seat)
        await db_session.commit()
        result = await db_session.get(Seat, seat.id)
        assert result is not None
        assert result.room_id == 1
        assert result.seat_number == "A1"
        assert result.zone == "quiet"
        assert result.price_per_hour == 10.00
        assert result.row == 1
        assert result.col == 1
