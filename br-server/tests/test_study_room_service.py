"""Unit tests for study_room_service module."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.study_room import StudyRoom
from app.services import study_room_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_study_rooms(db_session: AsyncSession):
    """Seed study rooms for tests."""
    rooms = [
        StudyRoom(
            name=f"Room {i}",
            description=f"Description {i}",
            cover_image="https://example.com/img.jpg",
            address=f"Address {i}",
            business_hours="08:00-22:00",
            status="open",
            min_price=10.0 + i,
        )
        for i in range(3)
    ]
    # One closed room
    rooms.append(
        StudyRoom(
            name="Closed Room",
            address="Nowhere",
            status="closed",
            min_price=5.0,
        )
    )
    for room in rooms:
        db_session.add(room)
    await db_session.flush()


# ---------------------------------------------------------------------------
# list_study_rooms
# ---------------------------------------------------------------------------


class TestListStudyRooms:
    @pytest.mark.asyncio
    async def test_list_open_only(self, db_session: AsyncSession, seed_study_rooms):
        """Only open rooms are returned."""
        result = await study_room_service.list_study_rooms(db_session)
        assert result.total == 3
        assert len(result.items) == 3

    @pytest.mark.asyncio
    async def test_pagination(self, db_session: AsyncSession, seed_study_rooms):
        """Pagination works correctly."""
        result = await study_room_service.list_study_rooms(db_session, page=1, page_size=2)
        assert result.total == 3
        assert len(result.items) == 2
        assert result.page_size == 2

    @pytest.mark.asyncio
    async def test_page_size_capped(self, db_session: AsyncSession, seed_study_rooms):
        """Page size is capped at MAX_PAGE_SIZE (50)."""
        result = await study_room_service.list_study_rooms(db_session, page_size=100)
        assert result.page_size == 50

    @pytest.mark.asyncio
    async def test_empty_db(self, db_session: AsyncSession):
        """Empty DB returns zero total and empty items."""
        result = await study_room_service.list_study_rooms(db_session)
        assert result.total == 0
        assert result.items == []
