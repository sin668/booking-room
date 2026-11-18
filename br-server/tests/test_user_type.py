"""用户类型（super-admin/normal-user）：创建/更新生效，设超管清空角色关联。"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.models.admin_role import AdminRole, admin_user_roles
from app.models.user import User
from app.services.admin_auth_service import AdminAuthService


def legacy_headers():
    return {"X-Admin-Token": "test-admin-token"}


@pytest.fixture
async def admin_user(db_session):
    user = User(
        user_source="admin",
        username="typeuser",
        nickname="类型用户",
        password_hash=AdminAuthService.hash_password("secret123"),
        status="active",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def role(db_session):
    r = AdminRole(name="测试角色", code="test_role")
    db_session.add(r)
    await db_session.commit()
    await db_session.refresh(r)
    return r


@pytest.mark.asyncio
async def test_create_super_admin(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_source": "admin",
            "user_type": "super-admin",
            "username": "superadmin1",
            "password": "secret123",
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["user_source"] == "admin"
    assert body["user_type"] == "super-admin"

    listing = (
        await client.get(
            "/api/v1/admin/users", headers=legacy_headers(), params={"keyword": "superadmin1"}
        )
    ).json()
    assert listing["items"][0]["user_type"] == "super-admin"


@pytest.mark.asyncio
async def test_create_admin_defaults_normal_user(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_source": "admin",
            "username": "normaladmin1",
            "password": "secret123",
        },
    )
    assert resp.status_code == 201
    assert resp.json()["user_type"] == "normal-user"


@pytest.mark.asyncio
async def test_create_app_user_forced_normal_user(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_source": "app",
            "user_type": "super-admin",
            "phone": "13900001111",
            "password": "secret123",
        },
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]
    value = (
        await db_session.execute(select(User.user_type).where(User.id == uuid.UUID(user_id)))
    ).scalar_one()
    assert value == "normal-user"


@pytest.mark.asyncio
async def test_create_invalid_user_type_rejected(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_source": "admin",
            "user_type": "invalid",
            "username": "badtype1",
            "password": "secret123",
        },
    )
    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_to_super_clears_roles(client: AsyncClient, db_session, monkeypatch, admin_user, role):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    await db_session.execute(admin_user_roles.insert().values(user_id=admin_user.id, admin_role_id=role.id))
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=legacy_headers(),
        json={"user_type": "super-admin"},
    )
    assert resp.status_code == 200
    assert resp.json()["user_type"] == "super-admin"
    assert resp.json()["roles"] == []

    remaining = (
        await db_session.execute(
            select(admin_user_roles).where(admin_user_roles.c.user_id == admin_user.id)
        )
    ).all()
    assert remaining == []


@pytest.mark.asyncio
async def test_update_to_normal_keeps_roles(client: AsyncClient, db_session, monkeypatch, admin_user, role):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=legacy_headers(),
        json={"user_type": "normal-user", "role_ids": [role.id]},
    )
    assert resp.status_code == 200
    assert resp.json()["user_type"] == "normal-user"
    assert [r["id"] for r in resp.json()["roles"]] == [role.id]