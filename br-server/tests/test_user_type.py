"""用户类型（超级管理员/普通用户）：创建/更新生效，设超管清空角色关联。"""

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
        user_type="admin",
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
            "user_type": "admin",
            "username": "superadmin1",
            "password": "secret123",
            "is_super_admin": True,
        },
    )
    assert resp.status_code == 201
    body = resp.json()
    assert body["is_super_admin"] is True

    listing = (
        await client.get(
            "/api/v1/admin/users", headers=legacy_headers(), params={"keyword": "superadmin1"}
        )
    ).json()
    assert listing["items"][0]["is_super_admin"] is True


@pytest.mark.asyncio
async def test_create_app_user_ignores_super_flag(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    resp = await client.post(
        "/api/v1/admin/users",
        headers=legacy_headers(),
        json={
            "user_type": "app",
            "phone": "13900001111",
            "password": "secret123",
            "is_super_admin": True,
        },
    )
    assert resp.status_code == 201
    user_id = resp.json()["id"]
    flag = (
        await db_session.execute(select(User.is_super_admin).where(User.id == uuid.UUID(user_id)))
    ).scalar_one()
    assert flag is False


@pytest.mark.asyncio
async def test_update_to_super_clears_roles(client: AsyncClient, db_session, monkeypatch, admin_user, role):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    await db_session.execute(admin_user_roles.insert().values(user_id=admin_user.id, admin_role_id=role.id))
    await db_session.commit()

    resp = await client.put(
        f"/api/v1/admin/users/{admin_user.id}",
        headers=legacy_headers(),
        json={"is_super_admin": True},
    )
    assert resp.status_code == 200
    assert resp.json()["is_super_admin"] is True
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
        json={"is_super_admin": False, "role_ids": [role.id]},
    )
    assert resp.status_code == 200
    assert resp.json()["is_super_admin"] is False
    assert [r["id"] for r in resp.json()["roles"]] == [role.id]