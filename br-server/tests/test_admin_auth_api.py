import pytest
from httpx import AsyncClient

from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.models.admin_user import AdminUser
from app.services.admin_auth_service import AdminAuthService


@pytest.fixture
async def admin_user(db_session):
    permission = AdminMenu(type="button", title="Role create", permission_code="system:role:create")
    role = AdminRole(name="Role manager", code="role_manager")
    role.menus.append(permission)
    user = AdminUser(
        username="admin",
        password_hash=AdminAuthService.hash_password("secret123"),
        nickname="Admin",
        email="admin@example.com",
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_admin_login_and_me_return_permissions(client: AsyncClient, admin_user):
    login = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get(
        "/api/v1/admin/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert {"label": "Role create", "value": "system:role:create"} in me.json()["permissions"]


@pytest.mark.asyncio
async def test_admin_login_rejects_disabled_user(client: AsyncClient, db_session):
    db_session.add(
        AdminUser(
            username="disabled",
            password_hash=AdminAuthService.hash_password("secret123"),
            status="disabled",
        )
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "disabled", "password": "secret123"},
    )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_profile_update_does_not_accept_username(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "new-name", "nickname": "New"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_password_update_validates_confirmation(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "old_password": "secret123",
            "new_password": "new-secret",
            "confirm_password": "different",
        },
    )

    assert resp.status_code == 422
