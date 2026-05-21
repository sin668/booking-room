import pytest
from httpx import AsyncClient

from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.models.user import User
from app.services.admin_auth_service import AdminAuthService


def legacy_headers():
    return {"X-Admin-Token": "test-admin-token"}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_users(db_session):
    """Create a mix of app and admin users for list/filter tests."""
    users = []
    # App users
    for i in range(5):
        u = User(
            user_type="app",
            phone=f"1380013800{i}",
            nickname=f"appuser{i}",
            password_hash=AdminAuthService.hash_password("secret123"),
            status="active" if i < 4 else "banned",
        )
        db_session.add(u)
        users.append(u)
    # Admin users - use unique phone values to avoid UNIQUE constraint
    for i in range(3):
        u = User(
            user_type="admin",
            phone=f"admin_phone_{i}",
            username=f"adminuser{i}",
            nickname=f"Admin {i}",
            password_hash=AdminAuthService.hash_password("secret123"),
            status="active" if i < 2 else "banned",
        )
        db_session.add(u)
        users.append(u)
    await db_session.commit()
    for u in users:
        await db_session.refresh(u)
    return users


# ---------------------------------------------------------------------------
# GET /api/v1/admin/users  - list users
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_list_users_default(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get("/api/v1/admin/users", headers=legacy_headers())
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 8
    assert len(body["items"]) == 8
    assert body["page"] == 1
    assert body["page_size"] == 20


@pytest.mark.asyncio
async def test_list_users_pagination(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"page": 1, "page_size": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 8
    assert len(body["items"]) == 3
    assert body["page"] == 1
    assert body["page_size"] == 3


@pytest.mark.asyncio
async def test_list_users_pagination_page2(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"page": 2, "page_size": 3},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 8
    assert len(body["items"]) == 3
    assert body["page"] == 2


@pytest.mark.asyncio
async def test_list_users_filter_by_user_type_app(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"user_type": "app"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    for item in body["items"]:
        assert item["user_type"] == "app"


@pytest.mark.asyncio
async def test_list_users_filter_by_user_type_admin(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"user_type": "admin"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 3
    for item in body["items"]:
        assert item["user_type"] == "admin"


@pytest.mark.asyncio
async def test_list_users_filter_by_keyword_phone(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"keyword": "13800138001"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    assert body["items"][0]["phone"] == "13800138001"


@pytest.mark.asyncio
async def test_list_users_filter_by_keyword_nickname(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"keyword": "appuser"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 5
    for item in body["items"]:
        assert "appuser" in (item["nickname"] or "")


@pytest.mark.asyncio
async def test_list_users_filter_by_keyword_username(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"keyword": "adminuser0"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 1
    # AdminUserListItem does not include username; verify by nickname instead
    assert body["items"][0]["nickname"] == "Admin 0"


@pytest.mark.asyncio
async def test_list_users_filter_by_status_active(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"status_filter": "active"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 6  # 4 active app + 2 active admin
    for item in body["items"]:
        assert item["status"] == "active"


@pytest.mark.asyncio
async def test_list_users_filter_by_status_banned(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"status_filter": "banned"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 2  # 1 banned app + 1 banned admin
    for item in body["items"]:
        assert item["status"] == "banned"


@pytest.mark.asyncio
async def test_list_users_empty_result(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.get(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        params={"keyword": "nonexistentxyz"},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total"] == 0
    assert body["items"] == []


# ---------------------------------------------------------------------------
# GET /api/v1/admin/users/{user_id}  - get user detail
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_get_user_detail(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]
    resp = await client.get(
        f"/api/v1/admin/users/{user.id}",
        headers=legacy_headers(),
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == str(user.id)
    assert body["phone"] == user.phone
    assert body["nickname"] == user.nickname
    assert body["user_type"] == user.user_type


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    import uuid
    resp = await client.get(
        f"/api/v1/admin/users/{uuid.uuid4()}",
        headers=legacy_headers(),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# POST /api/v1/admin/users  - create user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_app_user(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "app",
            "phone": "13900139001",
            "password": "testpass123",
            "nickname": "New App User",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_type"] == "app"
    assert body["phone"] == "13900139001"
    assert body["nickname"] == "New App User"


@pytest.mark.asyncio
async def test_create_admin_user(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "admin",
            "username": "newadmin",
            "password": "testpass123",
            "nickname": "New Admin",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_type"] == "admin"
    assert body["username"] == "newadmin"
    assert body["nickname"] == "New Admin"


@pytest.mark.asyncio
async def test_create_app_user_requires_phone(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "app",
            "password": "testpass123",
            "nickname": "No Phone",
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_admin_user_requires_username(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "admin",
            "password": "testpass123",
            "nickname": "No Username",
        },
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_create_duplicate_phone_returns_409(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "app",
            "phone": "13800138001",
            "password": "testpass123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_duplicate_username_returns_409(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "admin",
            "username": "adminuser0",
            "password": "testpass123",
        },
    )
    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_create_app_user_invalid_phone_format(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "app",
            "phone": "123",
            "password": "testpass123",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_create_user_short_password(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "app",
            "phone": "13900139002",
            "password": "abc",
        },
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/admin/users/{user_id}  - update user
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_update_user_nickname(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}",
        headers=legacy_headers(),
        json={"nickname": "Updated Nickname"},
    )
    assert resp.status_code == 200
    assert resp.json()["nickname"] == "Updated Nickname"


@pytest.mark.asyncio
async def test_update_user_email(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}",
        headers=legacy_headers(),
        json={"email": "new@example.com"},
    )
    assert resp.status_code == 200
    assert resp.json()["email"] == "new@example.com"


@pytest.mark.asyncio
async def test_update_user_multiple_fields(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}",
        headers=legacy_headers(),
        json={
            "nickname": "Multi",
            "email": "multi@test.com",
            "mobile": "18612345678",
        },
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["nickname"] == "Multi"
    assert body["email"] == "multi@test.com"
    assert body["mobile"] == "18612345678"


@pytest.mark.asyncio
async def test_update_user_not_found(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    import uuid
    resp = await client.put(
        f"/api/v1/admin/users/{uuid.uuid4()}",
        headers=legacy_headers(),
        json={"nickname": "Ghost"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# PUT /api/v1/admin/users/{user_id}/reset-password
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_reset_password(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}/reset-password",
        headers=legacy_headers(),
        json={"new_password": "newpassword123"},
    )
    assert resp.status_code == 200
    # Verify the returned user detail is correct
    assert resp.json()["id"] == str(user.id)


@pytest.mark.asyncio
async def test_reset_password_not_found(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    import uuid
    resp = await client.put(
        f"/api/v1/admin/users/{uuid.uuid4()}/reset-password",
        headers=legacy_headers(),
        json={"new_password": "newpassword123"},
    )
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_reset_password_too_short(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}/reset-password",
        headers=legacy_headers(),
        json={"new_password": "abc"},
    )
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# PUT /api/v1/admin/users/{user_id}/status
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_toggle_status_ban_user(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]  # active user
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}/status",
        headers=legacy_headers(),
        json={"target_status": "banned"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "banned"


@pytest.mark.asyncio
async def test_toggle_status_activate_user(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[4]  # banned app user (index 4)
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}/status",
        headers=legacy_headers(),
        json={"target_status": "active"},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "active"


@pytest.mark.asyncio
async def test_toggle_status_invalid_value(client: AsyncClient, monkeypatch, seed_users):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = seed_users[0]
    resp = await client.put(
        f"/api/v1/admin/users/{user.id}/status",
        headers=legacy_headers(),
        json={"target_status": "invalid_status"},
    )
    assert resp.status_code == 400


@pytest.mark.asyncio
async def test_toggle_status_not_found(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    import uuid
    resp = await client.put(
        f"/api/v1/admin/users/{uuid.uuid4()}/status",
        headers=legacy_headers(),
        json={"target_status": "banned"},
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# DELETE /api/v1/admin/users/{user_id}
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_delete_user(client: AsyncClient, monkeypatch, db_session):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    user = User(
        user_type="app",
        phone="13700137001",
        nickname="Delete Me",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    resp = await client.delete(
        f"/api/v1/admin/users/{user.id}",
        headers=legacy_headers(),
    )
    assert resp.status_code == 204

    # Verify the user is gone
    resp2 = await client.get(
        f"/api/v1/admin/users/{user.id}",
        headers=legacy_headers(),
    )
    assert resp2.status_code == 404


@pytest.mark.asyncio
async def test_delete_user_not_found(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    import uuid
    resp = await client.delete(
        f"/api/v1/admin/users/{uuid.uuid4()}",
        headers=legacy_headers(),
    )
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Permission checks - unauthenticated requests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unauthenticated_list_users(client: AsyncClient):
    """No auth headers at all - get_current_admin override returns None,
    which the permission checker passes through."""
    # With the conftest override of get_current_admin -> None,
    # the permission checker returns None (passes through).
    # To test actual 401, we need to restore the original dependency.
    from app.api.dependencies import get_current_admin
    from app.main import app

    # Restore original dependency (no override)
    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.get("/api/v1/admin/users")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None


@pytest.mark.asyncio
async def test_unauthenticated_create_user(client: AsyncClient):
    from app.api.dependencies import get_current_admin
    from app.main import app

    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.post(
            "/api/v1/admin/users",
            json={
                "user_type": "app",
                "phone": "13900139003",
                "password": "testpass123",
            },
        )
        assert resp.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None


@pytest.mark.asyncio
async def test_unauthenticated_get_user(client: AsyncClient, db_session):
    from app.api.dependencies import get_current_admin
    from app.main import app

    user = User(
        user_type="app",
        phone="13700137002",
        nickname="Auth Test",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.get(f"/api/v1/admin/users/{user.id}")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None


@pytest.mark.asyncio
async def test_unauthenticated_update_user(client: AsyncClient, db_session):
    from app.api.dependencies import get_current_admin
    from app.main import app

    user = User(
        user_type="app",
        phone="13700137003",
        nickname="Auth Test",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.put(
            f"/api/v1/admin/users/{user.id}",
            json={"nickname": "Hacked"},
        )
        assert resp.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None


@pytest.mark.asyncio
async def test_unauthenticated_delete_user(client: AsyncClient, db_session):
    from app.api.dependencies import get_current_admin
    from app.main import app

    user = User(
        user_type="app",
        phone="13700137004",
        nickname="Auth Test",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.delete(f"/api/v1/admin/users/{user.id}")
        assert resp.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None


@pytest.mark.asyncio
async def test_unauthenticated_reset_password(client: AsyncClient, db_session):
    from app.api.dependencies import get_current_admin
    from app.main import app

    user = User(
        user_type="app",
        phone="13700137005",
        nickname="Auth Test",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.put(
            f"/api/v1/admin/users/{user.id}/reset-password",
            json={"new_password": "hacked123"},
        )
        assert resp.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None


@pytest.mark.asyncio
async def test_unauthenticated_toggle_status(client: AsyncClient, db_session):
    from app.api.dependencies import get_current_admin
    from app.main import app

    user = User(
        user_type="app",
        phone="13700137006",
        nickname="Auth Test",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.put(
            f"/api/v1/admin/users/{user.id}/status",
            json={"target_status": "banned"},
        )
        assert resp.status_code == 401
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None


# ---------------------------------------------------------------------------
# Permission check - non-super-admin without specific permission
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_forbidden_without_permission(client: AsyncClient, db_session):
    """Create an admin with a role that does NOT have system:user:view permission.
    Verify the endpoint returns 403."""
    from app.api.dependencies import get_current_admin
    from app.main import app

    # Role with a different permission, NOT system:user:view
    menu = AdminMenu(type="button", title="Other perm", permission_code="system:other:view")
    role = AdminRole(name="No user perm", code="no_user_perm")
    role.menus.append(menu)
    admin = User(
        user_type="admin",
        phone="",
        username="nopermadmin",
        password_hash=AdminAuthService.hash_password("secret123"),
        nickname="NoPerm",
        is_super_admin=False,
    )
    admin.roles.append(role)
    db_session.add(admin)
    await db_session.commit()

    token = AdminAuthService.create_access_token(admin.id)

    # Override get_current_admin to use the real dependency chain
    app.dependency_overrides.pop(get_current_admin, None)
    try:
        resp = await client.get(
            "/api/v1/admin/users",
            headers={"Authorization": f"Bearer {token}"},
        )
        assert resp.status_code == 403
    finally:
        app.dependency_overrides[get_current_admin] = lambda: None
