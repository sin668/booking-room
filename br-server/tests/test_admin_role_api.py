import pytest
from httpx import AsyncClient

from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.models.admin_user import AdminUser
from app.services.admin_auth_service import AdminAuthService


def legacy_headers():
    return {"X-Admin-Token": "test-admin-token"}


@pytest.mark.asyncio
async def test_role_crud_duplicate_and_assigned_delete_conflict(client: AsyncClient, monkeypatch, db_session):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")

    created = await client.post(
        "/api/v1/admin/roles",
        headers=legacy_headers(),
        json={"name": "Manager", "code": "manager", "description": "ops", "status": "active"},
    )
    assert created.status_code == 201

    duplicate = await client.post(
        "/api/v1/admin/roles",
        headers=legacy_headers(),
        json={"name": "Manager 2", "code": "manager", "status": "active"},
    )
    assert duplicate.status_code == 409

    role_id = created.json()["id"]
    role = await db_session.get(AdminRole, role_id)
    user = AdminUser(username="assigned", password_hash=AdminAuthService.hash_password("secret123"))
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()

    delete = await client.delete(f"/api/v1/admin/roles/{role_id}", headers=legacy_headers())
    assert delete.status_code == 409


@pytest.mark.asyncio
async def test_role_menu_assignment_updates_auth_permissions(client: AsyncClient, monkeypatch, db_session):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    menu = AdminMenu(type="button", title="Role assign", permission_code="system:role:assign")
    role = AdminRole(name="Assigner", code="assigner")
    user = AdminUser(username="user1", password_hash=AdminAuthService.hash_password("secret123"))
    user.roles.append(role)
    db_session.add_all([menu, role, user])
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/admin/roles/{role.id}/menus",
        headers=legacy_headers(),
        json={"menu_ids": [menu.id]},
    )
    assert resp.status_code == 200

    token = AdminAuthService.create_access_token(user.id)
    me = await client.get("/api/v1/admin/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert {"label": "Role assign", "value": "system:role:assign"} in me.json()["permissions"]
