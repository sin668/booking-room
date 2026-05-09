"""Integration tests for Study Record API."""

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


@pytest.fixture
async def seed_completed_bookings(db_session: AsyncSession):
    room = StudyRoom(name="Test Room", address="123 Test St", status="open", min_price=10.00)
    db_session.add(room)
    await db_session.flush()

    seat = Seat(
        room_id=room.id, seat_number="A-01", zone="quiet", position="window",
        floor=3, price_per_hour=15.00, status="available", row=1, col=1,
    )
    db_session.add(seat)
    await db_session.flush()

    bookings = []
    for i in range(3):
        b = Booking(
            seat_id=seat.id, user_id=str(USER_ID), room_id=room.id,
            date=date(2026, 5, 1 + i), start_time=time(9, 0), end_time=time(12, 0),
            status="completed", total_price=45.00,
        )
        db_session.add(b)
        bookings.append(b)
    await db_session.flush()

    return {"room": room, "seat": seat, "bookings": bookings}


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


class TestGetSummary:
    @pytest.mark.asyncio
    async def test_summary_with_records(self, auth_client: AsyncClient, seed_completed_bookings):
        resp = await auth_client.get("/api/v1/study-records/summary", params={"month": "2026-05"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["monthly_hours"] == 9.0
        assert data["monthly_bookings"] == 3
        assert data["max_streak_days"] == 3
        assert data["total_hours"] == 9.0
        assert len(data["calendar_mark"]) == 31
        studied = [m for m in data["calendar_mark"] if m["studied"]]
        assert len(studied) == 3

    @pytest.mark.asyncio
    async def test_summary_no_records(self, auth_client: AsyncClient, db_session: AsyncSession):
        resp = await auth_client.get("/api/v1/study-records/summary", params={"month": "2026-06"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["monthly_hours"] == 0.0
        assert data["monthly_bookings"] == 0
        assert data["max_streak_days"] == 0
        assert data["total_hours"] == 0.0
        assert len(data["calendar_mark"]) == 30

    @pytest.mark.asyncio
    async def test_summary_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/study-records/summary", params={"month": "2026-05"})
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_summary_missing_month_param(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/v1/study-records/summary")
        assert resp.status_code == 422


class TestListRecords:
    @pytest.mark.asyncio
    async def test_list_with_records(self, auth_client: AsyncClient, seed_completed_bookings):
        resp = await auth_client.get("/api/v1/study-records")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3
        assert data["page"] == 1
        assert data["page_size"] == 10
        item = data["items"][0]
        assert item["room_name"] == "Test Room"
        assert item["seat_number"] == "A-01"
        assert item["hours"] == 3.0
        assert "total_price" in item

    @pytest.mark.asyncio
    async def test_list_pagination(self, auth_client: AsyncClient, seed_completed_bookings):
        resp = await auth_client.get("/api/v1/study-records", params={"page": 1, "page_size": 2})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 2

        resp2 = await auth_client.get("/api/v1/study-records", params={"page": 2, "page_size": 2})
        assert resp2.status_code == 200
        assert len(resp2.json()["items"]) == 1

    @pytest.mark.asyncio
    async def test_list_filter_by_month(self, auth_client: AsyncClient, seed_completed_bookings):
        resp = await auth_client.get("/api/v1/study-records", params={"month": "2026-05"})
        assert resp.status_code == 200
        assert resp.json()["total"] == 3

        resp2 = await auth_client.get("/api/v1/study-records", params={"month": "2026-06"})
        assert resp2.status_code == 200
        assert resp2.json()["total"] == 0

    @pytest.mark.asyncio
    async def test_list_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/study-records")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_empty(self, auth_client: AsyncClient, db_session: AsyncSession):
        resp = await auth_client.get("/api/v1/study-records")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_records_ordered_by_date_desc(self, auth_client: AsyncClient, seed_completed_bookings):
        resp = await auth_client.get("/api/v1/study-records")
        assert resp.status_code == 200
        items = resp.json()["items"]
        dates = [item["date"] for item in items]
        assert dates == sorted(dates, reverse=True)
