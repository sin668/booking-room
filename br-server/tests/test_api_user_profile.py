import uuid
from datetime import datetime, timedelta
from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.core.redis import get_redis
from app.main import app
from app.models.user import User


FIXED_USER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
async def profile_client(db_session):
    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: AsyncMock()
    app.dependency_overrides[get_current_user_id] = lambda: FIXED_USER_ID

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


async def _create_user(db_session, **overrides) -> User:
    values = {
        "id": FIXED_USER_ID,
        "phone": "13800138000",
        "username": "Luna48392",
        "nickname": "学习达人",
        "password_hash": "hashed",
        "status": "active",
    }
    values.update(overrides)
    user = User(**values)
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_get_current_user_profile_returns_username_fields(profile_client, db_session):
    await _create_user(db_session)

    resp = await profile_client.get("/api/v1/users/me")

    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "Luna48392"
    assert "username_updated_at" in data
    assert "balance" not in data
    assert "roles" not in data
    assert "invite_code" not in data


@pytest.mark.asyncio
async def test_update_username_success_sets_cooldown_timestamp(profile_client, db_session):
    await _create_user(db_session, username_updated_at=None)

    resp = await profile_client.patch("/api/v1/users/me", json={"username": "LunaStudy01"})

    assert resp.status_code == 200
    data = resp.json()
    assert data["username"] == "LunaStudy01"
    assert data["username_updated_at"] is not None


@pytest.mark.asyncio
async def test_update_username_rejects_duplicate(profile_client, db_session):
    await _create_user(db_session)
    db_session.add(
        User(
            phone="13900139000",
            username="TakenName1",
            nickname="taken",
            password_hash="hashed",
        )
    )
    await db_session.flush()

    resp = await profile_client.patch("/api/v1/users/me", json={"username": "TakenName1"})

    assert resp.status_code == 409
    assert resp.json()["detail"] == "该用户名已存在"


@pytest.mark.asyncio
async def test_update_username_rejects_invalid_format(profile_client, db_session):
    await _create_user(db_session)

    resp = await profile_client.patch("/api/v1/users/me", json={"username": "中文用户123"})

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_update_username_rejects_cooldown(profile_client, db_session):
    await _create_user(db_session, username_updated_at=datetime.now() - timedelta(hours=1))

    resp = await profile_client.patch("/api/v1/users/me", json={"username": "LunaStudy01"})

    assert resp.status_code == 429
    data = resp.json()
    assert data["detail"] == "用户名修改后 24 小时内不可再次修改"
    assert data["retry_after_seconds"] > 0


@pytest.mark.asyncio
async def test_update_nickname_does_not_require_username_cooldown(profile_client, db_session):
    await _create_user(db_session, username_updated_at=datetime.now() - timedelta(hours=1))

    resp = await profile_client.patch("/api/v1/users/me", json={"nickname": "新昵称"})

    assert resp.status_code == 200
    assert resp.json()["nickname"] == "新昵称"


@pytest.mark.asyncio
async def test_update_profile_rejects_protected_fields(profile_client, db_session):
    await _create_user(db_session)

    resp = await profile_client.patch("/api/v1/users/me", json={"balance": 999})

    assert resp.status_code == 422
