"""Unit tests for activity_service module."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity
from app.services import activity_service


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_activities(db_session: AsyncSession):
    """Seed activities for pagination and filter tests."""
    for i in range(5):
        db_session.add(
            Activity(
                title=f"Activity {i}",
                description=f"Desc {i}",
                participant_count=i * 10,
                sort_order=i,
                is_active=True,
            )
        )
    # One inactive activity
    db_session.add(Activity(title="Inactive", is_active=False))
    await db_session.flush()


# ---------------------------------------------------------------------------
# list_active_activities
# ---------------------------------------------------------------------------


class TestListActiveActivities:
    @pytest.mark.asyncio
    async def test_returns_only_active(self, db_session: AsyncSession, seed_activities):
        """list_active_activities returns only is_active=True records."""
        result = await activity_service.list_active_activities(db_session)
        assert len(result) == 5
        assert all(a.is_active is True for a in result)

    @pytest.mark.asyncio
    async def test_order_by_sort_order(self, db_session: AsyncSession, seed_activities):
        """Results are ordered by sort_order ascending."""
        result = await activity_service.list_active_activities(db_session)
        sort_orders = [a.sort_order for a in result]
        assert sort_orders == sorted(sort_orders)

    @pytest.mark.asyncio
    async def test_empty_db(self, db_session: AsyncSession):
        """Returns empty list when no activities exist."""
        result = await activity_service.list_active_activities(db_session)
        assert result == []


# ---------------------------------------------------------------------------
# list_activities (pagination)
# ---------------------------------------------------------------------------


class TestListActivities:
    @pytest.mark.asyncio
    async def test_default_pagination(self, db_session: AsyncSession, seed_activities):
        """Default pagination returns page 1 with all items."""
        result = await activity_service.list_activities(db_session)
        assert result["total"] == 6
        assert result["page"] == 1
        assert result["page_size"] == 10
        assert len(result["items"]) == 6

    @pytest.mark.asyncio
    async def test_custom_page_size(self, db_session: AsyncSession, seed_activities):
        """Custom page_size limits items per page."""
        result = await activity_service.list_activities(db_session, page=1, page_size=2)
        assert len(result["items"]) == 2
        assert result["total"] == 6
        assert result["page_size"] == 2

    @pytest.mark.asyncio
    async def test_second_page(self, db_session: AsyncSession, seed_activities):
        """Page 2 returns remaining items."""
        result = await activity_service.list_activities(db_session, page=2, page_size=2)
        assert len(result["items"]) == 2
        assert result["total"] == 6

    @pytest.mark.asyncio
    async def test_page_beyond_total(self, db_session: AsyncSession, seed_activities):
        """Page beyond total items adjusts offset to last valid page."""
        result = await activity_service.list_activities(db_session, page=100, page_size=2)
        # Should return items from the last page (offset adjusted)
        assert len(result["items"]) <= 2
        assert result["total"] == 6

    @pytest.mark.asyncio
    async def test_keyword_search(self, db_session: AsyncSession, seed_activities):
        """Keyword search filters by title and description."""
        result = await activity_service.list_activities(db_session, keyword="Activity 2")
        assert result["total"] == 1
        assert result["items"][0].title == "Activity 2"

    @pytest.mark.asyncio
    async def test_keyword_search_no_match(self, db_session: AsyncSession, seed_activities):
        """Keyword search with no matches returns empty."""
        result = await activity_service.list_activities(db_session, keyword="nonexistent")
        assert result["total"] == 0
        assert result["items"] == []

    @pytest.mark.asyncio
    async def test_filter_active_true(self, db_session: AsyncSession, seed_activities):
        """Filter is_active=True returns only active activities."""
        result = await activity_service.list_activities(db_session, is_active=True)
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_filter_active_false(self, db_session: AsyncSession, seed_activities):
        """Filter is_active=False returns only inactive activities."""
        result = await activity_service.list_activities(db_session, is_active=False)
        assert result["total"] == 1
        assert result["items"][0].title == "Inactive"

    @pytest.mark.asyncio
    async def test_keyword_and_filter_combined(self, db_session: AsyncSession, seed_activities):
        """Keyword and is_active filter combined."""
        result = await activity_service.list_activities(db_session, keyword="Activity", is_active=True)
        assert result["total"] == 5

    @pytest.mark.asyncio
    async def test_empty_db(self, db_session: AsyncSession):
        """Empty DB returns zero total and empty items."""
        result = await activity_service.list_activities(db_session)
        assert result["total"] == 0
        assert result["items"] == []
        assert result["total_pages"] == 0 if "total_pages" in result else True


# ---------------------------------------------------------------------------
# get_activity_by_id
# ---------------------------------------------------------------------------


class TestGetActivityById:
    @pytest.mark.asyncio
    async def test_found(self, db_session: AsyncSession, seed_activities):
        """Returns activity when found."""
        activity = await activity_service.get_activity_by_id(db_session, 1)
        assert activity is not None
        assert activity.title == "Activity 0"

    @pytest.mark.asyncio
    async def test_not_found(self, db_session: AsyncSession):
        """Returns None when not found."""
        activity = await activity_service.get_activity_by_id(db_session, 999)
        assert activity is None


# ---------------------------------------------------------------------------
# create_activity
# ---------------------------------------------------------------------------


class TestCreateActivity:
    @pytest.mark.asyncio
    async def test_create_success(self, db_session: AsyncSession):
        """Creates an activity and returns it with an ID."""
        data = {
            "title": "New Activity",
            "description": "A new one",
            "participant_count": 42,
            "sort_order": 1,
            "is_active": True,
        }
        activity = await activity_service.create_activity(db_session, data)
        assert activity.id is not None
        assert activity.title == "New Activity"
        assert activity.participant_count == 42

    @pytest.mark.asyncio
    async def test_create_with_defaults(self, db_session: AsyncSession):
        """Creates activity with minimal data."""
        data = {"title": "Minimal"}
        activity = await activity_service.create_activity(db_session, data)
        assert activity.id is not None
        assert activity.title == "Minimal"
        assert activity.is_active is True


# ---------------------------------------------------------------------------
# update_activity
# ---------------------------------------------------------------------------


class TestUpdateActivity:
    @pytest.mark.asyncio
    async def test_update_success(self, db_session: AsyncSession, seed_activities):
        """Updates activity fields."""
        activity = await activity_service.get_activity_by_id(db_session, 1)
        updated = await activity_service.update_activity(db_session, activity, {"title": "Updated"})
        assert updated.title == "Updated"

    @pytest.mark.asyncio
    async def test_update_none_values_ignored(self, db_session: AsyncSession, seed_activities):
        """None values in update data are ignored."""
        activity = await activity_service.get_activity_by_id(db_session, 1)
        original_title = activity.title
        updated = await activity_service.update_activity(db_session, activity, {"title": None})
        assert updated.title == original_title


# ---------------------------------------------------------------------------
# delete_activity
# ---------------------------------------------------------------------------


class TestDeleteActivity:
    @pytest.mark.asyncio
    async def test_delete_success(self, db_session: AsyncSession, seed_activities):
        """Deletes an activity."""
        activity = await activity_service.get_activity_by_id(db_session, 1)
        assert activity is not None
        await activity_service.delete_activity(db_session, activity)
        assert await activity_service.get_activity_by_id(db_session, 1) is None


# ---------------------------------------------------------------------------
# toggle_activity_status
# ---------------------------------------------------------------------------


class TestToggleActivityStatus:
    @pytest.mark.asyncio
    async def test_toggle_to_inactive(self, db_session: AsyncSession, seed_activities):
        """Toggles activity to inactive."""
        activity = await activity_service.get_activity_by_id(db_session, 1)
        assert activity.is_active is True
        result = await activity_service.toggle_activity_status(db_session, activity, False)
        assert result.is_active is False

    @pytest.mark.asyncio
    async def test_toggle_to_active(self, db_session: AsyncSession, seed_activities):
        """Toggles activity to active."""
        # Get the inactive activity (id=6)
        activity = await activity_service.get_activity_by_id(db_session, 6)
        assert activity.is_active is False
        result = await activity_service.toggle_activity_status(db_session, activity, True)
        assert result.is_active is True
