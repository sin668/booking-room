import pytest
from httpx import AsyncClient

from app.api.dependencies import get_current_admin
from app.main import app
from app.models.admin_menu import AdminMenu


def legacy_headers():
    return {"X-Admin-Token": "test-admin-token"}


@pytest.mark.asyncio
async def test_component_options_and_invalid_component(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")

    options = await client.get("/api/v1/admin/menus/component-options", headers=legacy_headers())
    assert options.status_code == 200
    assert {"label": "LAYOUT", "value": "LAYOUT"} in options.json()

    invalid = await client.post(
        "/api/v1/admin/menus",
        headers=legacy_headers(),
        json={"type": "menu", "title": "Bad", "path": "/bad", "name": "Bad", "component": "/missing/page"},
    )
    assert invalid.status_code == 422


@pytest.mark.asyncio
async def test_menu_tree_crud_and_delete_child_conflict(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")

    parent = await client.post(
        "/api/v1/admin/menus",
        headers=legacy_headers(),
        json={"type": "directory", "title": "System", "path": "/system", "name": "System", "component": "LAYOUT"},
    )
    assert parent.status_code == 201
    parent_id = parent.json()["id"]

    child = await client.post(
        "/api/v1/admin/menus",
        headers=legacy_headers(),
        json={
            "parent_id": parent_id,
            "type": "button",
            "title": "Create",
            "permission_code": "system:menu:create",
        },
    )
    assert child.status_code == 201

    blocked = await client.delete(f"/api/v1/admin/menus/{parent_id}", headers=legacy_headers())
    assert blocked.status_code == 409

    tree = await client.get("/api/v1/admin/menus", headers=legacy_headers())
    assert tree.status_code == 200
    assert tree.json()[0]["children"][0]["permission_code"] == "system:menu:create"


@pytest.mark.asyncio
async def test_dynamic_routes_exclude_buttons_and_disabled_nodes(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    app.dependency_overrides.pop(get_current_admin, None)
    enabled = AdminMenu(type="menu", title="Dashboard", path="/dashboard", name="Dashboard", component="/dashboard/console/console")
    disabled = AdminMenu(type="menu", title="Hidden", path="/hidden", name="Hidden", component="/dashboard/console/console", enabled=False)
    button = AdminMenu(type="button", title="Button", permission_code="dashboard:create")
    db_session.add_all([enabled, disabled, button])
    await db_session.commit()

    resp = await client.get("/api/v1/admin/menus/routes", headers=legacy_headers())

    assert resp.status_code == 200
    names = {item["name"] for item in resp.json()}
    assert names == {"Dashboard"}
