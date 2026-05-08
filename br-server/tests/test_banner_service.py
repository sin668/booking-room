"""Unit tests for banner_service module."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.banner import Banner
from app.services import banner_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_banners(db_session: AsyncSession):
    """Seed banners for tests."""
    for i in range(3):
        db_session.add(
            Banner(
                image_url=f"https://example.com/banner{i}.jpg",
                title=f"Banner {i}",
                subtitle=f"Subtitle {i}",
                sort_order=i,
                is_active=True,
            )
        )
    # One inactive banner
    db_session.add(Banner(image_url="https://example.com/inactive.jpg", title="Inactive", is_active=False))
    await db_session.flush()


# ---------------------------------------------------------------------------
# list_active_banners
# ---------------------------------------------------------------------------


class TestListActiveBanners:
    @pytest.mark.asyncio
    async def test_returns_only_active(self, db_session: AsyncSession, seed_banners):
        """Only active banners are returned."""
        result = await banner_service.list_active_banners(db_session)
        assert len(result) == 3
        assert all(b.is_active is True for b in result)

    @pytest.mark.asyncio
    async def test_order_by_sort_order(self, db_session: AsyncSession, seed_banners):
        """Results are ordered by sort_order ascending."""
        result = await banner_service.list_active_banners(db_session)
        sort_orders = [b.sort_order for b in result]
        assert sort_orders == sorted(sort_orders)

    @pytest.mark.asyncio
    async def test_empty_db(self, db_session: AsyncSession):
        """Empty DB returns empty list."""
        result = await banner_service.list_active_banners(db_session)
        assert result == []
