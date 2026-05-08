"""Tests for API dependencies."""

import uuid
from unittest.mock import AsyncMock

import pytest
from fastapi import HTTPException
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_admin, get_current_user_id
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app


# ---------------------------------------------------------------------------
# get_current_admin tests
# ---------------------------------------------------------------------------


class TestGetCurrentAdmin:
    @pytest.mark.asyncio
    async def test_no_token(self, client: AsyncClient):
        """No admin token returns 401."""
        del app.dependency_overrides[get_current_admin]
        try:
            resp = await client.get("/api/v1/admin/activities")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None

    @pytest.mark.asyncio
    async def test_wrong_token(self, client: AsyncClient):
        """Wrong admin token returns 401."""
        del app.dependency_overrides[get_current_admin]
        try:
            resp = await client.get(
                "/api/v1/admin/activities",
                headers={"X-Admin-Token": "wrong-token"},
            )
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None


# ---------------------------------------------------------------------------
# get_current_user_id tests
# ---------------------------------------------------------------------------


class TestGetCurrentUserId:
    @pytest.mark.asyncio
    async def test_no_credentials_returns_401(self, db_session):
        """No credentials (no Authorization header) returns 401."""
        mock_redis = AsyncMock()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_redis] = lambda: mock_redis

        if get_current_user_id in app.dependency_overrides:
            del app.dependency_overrides[get_current_user_id]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/auth/me")

        assert resp.status_code == 401
        assert "未提供认证凭证" in resp.json()["detail"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_valid_token_returns_user_id(self, db_session):
        """Valid access token returns the user ID."""
        from jose import jwt
        from datetime import UTC, datetime, timedelta

        user_id = uuid.uuid4()
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        }
        token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

        mock_redis = AsyncMock()
        mock_redis.exists.return_value = 0  # not blacklisted

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_redis] = lambda: mock_redis
        if get_current_user_id in app.dependency_overrides:
            del app.dependency_overrides[get_current_user_id]

        # Seed a user so /auth/me returns 200
        from app.models.user import User
        db_session.add(User(
            id=user_id, phone="13800138000", nickname="Test",
            password_hash="hash", status="active",
        ))
        await db_session.flush()

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})

        assert resp.status_code == 200
        assert resp.json()["phone"] == "13800138000"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_invalid_token_returns_401(self, db_session):
        """Invalid token returns 401."""
        mock_redis = AsyncMock()

        async def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db
        app.dependency_overrides[get_redis] = lambda: mock_redis
        if get_current_user_id in app.dependency_overrides:
            del app.dependency_overrides[get_current_user_id]

        transport = ASGITransport(app=app)
        async with AsyncClient(transport=transport, base_url="http://test") as ac:
            resp = await ac.get("/api/v1/auth/me", headers={"Authorization": "Bearer invalid.token.here"})

        assert resp.status_code == 401

        app.dependency_overrides.clear()
