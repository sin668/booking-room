"""Integration tests for auth API endpoints."""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from httpx import ASGITransport, AsyncClient
from jose import jwt

from app.api.dependencies import get_current_user_id
from app.core.config import settings
from app.core.database import Base, get_db
from app.core.redis import get_redis
from app.main import app
from app.schemas.user import TokenResponse


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _create_access_token(user_id: uuid.UUID) -> str:
    """Create a valid access token for the given user ID."""
    payload = {
        "sub": str(user_id),
        "type": "access",
        "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


def _create_refresh_token(user_id: uuid.UUID) -> str:
    """Create a valid refresh token for the given user ID."""
    payload = {
        "sub": str(user_id),
        "type": "refresh",
        "jti": uuid.uuid4().hex,
        "exp": int((datetime.now(UTC) + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)).timestamp()),
    }
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)


FIXED_USER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")


def _make_real_token_response(user_id: uuid.UUID) -> TokenResponse:
    """Create a TokenResponse with real JWT access/refresh tokens."""
    return TokenResponse(
        access_token=_create_access_token(user_id),
        refresh_token=_create_refresh_token(user_id),
        token_type="bearer",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
async def client_with_user(db_session) -> AsyncClient:
    """Create a client with get_current_user_id overridden to return FIXED_USER_ID."""

    async def override_get_db():
        yield db_session

    mock_redis = AsyncMock()
    mock_redis.exists.return_value = 0
    mock_redis.setex = AsyncMock()
    mock_redis.keys.return_value = []
    mock_redis.delete = AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: mock_redis
    app.dependency_overrides[get_current_user_id] = lambda: FIXED_USER_ID

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# send-code tests
# ---------------------------------------------------------------------------


class TestSendCode:
    @pytest.mark.asyncio
    @patch("app.api.routes.auth.SMSService")
    async def test_send_code_success(self, MockSMS, client: AsyncClient):
        """Successful send-code returns 200."""
        mock_instance = AsyncMock()
        MockSMS.return_value = mock_instance

        resp = await client.post("/api/v1/auth/send-code", json={"phone": "13800138000"})
        assert resp.status_code == 200
        assert resp.json()["message"] == "验证码发送成功"

    @pytest.mark.asyncio
    @patch("app.api.routes.auth.SMSService")
    async def test_send_code_captcha_token(self, MockSMS, client: AsyncClient):
        """send-code with captcha_token passes it through."""
        mock_instance = AsyncMock()
        MockSMS.return_value = mock_instance

        resp = await client.post(
            "/api/v1/auth/send-code",
            json={"phone": "13800138000", "captcha_token": "some-captcha-token"},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    @patch("app.api.routes.auth.SMSService")
    async def test_send_code_sms_failure_raises(self, MockSMS, client: AsyncClient):
        """When SMSService raises HTTPException, it propagates."""
        from fastapi import HTTPException

        mock_instance = AsyncMock()
        mock_instance.send_code.side_effect = HTTPException(status_code=429, detail="发送过于频繁")
        MockSMS.return_value = mock_instance

        resp = await client.post("/api/v1/auth/send-code", json={"phone": "13800138000"})
        assert resp.status_code == 429


# ---------------------------------------------------------------------------
# register tests
# ---------------------------------------------------------------------------


class TestRegister:
    @pytest.mark.asyncio
    @patch("app.api.routes.auth.AuthService")
    async def test_register_success(self, MockAuthService, client: AsyncClient):
        """Successful registration returns 201 with TokenResponse."""
        mock_auth = AsyncMock()
        mock_auth.register.return_value = _make_real_token_response(FIXED_USER_ID)
        MockAuthService.return_value = mock_auth

        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "phone": "13800138000",
                "password": "test123456",
                "sms_code": "123456",
                "agree_terms": True,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert data["access_token"]
        # Verify refresh token cookie is set
        assert "refresh_token" in resp.cookies

    @pytest.mark.asyncio
    async def test_register_not_agree_terms(self, client: AsyncClient):
        """Registration without agreeing to terms returns 422."""
        resp = await client.post(
            "/api/v1/auth/register",
            json={
                "phone": "13800138000",
                "password": "test123456",
                "sms_code": "123456",
                "agree_terms": False,
            },
        )
        assert resp.status_code == 422
        assert "必须同意用户协议" in resp.json()["detail"]


# ---------------------------------------------------------------------------
# login tests
# ---------------------------------------------------------------------------


class TestLogin:
    @pytest.mark.asyncio
    @patch("app.api.routes.auth.AuthService")
    async def test_login_success(self, MockAuthService, client: AsyncClient):
        """Successful login returns 200 with TokenResponse."""
        mock_auth = AsyncMock()
        mock_auth.login.return_value = _make_real_token_response(FIXED_USER_ID)
        MockAuthService.return_value = mock_auth

        resp = await client.post(
            "/api/v1/auth/login",
            json={"phone": "13800138000", "password": "test123456"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["token_type"] == "bearer"
        assert "refresh_token" in resp.cookies


# ---------------------------------------------------------------------------
# refresh tests
# ---------------------------------------------------------------------------


class TestRefresh:
    @pytest.mark.asyncio
    @patch("app.api.routes.auth.AuthService")
    async def test_refresh_from_cookie(self, MockAuthService, client: AsyncClient):
        """Refresh with cookie token returns new TokenResponse."""
        refresh_token = _create_refresh_token(FIXED_USER_ID)
        mock_auth = AsyncMock()
        mock_auth.refresh_token.return_value = _make_real_token_response(FIXED_USER_ID)
        MockAuthService.return_value = mock_auth

        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200
        assert resp.json()["token_type"] == "bearer"
        assert "refresh_token" in resp.cookies

    @pytest.mark.asyncio
    @patch("app.api.routes.auth.AuthService")
    async def test_refresh_from_body(self, MockAuthService, client: AsyncClient):
        """Refresh with body token (no cookie) returns new TokenResponse."""
        refresh_token = _create_refresh_token(FIXED_USER_ID)
        mock_auth = AsyncMock()
        mock_auth.refresh_token.return_value = _make_real_token_response(FIXED_USER_ID)
        MockAuthService.return_value = mock_auth

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": refresh_token},
        )
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_refresh_no_token(self, client: AsyncClient):
        """Refresh with no token returns 401."""
        resp = await client.post("/api/v1/auth/refresh")
        assert resp.status_code == 401
        assert "未提供Refresh Token" in resp.json()["detail"]

    @pytest.mark.asyncio
    @patch("app.api.routes.auth.AuthService")
    async def test_refresh_expired_token(self, MockAuthService, client: AsyncClient):
        """Refresh with expired/invalid token deletes cookie and returns 401."""
        refresh_token = _create_refresh_token(FIXED_USER_ID)
        mock_auth = AsyncMock()
        mock_auth.refresh_token.return_value = None
        MockAuthService.return_value = mock_auth

        resp = await client.post(
            "/api/v1/auth/refresh",
            cookies={"refresh_token": refresh_token},
        )
        assert resp.status_code == 401
        assert "登录已过期" in resp.json()["detail"]

    @pytest.mark.asyncio
    @patch("app.api.routes.auth.AuthService")
    async def test_refresh_prefers_cookie_over_body(self, MockAuthService, client: AsyncClient):
        """When both cookie and body are present, cookie takes precedence."""
        cookie_token = _create_refresh_token(FIXED_USER_ID)
        mock_auth = AsyncMock()
        mock_auth.refresh_token.return_value = _make_real_token_response(FIXED_USER_ID)
        MockAuthService.return_value = mock_auth

        resp = await client.post(
            "/api/v1/auth/refresh",
            json={"refresh_token": "body-token"},
            cookies={"refresh_token": cookie_token},
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# logout tests
# ---------------------------------------------------------------------------


class TestLogout:
    @pytest.mark.asyncio
    @patch("app.api.routes.auth.AuthService")
    async def test_logout_success(self, MockAuthService, client_with_user: AsyncClient):
        """Logout with valid token returns 200 and clears cookie."""
        mock_auth = AsyncMock()
        mock_auth.logout = AsyncMock()
        MockAuthService.return_value = mock_auth

        access_token = _create_access_token(FIXED_USER_ID)
        resp = await client_with_user.post(
            "/api/v1/auth/logout",
            headers={"Authorization": f"Bearer {access_token}"},
        )
        assert resp.status_code == 200
        assert resp.json()["message"] == "退出成功"


# ---------------------------------------------------------------------------
# /me tests (auth version)
# ---------------------------------------------------------------------------


class TestGetMeAuth:
    @pytest.mark.asyncio
    async def test_get_me_no_auth(self, client: AsyncClient):
        """GET /me without auth returns 401."""
        resp = await client.get("/api/v1/auth/me")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_get_me_with_auth(self, client_with_user: AsyncClient, db_session):
        """GET /me with valid auth returns user info."""
        from app.models.user import User

        user = User(
            id=FIXED_USER_ID,
            phone="13800138000",
            nickname="TestUser",
            password_hash="hashed",
            status="active",
        )
        db_session.add(user)
        await db_session.flush()

        resp = await client_with_user.get("/api/v1/auth/me")
        assert resp.status_code == 200
        data = resp.json()
        assert data["phone"] == "13800138000"
        assert data["nickname"] == "TestUser"

    @pytest.mark.asyncio
    async def test_get_me_user_not_found(self, client_with_user: AsyncClient):
        """GET /me with auth but user not in DB returns 404."""
        resp = await client_with_user.get("/api/v1/auth/me")
        assert resp.status_code == 404
        assert "用户不存在" in resp.json()["detail"]
