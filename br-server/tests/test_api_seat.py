"""Integration tests for Seat API."""

from datetime import date, time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom


@pytest.fixture
async def seed_room_and_seats(db_session: AsyncSession):
    """Insert a study room and seats into the test database."""
    room = StudyRoom(name="Test Room", address="Test Address", status="open", min_price=10.00)
    db_session.add(room)
    await db_session.flush()

    db_session.add(Seat(room_id=room.id, seat_number="A-01", zone="quiet", position="靠窗", floor=3, price_per_hour=15.00, status="available", row=1, col=1))
    db_session.add(Seat(room_id=room.id, seat_number="A-02", zone="keyboard", position="靠墙", floor=3, price_per_hour=20.00, status="available", row=1, col=2))
    db_session.add(Seat(room_id=room.id, seat_number="B-01", zone="vip", floor=3, price_per_hour=30.00, status="maintenance", row=2, col=1))
    await db_session.flush()

    return room.id


class TestSeatAPI:
    @pytest.mark.asyncio
    async def test_list_seats_no_time_filter(self, client: AsyncClient, seed_room_and_seats):
        room_id = seed_room_and_seats
        resp = await client.get(f"/api/v1/rooms/{room_id}/seats/")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        assert data[0]["seat_number"] == "A-01"
        assert data[0]["zone"] == "quiet"
        assert data[0]["position"] == "靠窗"
        assert data[0]["floor"] == 3
        assert data[0]["price_per_hour"] == "15.00"
        assert data[0]["status"] == "available"
        assert data[0]["row"] == 1
        assert data[0]["col"] == 1
        assert "is_available" not in data[0]

    @pytest.mark.asyncio
    async def test_list_seats_with_availability_all_free(self, client: AsyncClient, seed_room_and_seats):
        room_id = seed_room_and_seats
        resp = await client.get(
            f"/api/v1/rooms/{room_id}/seats/",
            params={"date": "2026-05-01", "start_time": "09:00", "end_time": "12:00"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # A-01 available
        assert data[0]["seat_number"] == "A-01"
        assert data[0]["is_available"] is True
        # A-02 available
        assert data[1]["seat_number"] == "A-02"
        assert data[1]["is_available"] is True
        # B-01 maintenance → always unavailable
        assert data[2]["seat_number"] == "B-01"
        assert data[2]["is_available"] is False

    @pytest.mark.asyncio
    async def test_list_seats_with_availability_booked(self, client: AsyncClient, db_session: AsyncSession, seed_room_and_seats):
        room_id = seed_room_and_seats
        # Get seat A-01 id (first seat)
        from sqlalchemy import select
        result = await db_session.execute(select(Seat).where(Seat.seat_number == "A-01"))
        seat_a01 = result.scalar_one()

        # Create a booking that overlaps 09:00-12:00 (08:00-10:00)
        db_session.add(Booking(
            seat_id=seat_a01.id,
            user_id="user-001",
            room_id=room_id,
            date=date(2026, 5, 1),
            start_time=time(8, 0),
            end_time=time(10, 0),
            status="confirmed",
            total_price=30.00,
        ))
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/rooms/{room_id}/seats/",
            params={"date": "2026-05-01", "start_time": "09:00", "end_time": "12:00"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 3
        # A-01 booked
        assert data[0]["seat_number"] == "A-01"
        assert data[0]["is_available"] is False
        # A-02 still free
        assert data[1]["seat_number"] == "A-02"
        assert data[1]["is_available"] is True
        # B-01 maintenance
        assert data[2]["seat_number"] == "B-01"
        assert data[2]["is_available"] is False

    @pytest.mark.asyncio
    async def test_list_seats_cancelled_booking_ignored(self, client: AsyncClient, db_session: AsyncSession, seed_room_and_seats):
        room_id = seed_room_and_seats
        from sqlalchemy import select
        result = await db_session.execute(select(Seat).where(Seat.seat_number == "A-01"))
        seat_a01 = result.scalar_one()

        # Cancelled booking should not block availability
        db_session.add(Booking(
            seat_id=seat_a01.id,
            user_id="user-001",
            room_id=room_id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            status="cancelled",
            total_price=30.00,
        ))
        await db_session.flush()

        resp = await client.get(
            f"/api/v1/rooms/{room_id}/seats/",
            params={"date": "2026-05-01", "start_time": "09:00", "end_time": "12:00"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data[0]["seat_number"] == "A-01"
        assert data[0]["is_available"] is True

    @pytest.mark.asyncio
    async def test_list_seats_room_not_found(self, client: AsyncClient):
        resp = await client.get("/api/v1/rooms/9999/seats/")
        assert resp.status_code == 404
        assert "not found" in resp.json()["detail"].lower()

    @pytest.mark.asyncio
    async def test_list_seats_empty_room(self, client: AsyncClient, db_session: AsyncSession):
        room = StudyRoom(name="Empty Room", address="Nowhere", status="open", min_price=5.00)
        db_session.add(room)
        await db_session.flush()

        resp = await client.get(f"/api/v1/rooms/{room.id}/seats/")
        assert resp.status_code == 200
        assert resp.json() == []
