"""Integration tests for admin booking API endpoints."""

import pytest
from datetime import date
from decimal import Decimal
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom


@pytest.fixture
async def seed_data(db_session: AsyncSession):
    room = StudyRoom(id=1, name="Room A", address="Address A", status="open")
    seat = Seat(
        id=1,
        room_id=1,
        seat_number="A1",
        zone="quiet",
        price_per_hour=Decimal("10.00"),
        status="available",
        row=1,
        col=1,
    )
    db_session.add(room)
    db_session.add(seat)

    from datetime import time

    confirmed = Booking(
        id=1,
        seat_id=1,
        user_id="user-1",
        room_id=1,
        date=date(2026, 5, 1),
        start_time=time(9, 0),
        end_time=time(11, 0),
        status="confirmed",
        total_price=Decimal("20.00"),
    )
    cancelled = Booking(
        id=2,
        seat_id=1,
        user_id="user-2",
        room_id=1,
        date=date(2026, 5, 2),
        start_time=time(14, 0),
        end_time=time(16, 0),
        status="cancelled",
        total_price=Decimal("20.00"),
    )
    db_session.add(confirmed)
    db_session.add(cancelled)
    await db_session.flush()


class TestAdminAuth:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client: AsyncClient, seed_data):
        from app.main import app

        del app.dependency_overrides[get_current_admin]
        try:
            resp = await client.get("/api/v1/admin/bookings")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None


class TestAdminListBookings:
    @pytest.mark.asyncio
    async def test_list_returns_200(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/admin/bookings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/admin/bookings?page=1&page_size=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert len(data["items"]) == 1
        assert data["page_size"] == 1

    @pytest.mark.asyncio
    async def test_filter_by_status(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/admin/bookings?status=confirmed")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "confirmed"


class TestAdminGetBooking:
    @pytest.mark.asyncio
    async def test_detail_returns_200(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/admin/bookings/1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == 1
        assert data["user_id"] == "user-1"
        assert data["seat"]["seat_number"] == "A1"
        assert data["room"]["name"] == "Room A"

    @pytest.mark.asyncio
    async def test_not_found_returns_404(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/admin/bookings/999")
        assert resp.status_code == 404


class TestAdminCancelBooking:
    @pytest.mark.asyncio
    async def test_cancel_confirmed_returns_200(self, client: AsyncClient, seed_data):
        resp = await client.post("/api/v1/admin/bookings/1/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled_returns_400(self, client: AsyncClient, seed_data):
        resp = await client.post("/api/v1/admin/bookings/2/cancel")
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_cancel_not_found_returns_404(self, client: AsyncClient, seed_data):
        resp = await client.post("/api/v1/admin/bookings/999/cancel")
        assert resp.status_code == 404
