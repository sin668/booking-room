import uuid
from collections.abc import AsyncGenerator
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_admin, get_current_admin_context, require_admin_permission
from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.main import app
from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.models.admin_user import AdminUser
from app.services.admin_auth_service import AdminAuthService


@pytest.fixture
async def real_auth_client(db_session) -> AsyncGenerator[AsyncClient, None]:
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock()
    app.dependency_overrides.pop(get_current_admin, None)
    app.dependency_overrides.pop(get_current_admin_context, None)

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


@pytest.mark.asyncio
async def test_legacy_admin_token_returns_super_admin_context(monkeypatch, db_session):
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "legacy-token")

    context = await get_current_admin_context(
        credentials=None,
        x_admin_token="legacy-token",
        db=db_session,
        redis=AsyncMock(),
    )

    assert context.is_super_admin is True
    assert context.username == "legacy-admin"


@pytest.mark.asyncio
async def test_wrong_legacy_admin_token_returns_401(monkeypatch, real_auth_client):
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "legacy-token")

    resp = await real_auth_client.get(
        "/api/v1/admin/menus/routes",
        headers={"X-Admin-Token": "wrong"},
    )

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_bearer_admin_token_can_access_permissioned_route(db_session, real_auth_client):
    menu = AdminMenu(type="button", title="Menu view", permission_code="system:menu:view")
    role = AdminRole(name="Menu viewer", code="menu_viewer")
    role.menus.append(menu)
    admin = AdminUser(
        id=uuid.uuid4(),
        username="manager",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    admin.roles.append(role)
    db_session.add(admin)
    await db_session.commit()

    token = AdminAuthService.create_access_token(admin.id, settings)
    resp = await real_auth_client.get(
        "/api/v1/admin/menus",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert resp.status_code == 200


@pytest.mark.asyncio
async def test_permission_dependency_rejects_missing_permission(db_session):
    admin = AdminUser(
        id=uuid.uuid4(),
        username="manager",
        password_hash=AdminAuthService.hash_password("secret123"),
    )
    db_session.add(admin)
    await db_session.commit()

    context = await get_current_admin_context(
        credentials=type("Creds", (), {"credentials": AdminAuthService.create_access_token(admin.id, settings)})(),
        x_admin_token=None,
        db=db_session,
        redis=AsyncMock(),
    )
    checker = require_admin_permission("system:role:create")

    with pytest.raises(Exception) as exc_info:
        await checker(context)

    assert getattr(exc_info.value, "status_code", None) == 403
