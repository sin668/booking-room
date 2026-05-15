"""Unit tests for the City model."""

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City


class TestCityModel:
    @pytest.mark.asyncio
    async def test_create_city(self, db_session: AsyncSession):
        city = City(name="茂名市", province="广东省", sort_order=1)

        db_session.add(city)
        await db_session.flush()

        assert city.id is not None
        assert city.name == "茂名市"
        assert city.province == "广东省"
        assert city.sort_order == 1

    @pytest.mark.asyncio
    async def test_name_unique(self, db_session: AsyncSession):
        db_session.add(City(name="茂名市", province="广东省", sort_order=1))
        await db_session.flush()

        db_session.add(City(name="茂名市", province="广东省", sort_order=2))

        with pytest.raises(IntegrityError):
            await db_session.flush()

    @pytest.mark.asyncio
    async def test_status_defaults_to_active(self, db_session: AsyncSession):
        city = City(name="茂名市", province="广东省", sort_order=1)

        db_session.add(city)
        await db_session.flush()

        assert city.status == "active"
