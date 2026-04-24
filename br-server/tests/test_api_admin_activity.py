"""Integration tests for admin activity API endpoints."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin
from app.models.activity import Activity

ADMIN_TOKEN = "test-admin-token"


@pytest.fixture
def admin_headers():
    return {"X-Admin-Token": ADMIN_TOKEN}


@pytest.fixture
async def seed_activities(db_session: AsyncSession):
    db_session.add(Activity(title="Active Activity 1", description="Desc 1", participant_count=100, sort_order=1, is_active=True))
    db_session.add(Activity(title="Active Activity 2", participant_count=200, sort_order=2, is_active=True))
    db_session.add(Activity(title="Inactive Activity", is_active=False))
    await db_session.flush()


class TestAdminAuth:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client: AsyncClient, seed_activities):
        from app.main import app

        # Temporarily remove the override so the real dependency runs
        del app.dependency_overrides[get_current_admin]
        try:
            resp = await client.get("/api/v1/admin/activities")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None

    @pytest.mark.asyncio
    async def test_wrong_token_returns_401(self, client: AsyncClient, seed_activities):
        from app.main import app

        # Temporarily remove the override so the real dependency runs
        del app.dependency_overrides[get_current_admin]
        try:
            resp = await client.get("/api/v1/admin/activities", headers={"X-Admin-Token": "wrong"})
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None


class TestAdminListActivities:
    @pytest.mark.asyncio
    async def test_list_all_activities(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_pagination(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?page=1&page_size=2", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["page_size"] == 2
        assert len(data["items"]) == 2
        assert data["total"] == 3

    @pytest.mark.asyncio
    async def test_keyword_search(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?keyword=Inactive", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["title"] == "Inactive Activity"

    @pytest.mark.asyncio
    async def test_filter_by_active_true(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?is_active=true", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2

    @pytest.mark.asyncio
    async def test_filter_by_active_false(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities?is_active=false", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1

    @pytest.mark.asyncio
    async def test_empty_result(self, client: AsyncClient, admin_headers):
        resp = await client.get("/api/v1/admin/activities", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestAdminCreateActivity:
    @pytest.mark.asyncio
    async def test_create_activity(self, client: AsyncClient, admin_headers):
        resp = await client.post(
            "/api/v1/admin/activities",
            json={"title": "New Activity", "description": "Test desc", "participant_count": 50, "sort_order": 3},
            headers=admin_headers,
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["title"] == "New Activity"
        assert data["is_active"] is True
        assert data["id"] is not None

    @pytest.mark.asyncio
    async def test_create_with_defaults(self, client: AsyncClient, admin_headers):
        resp = await client.post("/api/v1/admin/activities", json={"title": "Minimal"}, headers=admin_headers)
        assert resp.status_code == 201
        data = resp.json()
        assert data["participant_count"] == 0
        assert data["sort_order"] == 0
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_create_missing_title(self, client: AsyncClient, admin_headers):
        resp = await client.post("/api/v1/admin/activities", json={}, headers=admin_headers)
        assert resp.status_code == 422


class TestAdminGetActivity:
    @pytest.mark.asyncio
    async def test_get_activity(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.get("/api/v1/admin/activities/1", headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Active Activity 1"
        assert "created_at" in data
        assert "updated_at" in data

    @pytest.mark.asyncio
    async def test_get_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.get("/api/v1/admin/activities/999", headers=admin_headers)
        assert resp.status_code == 404


class TestAdminUpdateActivity:
    @pytest.mark.asyncio
    async def test_update_activity(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.put(
            "/api/v1/admin/activities/1",
            json={"title": "Updated Title"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["title"] == "Updated Title"

    @pytest.mark.asyncio
    async def test_update_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.put("/api/v1/admin/activities/999", json={"title": "X"}, headers=admin_headers)
        assert resp.status_code == 404


class TestAdminDeleteActivity:
    @pytest.mark.asyncio
    async def test_delete_activity(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.delete("/api/v1/admin/activities/1", headers=admin_headers)
        assert resp.status_code == 204

        resp = await client.get("/api/v1/admin/activities/1", headers=admin_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.delete("/api/v1/admin/activities/999", headers=admin_headers)
        assert resp.status_code == 404


class TestAdminToggleStatus:
    @pytest.mark.asyncio
    async def test_toggle_to_inactive(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.patch("/api/v1/admin/activities/1/status", json={"is_active": False}, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is False

    @pytest.mark.asyncio
    async def test_toggle_to_active(self, client: AsyncClient, seed_activities, admin_headers):
        resp = await client.patch("/api/v1/admin/activities/3/status", json={"is_active": True}, headers=admin_headers)
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_active"] is True

    @pytest.mark.asyncio
    async def test_toggle_not_found(self, client: AsyncClient, admin_headers):
        resp = await client.patch("/api/v1/admin/activities/999/status", json={"is_active": True}, headers=admin_headers)
        assert resp.status_code == 404
