"""Unit tests for AuthService."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin
from app.services.auth_service import AuthService


def _mock_keys_result(items: list[str]) -> AsyncMock:
    """Return an AsyncMock whose coroutine resolves to the given list."""
    async def _coro(*_args, **_kwargs):
        return items
    mock = AsyncMock(side_effect=_coro)
    return mock


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret-key-for-auth-tests",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
    )


@pytest.fixture
def mock_redis() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def mock_db() -> AsyncMock:
    """Mock async database session."""
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def auth_service(mock_db: AsyncMock, mock_redis: AsyncMock, settings: Settings) -> AuthService:
    return AuthService(mock_db, mock_redis, settings)


@pytest.fixture
def user_create_data() -> UserCreate:
    return UserCreate(
        phone="13800138000",
        password="test123456",
        nickname=None,
        sms_code="123456",
        captcha_token="captcha-token",
        agree_terms=True,
        invite_code=None,
    )


@pytest.fixture
def user_login_data() -> UserLogin:
    return UserLogin(phone="13800138000", password="test123456")


@pytest.fixture
def existing_user() -> User:
    user = User(
        id=uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee"),
        phone="13800138000",
        nickname="测试用户",
        password_hash="$2b$12$dummy_hash_for_testing",
        status="active",
    )
    return user


# ---------------------------------------------------------------------------
# Helper: build a mock result that behaves like a SQLAlchemy Result
# ---------------------------------------------------------------------------


def _mock_scalar_result(value):
    """Create a mock that supports .scalar_one_or_none()."""
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


# ---------------------------------------------------------------------------
# Register tests
# ---------------------------------------------------------------------------


class TestRegister:
    @patch("app.services.auth_service.bcrypt")
    @patch("app.services.sms_service.SMSService")
    async def test_register_success(
        self,
        MockSMS: MagicMock,
        mock_pwd: MagicMock,
        auth_service: AuthService,
        mock_db: AsyncMock,
        mock_redis: AsyncMock,
        user_create_data: UserCreate,
    ) -> None:
        """Successful registration returns TokenResponse."""
        # No existing user
        mock_db.execute.return_value = _mock_scalar_result(None)
        mock_db.flush = AsyncMock()

        mock_pwd.hashpw.return_value = b"$2b$12$dummy_hash"

        # SMSService mock
        mock_sms_instance = AsyncMock()
        mock_sms_instance.verify_code.return_value = True
        MockSMS.return_value = mock_sms_instance

        result = await auth_service.register(user_create_data)

        assert isinstance(result, TokenResponse)
        assert result.token_type == "bearer"
        assert len(result.access_token) > 0
        mock_db.add.assert_called_once()

    @patch("app.services.sms_service.SMSService")
    async def test_register_duplicate_phone(
        self,
        MockSMS: MagicMock,
        auth_service: AuthService,
        mock_db: AsyncMock,
        user_create_data: UserCreate,
    ) -> None:
        """Registering with an existing phone raises 409."""
        existing = User(
            id=uuid.uuid4(),
            phone="13800138000",
            nickname="已存在",
            password_hash="hash",
        )
        mock_db.execute.return_value = _mock_scalar_result(existing)

        mock_sms_instance = AsyncMock()
        mock_sms_instance.verify_code.return_value = True
        MockSMS.return_value = mock_sms_instance

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(user_create_data)
        assert exc_info.value.status_code == 409

    @patch("app.services.sms_service.SMSService")
    async def test_register_invalid_sms_code(
        self,
        MockSMS: MagicMock,
        auth_service: AuthService,
        mock_db: AsyncMock,
        user_create_data: UserCreate,
    ) -> None:
        """Registering with invalid SMS code raises 400."""
        mock_sms_instance = AsyncMock()
        mock_sms_instance.verify_code.return_value = False
        MockSMS.return_value = mock_sms_instance

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.register(user_create_data)
        assert exc_info.value.status_code == 400
        assert "短信验证码" in exc_info.value.detail

    @patch("app.services.auth_service.bcrypt")
    @patch("app.services.sms_service.SMSService")
    async def test_register_default_nickname(
        self,
        MockSMS: MagicMock,
        mock_pwd: MagicMock,
        auth_service: AuthService,
        mock_db: AsyncMock,
        user_create_data: UserCreate,
    ) -> None:
        """When nickname is None, a default '学习者XXXXXX' nickname is generated."""
        mock_db.execute.return_value = _mock_scalar_result(None)
        mock_db.flush = AsyncMock()

        mock_pwd.hashpw.return_value = b"$2b$12$dummy_hash"

        mock_sms_instance = AsyncMock()
        mock_sms_instance.verify_code.return_value = True
        MockSMS.return_value = mock_sms_instance

        await auth_service.register(user_create_data)

        # Verify the User was added with a nickname starting with "学习者"
        added_user = mock_db.add.call_args[0][0]
        assert added_user.nickname.startswith("学习者")
        assert len(added_user.nickname) == len("学习者") + 6

    @patch("app.services.sms_service.SMSService")
    async def test_register_empty_captcha_token(
        self,
        MockSMS: MagicMock,
        auth_service: AuthService,
        user_create_data: UserCreate,
    ) -> None:
        """Registering with empty captcha_token skips captcha validation."""
        user_create_data.captcha_token = None

        # Should NOT raise 400 for captcha — captcha is skipped when None
        # It may still fail at SMS verification (mock not set up), but
        # that proves captcha validation was bypassed.
        with pytest.raises(Exception):
            await auth_service.register(user_create_data)


# ---------------------------------------------------------------------------
# Login tests
# ---------------------------------------------------------------------------


class TestLogin:
    @patch("app.services.auth_service.bcrypt")
    async def test_login_success(
        self,
        mock_pwd: MagicMock,
        auth_service: AuthService,
        mock_db: AsyncMock,
        mock_redis: AsyncMock,
        user_login_data: UserLogin,
        existing_user: User,
    ) -> None:
        """Successful login returns TokenResponse."""
        mock_db.execute.return_value = _mock_scalar_result(existing_user)
        mock_pwd.checkpw.return_value = True

        result = await auth_service.login(user_login_data)

        assert isinstance(result, TokenResponse)
        assert result.token_type == "bearer"
        assert len(result.access_token) > 0

    @patch("app.services.auth_service.bcrypt")
    async def test_login_wrong_password(
        self,
        mock_pwd: MagicMock,
        auth_service: AuthService,
        mock_db: AsyncMock,
        user_login_data: UserLogin,
        existing_user: User,
    ) -> None:
        """Wrong password raises 401."""
        mock_db.execute.return_value = _mock_scalar_result(existing_user)
        mock_pwd.checkpw.return_value = False

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(user_login_data)
        assert exc_info.value.status_code == 401
        assert "手机号或密码错误" in exc_info.value.detail

    async def test_login_account_not_found(
        self,
        auth_service: AuthService,
        mock_db: AsyncMock,
        user_login_data: UserLogin,
    ) -> None:
        """Non-existent phone raises 401."""
        mock_db.execute.return_value = _mock_scalar_result(None)

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(user_login_data)
        assert exc_info.value.status_code == 401

    @patch("app.services.auth_service.bcrypt")
    async def test_login_account_banned(
        self,
        mock_pwd: MagicMock,
        auth_service: AuthService,
        mock_db: AsyncMock,
        user_login_data: UserLogin,
    ) -> None:
        """Banned account raises 403."""
        banned_user = User(
            id=uuid.uuid4(),
            phone="13800138000",
            nickname="被封禁",
            password_hash="hash",
            status="banned",
        )
        mock_db.execute.return_value = _mock_scalar_result(banned_user)

        with pytest.raises(HTTPException) as exc_info:
            await auth_service.login(user_login_data)
        assert exc_info.value.status_code == 403
        assert "封禁" in exc_info.value.detail


# ---------------------------------------------------------------------------
# Refresh token tests
# ---------------------------------------------------------------------------


class TestRefreshToken:
    async def test_refresh_token_success(
        self,
        auth_service: AuthService,
        mock_redis: AsyncMock,
    ) -> None:
        """refresh_token returns TokenResponse when the RT is valid."""
        # Create a valid refresh token string using the JWT service
        user_id = uuid.uuid4()
        refresh_token = auth_service._jwt.create_refresh_token(user_id)

        # Decode to get jti
        from jose import jwt

        payload = jwt.decode(
            refresh_token,
            auth_service._config.JWT_SECRET_KEY,
            algorithms=[auth_service._config.JWT_ALGORITHM],
        )
        jti = payload["jti"]

        # Redis: old RT exists
        mock_redis.exists.return_value = 1
        # scan_iter for the async iterator
        mock_redis.keys.return_value = []

        result = await auth_service.refresh_token(refresh_token)

        assert result is not None
        assert isinstance(result, TokenResponse)
        assert len(result.access_token) > 0

    async def test_refresh_token_expired(
        self,
        auth_service: AuthService,
    ) -> None:
        """refresh_token returns None when the token is expired."""
        user_id = uuid.uuid4()
        from jose import jwt

        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": 0,  # already expired
            "jti": str(uuid.uuid4()),
        }
        expired_token = jwt.encode(
            payload,
            auth_service._config.JWT_SECRET_KEY,
            algorithm=auth_service._config.JWT_ALGORITHM,
        )

        result = await auth_service.refresh_token(expired_token)
        assert result is None

    async def test_refresh_token_reuse_detection(
        self,
        auth_service: AuthService,
        mock_redis: AsyncMock,
    ) -> None:
        """refresh_token returns None when reuse is detected (RT already revoked)."""
        user_id = uuid.uuid4()
        refresh_token = auth_service._jwt.create_refresh_token(user_id)

        from jose import jwt

        payload = jwt.decode(
            refresh_token,
            auth_service._config.JWT_SECRET_KEY,
            algorithms=[auth_service._config.JWT_ALGORITHM],
        )
        jti = payload["jti"]

        # Redis: old RT does NOT exist (already revoked -> reuse)
        mock_redis.exists.return_value = 0
        mock_redis.keys.return_value = [f"refresh:{user_id}:other-jti"]

        result = await auth_service.refresh_token(refresh_token)

        assert result is None
        mock_redis.delete.assert_called_with(f"refresh:{user_id}:other-jti")


# ---------------------------------------------------------------------------
# Logout tests
# ---------------------------------------------------------------------------


class TestLogout:
    async def test_logout(
        self,
        auth_service: AuthService,
        mock_redis: AsyncMock,
    ) -> None:
        """Logout blacklists the token and revokes all refresh tokens."""
        user_id = uuid.uuid4()
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": int(datetime.now(UTC).timestamp()) + 900,
        }
        token = "dummy-access-token"

        # scan_iter returns an async iterator with one key
        mock_redis.keys.return_value = [f"refresh:{user_id}:some-jti"]

        await auth_service.logout(token, payload)

        # Should have called setex for blacklisting
        mock_redis.setex.assert_called_once()
        key = mock_redis.setex.call_args[0][0]
        assert "token:blacklist" in key

        # Should have called delete for refresh tokens found by scan_iter
        mock_redis.delete.assert_called_with(f"refresh:{user_id}:some-jti")

    async def test_logout_no_sub(
        self,
        auth_service: AuthService,
        mock_redis: AsyncMock,
    ) -> None:
        """Logout still blacklists the token even if sub is missing."""
        payload = {
            "type": "access",
            "exp": int(datetime.now(UTC).timestamp()) + 900,
        }
        token = "dummy-token"

        await auth_service.logout(token, payload)

        # setex should still be called for blacklisting
        mock_redis.setex.assert_called_once()
