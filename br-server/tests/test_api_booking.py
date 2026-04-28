"""Integration tests for Booking API."""

import uuid
from datetime import date, time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def seed_room_seat(db_session: AsyncSession):
    """Insert a study room with seats into the test database."""
    room = StudyRoom(
        name="Test Room",
        address="123 Test St",
        status="open",
        min_price=10.00,
    )
    db_session.add(room)
    await db_session.flush()

    seat_a = Seat(
        room_id=room.id,
        seat_number="A-01",
        zone="quiet",
        position="window",
        floor=3,
        price_per_hour=15.00,
        status="available",
        row=1,
        col=1,
    )
    seat_b = Seat(
        room_id=room.id,
        seat_number="A-02",
        zone="quiet",
        position="center",
        floor=3,
        price_per_hour=20.00,
        status="available",
        row=1,
        col=2,
    )
    seat_m = Seat(
        room_id=room.id,
        seat_number="B-01",
        zone="vip",
        position="corner",
        floor=3,
        price_per_hour=30.00,
        status="maintenance",
        row=2,
        col=1,
    )
    db_session.add(seat_a)
    db_session.add(seat_b)
    db_session.add(seat_m)
    await db_session.flush()

    return {"room": room, "seat_a": seat_a, "seat_b": seat_b, "seat_m": seat_m}


@pytest.fixture
async def auth_client(client: AsyncClient):
    """Create a client with mocked auth returning USER_ID."""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def other_auth_client(client: AsyncClient):
    """Create a client with mocked auth returning OTHER_USER_ID."""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: OTHER_USER_ID
    yield client
    app.dependency_overrides.clear()


class TestCreateBooking:
    """POST /api/v1/bookings"""

    @pytest.mark.asyncio
    async def test_create_booking_success(self, auth_client: AsyncClient, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["seat_id"] == seat.id
        assert data["user_id"] == str(USER_ID)
        assert data["date"] == "2026-05-01"
        assert data["start_time"] == "09:00:00"
        assert data["end_time"] == "12:00:00"
        assert data["status"] == "confirmed"
        assert data["total_price"] == "45.00"  # 3 hours * 15.00
        assert data["seat"]["seat_number"] == "A-01"
        assert data["seat"]["zone"] == "quiet"
        assert data["seat"]["position"] == "window"
        assert data["seat"]["price_per_hour"] in ("15.00", "15.0")
        assert data["room"]["name"] == "Test Room"
        assert data["room"]["address"] == "123 Test St"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_booking_no_auth(self, client: AsyncClient, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        resp = await client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_booking_nonexistent_seat(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": 99999,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "座位不存在"

    @pytest.mark.asyncio
    async def test_create_booking_time_conflict(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        # Create existing booking: 08:00-10:00
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id="other-user",
                room_id=room.id,
                date=date(2026, 5, 1),
                start_time=time(8, 0),
                end_time=time(10, 0),
                status="confirmed",
                total_price=30.00,
            )
        )
        await db_session.flush()

        # Try booking 09:00-12:00 (overlaps with 08:00-10:00)
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "该座位该时段已被预约"

    @pytest.mark.asyncio
    async def test_create_booking_invalid_time_range(self, auth_client: AsyncClient, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "12:00",
                "end_time": "09:00",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_booking_seat_under_maintenance(self, auth_client: AsyncClient, seed_room_seat):
        seat = seed_room_seat["seat_m"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "该座位正在维护中"

    @pytest.mark.asyncio
    async def test_create_booking_cancelled_does_not_conflict(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        # Create cancelled booking
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id="other-user",
                room_id=room.id,
                date=date(2026, 5, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                status="cancelled",
                total_price=45.00,
            )
        )
        await db_session.flush()

        # Should succeed since previous booking was cancelled
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_booking_missing_fields(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={"seat_id": 1},
        )
        assert resp.status_code == 422


class TestListBookings:
    """GET /api/v1/bookings"""

    @pytest.mark.asyncio
    async def test_list_bookings_default_pagination(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        for i in range(3):
            db_session.add(
                Booking(
                    seat_id=seat.id,
                    user_id=str(USER_ID),
                    room_id=room.id,
                    date=date(2026, 5, 1 + i),
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                    status="confirmed",
                    total_price=45.00,
                )
            )
        await db_session.flush()

        resp = await auth_client.get("/api/v1/bookings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_bookings_filter_by_status(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id=str(USER_ID),
                room_id=room.id,
                date=date(2026, 5, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                status="confirmed",
                total_price=45.00,
            )
        )
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id=str(USER_ID),
                room_id=room.id,
                date=date(2026, 5, 2),
                start_time=time(14, 0),
                end_time=time(17, 0),
                status="cancelled",
                total_price=45.00,
            )
        )
        await db_session.flush()

        resp = await auth_client.get("/api/v1/bookings", params={"status": "confirmed"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_list_bookings_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/bookings")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_bookings_empty(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/v1/bookings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestGetBooking:
    """GET /api/v1/bookings/{booking_id}"""

    @pytest.mark.asyncio
    async def test_get_own_booking(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=45.00,
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.get(f"/api/v1/bookings/{booking.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == booking.id
        assert data["seat"]["seat_number"] == "A-01"
        assert data["room"]["name"] == "Test Room"

    @pytest.mark.asyncio
    async def test_get_other_users_booking_404(self, other_auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=45.00,
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await other_auth_client.get(f"/api/v1/bookings/{booking.id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_get_nonexistent_booking(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/v1/bookings/99999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_get_booking_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/bookings/1")
        assert resp.status_code == 401


class TestCancelBooking:
    """POST /api/v1/bookings/{booking_id}/cancel"""

    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=45.00,
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="cancelled",
            total_price=45.00,
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "该预约已取消"

    @pytest.mark.asyncio
    async def test_cancel_other_users_booking(self, other_auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=45.00,
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await other_auth_client.post(f"/api/v1/bookings/{booking.id}/cancel")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_booking(self, auth_client: AsyncClient):
        resp = await auth_client.post("/api/v1/bookings/99999/cancel")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_cancel_no_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/bookings/1/cancel")
        assert resp.status_code == 401
