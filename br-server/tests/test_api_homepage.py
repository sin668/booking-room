"""Integration tests for banner, activity, and study room APIs."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.banner import Banner
from app.models.study_room import StudyRoom


@pytest.fixture
async def seed_data(db_session: AsyncSession):
    """Insert test data into the in-memory test database."""
    db_session.add(Banner(image_url="https://example.com/b1.jpg", title="Banner 1", sort_order=2, is_active=True))
    db_session.add(Banner(image_url="https://example.com/b2.jpg", title="Banner 2", sort_order=1, is_active=True))
    db_session.add(Banner(image_url="https://example.com/b3.jpg", title="Banner Inactive", is_active=False))

    db_session.add(Activity(title="Activity 1", description="Desc 1", participant_count=100, sort_order=1, is_active=True))
    db_session.add(Activity(title="Activity 2", description="Desc 2", participant_count=200, sort_order=2, is_active=True))
    db_session.add(Activity(title="Activity Inactive", is_active=False))

    db_session.add(StudyRoom(name="Room A", address="Addr A", status="open", min_price=10.00))
    db_session.add(StudyRoom(name="Room B", address="Addr B", status="open", min_price=15.00))
    db_session.add(StudyRoom(name="Room Closed", address="Addr C", status="closed", min_price=8.00))

    await db_session.flush()


class TestBannerAPI:
    @pytest.mark.asyncio
    async def test_list_banners(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/banners")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["title"] == "Banner 2"
        assert data[1]["title"] == "Banner 1"

    @pytest.mark.asyncio
    async def test_list_banners_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/banners")
        assert resp.status_code == 200
        assert resp.json() == []


class TestActivityAPI:
    @pytest.mark.asyncio
    async def test_list_activities(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/activities")
        assert resp.status_code == 200
        data = resp.json()
        assert len(data) == 2
        assert data[0]["participant_count"] == 100
        assert data[1]["participant_count"] == 200

    @pytest.mark.asyncio
    async def test_list_activities_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/activities")
        assert resp.status_code == 200
        assert resp.json() == []


class TestStudyRoomAPI:
    @pytest.mark.asyncio
    async def test_list_rooms_default_pagination(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) == 2

    @pytest.mark.asyncio
    async def test_list_rooms_custom_pagination(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/rooms?page=1&page_size=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 1
        assert len(data["items"]) == 1
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_list_rooms_page_size_exceeds_max(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/rooms?page_size=100")
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_rooms_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
