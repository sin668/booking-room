"""Integration tests for city APIs."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City


@pytest.fixture
async def seed_cities(db_session: AsyncSession):
    cities = [
        City(name="深圳市", province="广东省", sort_order=3, status="active"),
        City(name="茂名市", province="广东省", sort_order=1, status="active"),
        City(name="广州市", province="广东省", sort_order=2, status="active"),
        City(name="珠海市", province="广东省", sort_order=4, status="inactive"),
    ]
    db_session.add_all(cities)
    await db_session.flush()


class TestCityAPI:
    @pytest.mark.asyncio
    async def test_list_active_cities_sorted(self, client: AsyncClient, seed_cities):
        resp = await client.get("/api/v1/cities/")

        assert resp.status_code == 200
        data = resp.json()
        assert [item["name"] for item in data] == ["茂名市", "广州市", "深圳市"]
        assert {item["name"] for item in data}.isdisjoint({"珠海市"})
        assert data[0] == {"id": data[0]["id"], "name": "茂名市", "province": "广东省"}

    @pytest.mark.asyncio
    async def test_list_cities_empty_when_no_active_cities(
        self, client: AsyncClient, db_session: AsyncSession
    ):
        db_session.add(City(name="珠海市", province="广东省", sort_order=1, status="inactive"))
        await db_session.flush()

        resp = await client.get("/api/v1/cities/")

        assert resp.status_code == 200
        assert resp.json() == []
