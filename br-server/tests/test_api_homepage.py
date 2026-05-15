"""Integration tests for banner, activity, and study room APIs."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.models.banner import Banner
from app.models.city import City
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
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 50

    @pytest.mark.asyncio
    async def test_get_room_detail(self, client: AsyncClient, seed_data):
        list_resp = await client.get("/api/v1/rooms")
        room_id = list_resp.json()["items"][0]["id"]

        resp = await client.get(f"/api/v1/rooms/{room_id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == room_id
        assert data["name"] == "Room A"

    @pytest.mark.asyncio
    async def test_get_room_detail_not_found_for_closed_room(self, client: AsyncClient, seed_data):
        resp = await client.get("/api/v1/rooms")
        assert all(item["name"] != "Room Closed" for item in resp.json()["items"])

        closed_resp = await client.get("/api/v1/rooms/9999")
        assert closed_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_list_rooms_empty(self, client: AsyncClient):
        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []

    @pytest.mark.asyncio
    async def test_list_rooms_filters_by_city_id(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        maoming = City(name="茂名市", province="广东省", sort_order=1)
        guangzhou = City(name="广州市", province="广东省", sort_order=2)
        db_session.add_all([maoming, guangzhou])
        await db_session.flush()

        db_session.add_all(
            [
                StudyRoom(
                    name="Maoming Room",
                    address="Addr A",
                    status="open",
                    min_price=10.00,
                    city_id=maoming.id,
                ),
                StudyRoom(
                    name="Guangzhou Room",
                    address="Addr B",
                    status="open",
                    min_price=15.00,
                    city_id=guangzhou.id,
                ),
                StudyRoom(
                    name="Closed Maoming Room",
                    address="Addr C",
                    status="closed",
                    min_price=8.00,
                    city_id=maoming.id,
                ),
            ]
        )
        await db_session.flush()

        resp = await client.get(f"/api/v1/rooms?city_id={maoming.id}")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert [item["name"] for item in data["items"]] == ["Maoming Room"]
        assert data["items"][0]["city_id"] == maoming.id
        assert data["items"][0]["city_name"] == "茂名市"

    @pytest.mark.asyncio
    async def test_list_rooms_without_city_id_returns_all_open_rooms(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        maoming = City(name="茂名市", province="广东省", sort_order=1)
        guangzhou = City(name="广州市", province="广东省", sort_order=2)
        db_session.add_all([maoming, guangzhou])
        await db_session.flush()

        db_session.add_all(
            [
                StudyRoom(
                    name="Maoming Room",
                    address="Addr A",
                    status="open",
                    min_price=10.00,
                    city_id=maoming.id,
                ),
                StudyRoom(
                    name="Guangzhou Room",
                    address="Addr B",
                    status="open",
                    min_price=15.00,
                    city_id=guangzhou.id,
                ),
                StudyRoom(
                    name="No City Room",
                    address="Addr C",
                    status="open",
                    min_price=20.00,
                ),
            ]
        )
        await db_session.flush()

        resp = await client.get("/api/v1/rooms")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert {item["name"] for item in data["items"]} == {
            "Maoming Room",
            "Guangzhou Room",
            "No City Room",
        }

    @pytest.mark.asyncio
    async def test_list_rooms_missing_city_returns_empty(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        city = City(name="茂名市", province="广东省", sort_order=1)
        db_session.add(city)
        await db_session.flush()
        db_session.add(
            StudyRoom(
                name="Maoming Room",
                address="Addr A",
                status="open",
                min_price=10.00,
                city_id=city.id,
            )
        )
        await db_session.flush()

        resp = await client.get("/api/v1/rooms?city_id=9999")

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []
