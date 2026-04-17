"""Unit tests for JWTService."""

from __future__ import annotations

import time
import uuid
from datetime import UTC, datetime, timedelta
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch
from uuid import UUID

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.services.jwt_service import JWTService


def _mock_keys_result(items: list[str]) -> AsyncMock:
    """Return an AsyncMock whose coroutine resolves to the given list."""
    async def _coro(*_args, **_kwargs):
        return items
    mock = AsyncMock(side_effect=_coro)
    return mock


@pytest.fixture
def settings() -> Settings:
    """Return a Settings instance with test-friendly defaults."""
    return Settings(
        JWT_SECRET_KEY="test-secret-key-for-unit-tests",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
    )


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Return a mock Redis client."""
    return AsyncMock()


@pytest.fixture
def jwt_service(settings: Settings, mock_redis: AsyncMock) -> JWTService:
    """Return a JWTService instance with mocked Redis."""
    return JWTService(settings, mock_redis)


@pytest.fixture
def user_id() -> UUID:
    """Return a fixed UUID for testing."""
    return UUID("12345678-1234-5678-1234-567812345678")


# ---------------------------------------------------------------------------
# create_access_token
# ---------------------------------------------------------------------------


class TestCreateAccessToken:
    async def test_create_access_token(self, jwt_service: JWTService, user_id: UUID) -> None:
        """Access token is created and contains expected claims."""
        token = jwt_service.create_access_token(user_id)

        assert isinstance(token, str)
        assert len(token) > 0

        # Decode without verification to inspect payload
        from jose import jwt

        payload = jwt.decode(
            token,
            jwt_service._config.JWT_SECRET_KEY,
            algorithms=[jwt_service._config.JWT_ALGORITHM],
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"
        assert "exp" in payload

    async def test_create_access_token_expiry(self, jwt_service: JWTService, user_id: UUID) -> None:
        """Access token expires at the configured number of minutes from now."""
        token = jwt_service.create_access_token(user_id)

        from jose import jwt

        payload = jwt.decode(
            token,
            jwt_service._config.JWT_SECRET_KEY,
            algorithms=[jwt_service._config.JWT_ALGORITHM],
        )
        exp = datetime.fromtimestamp(payload["exp"], tz=UTC)
        now = datetime.now(UTC)
        delta = (exp - now).total_seconds()
        expected_seconds = jwt_service._config.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        assert abs(delta - expected_seconds) < 5  # allow 5s tolerance


# ---------------------------------------------------------------------------
# create_refresh_token
# ---------------------------------------------------------------------------


class TestCreateRefreshToken:
    async def test_create_refresh_token(self, jwt_service: JWTService, user_id: UUID) -> None:
        """Refresh token contains sub, type=refresh, exp, and jti."""
        token = jwt_service.create_refresh_token(user_id)

        from jose import jwt

        payload = jwt.decode(
            token,
            jwt_service._config.JWT_SECRET_KEY,
            algorithms=[jwt_service._config.JWT_ALGORITHM],
        )
        assert payload["sub"] == str(user_id)
        assert payload["type"] == "refresh"
        assert "exp" in payload
        assert "jti" in payload
        assert isinstance(payload["jti"], str)

    async def test_create_refresh_token_unique_jti(self, jwt_service: JWTService, user_id: UUID) -> None:
        """Each refresh token gets a unique jti."""
        token_a = jwt_service.create_refresh_token(user_id)
        token_b = jwt_service.create_refresh_token(user_id)

        from jose import jwt

        alg = jwt_service._config.JWT_ALGORITHM
        secret = jwt_service._config.JWT_SECRET_KEY
        payload_a = jwt.decode(token_a, secret, algorithms=[alg])
        payload_b = jwt.decode(token_b, secret, algorithms=[alg])
        assert payload_a["jti"] != payload_b["jti"]


# ---------------------------------------------------------------------------
# verify_token
# ---------------------------------------------------------------------------


class TestVerifyToken:
    async def test_verify_token_valid(self, jwt_service: JWTService, user_id: UUID) -> None:
        """verify_token returns payload for a valid token."""
        token = jwt_service.create_access_token(user_id)
        payload = jwt_service.verify_token(token)

        assert payload["sub"] == str(user_id)
        assert payload["type"] == "access"

    async def test_verify_token_expired(self, jwt_service: JWTService, user_id: UUID) -> None:
        """verify_token raises HTTPException 401 for an expired token."""
        # Create a token that is already expired
        from jose import jwt

        now = datetime.now(UTC)
        expired_payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": now - timedelta(seconds=10),
        }
        expired_token = jwt.encode(
            expired_payload,
            jwt_service._config.JWT_SECRET_KEY,
            algorithm=jwt_service._config.JWT_ALGORITHM,
        )

        with pytest.raises(HTTPException) as exc_info:
            jwt_service.verify_token(expired_token)
        assert exc_info.value.status_code == 401

    async def test_verify_token_invalid_signature(self, jwt_service: JWTService, user_id: UUID) -> None:
        """verify_token raises HTTPException 401 for a token with wrong secret."""
        from jose import jwt

        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(UTC) + timedelta(minutes=15),
        }
        bad_token = jwt.encode(payload, "wrong-secret", algorithm="HS256")

        with pytest.raises(HTTPException) as exc_info:
            jwt_service.verify_token(bad_token)
        assert exc_info.value.status_code == 401


# ---------------------------------------------------------------------------
# blacklist_token / is_blacklisted
# ---------------------------------------------------------------------------


class TestBlacklist:
    async def test_blacklist_token(self, jwt_service: JWTService, user_id: UUID) -> None:
        """blacklist_token stores the jti in Redis with correct TTL."""
        jti = "test-jti-123"
        exp = int((datetime.now(UTC) + timedelta(minutes=10)).timestamp())
        payload = {"sub": str(user_id), "jti": jti, "exp": exp}

        await jwt_service.blacklist_token("dummy-token", payload)

        jwt_service._redis.setex.assert_called_once()
        call_args = jwt_service._redis.setex.call_args
        key = call_args[0][0]
        ttl = call_args[0][1]
        assert key == f"token:blacklist:{jti}"
        assert ttl > 0

    async def test_is_blacklisted(self, jwt_service: JWTService) -> None:
        """is_blacklisted returns True when key exists in Redis."""
        jwt_service._redis.exists.return_value = 1
        assert await jwt_service.is_blacklisted("some-jti") is True

        jwt_service._redis.exists.return_value = 0
        assert await jwt_service.is_blacklisted("missing-jti") is False

    async def test_blacklist_token_no_exp(self, jwt_service: JWTService, user_id: UUID) -> None:
        """blacklist_token is a no-op when payload has no exp."""
        payload = {"sub": str(user_id), "jti": "jti-no-exp"}
        await jwt_service.blacklist_token("dummy", payload)
        jwt_service._redis.setex.assert_not_called()


# ---------------------------------------------------------------------------
# refresh token rotation & reuse detection
# ---------------------------------------------------------------------------


class TestRefreshTokenRotation:
    async def test_refresh_token_rotation(self, jwt_service: JWTService, user_id: UUID, mock_redis: AsyncMock) -> None:
        """rotate_refresh_token creates a new RT, stores it, and revokes the old one."""
        old_jti = "old-jti-456"

        # Old token is valid
        mock_redis.exists.return_value = 1

        result = await jwt_service.rotate_refresh_token(user_id, old_jti)

        assert result is not None
        new_rt, new_jti, user_id_str = result
        assert isinstance(new_rt, str)
        assert isinstance(new_jti, str)
        assert user_id_str == str(user_id)

        # Old token should have been deleted
        mock_redis.delete.assert_called_with(f"refresh:{user_id}:{old_jti}")

        # New token should have been stored
        setex_calls = [call for call in mock_redis.setex.call_args_list]
        stored_key = setex_calls[-1][0][0]
        assert stored_key == f"refresh:{user_id}:{new_jti}"

    async def test_refresh_token_reuse_detection(self, jwt_service: JWTService, user_id: UUID, mock_redis: AsyncMock) -> None:
        """rotate_refresh_token returns None and revokes all RTs on reuse."""
        old_jti = "reused-jti"

        # Old token is NOT valid (already revoked -> reuse)
        mock_redis.exists.return_value = 0
        mock_redis.keys.return_value = [f"refresh:{user_id}:other-jti"]

        result = await jwt_service.rotate_refresh_token(user_id, old_jti)

        assert result is None
        mock_redis.delete.assert_called_with(f"refresh:{user_id}:other-jti")


# ---------------------------------------------------------------------------
# store / revoke / validate refresh token
# ---------------------------------------------------------------------------


class TestRefreshTokenStorage:
    async def test_store_refresh_token(self, jwt_service: JWTService, user_id: UUID, mock_redis: AsyncMock) -> None:
        """store_refresh_token stores with correct key and TTL."""
        jti = "jti-store-test"
        await jwt_service.store_refresh_token(user_id, jti)

        mock_redis.setex.assert_called_once_with(
            f"refresh:{user_id}:{jti}",
            jwt_service._config.REFRESH_TOKEN_EXPIRE_DAYS * 86400,
            "1",
        )

    async def test_revoke_refresh_token(self, jwt_service: JWTService, user_id: UUID, mock_redis: AsyncMock) -> None:
        """revoke_refresh_token deletes the key from Redis."""
        jti = "jti-revoke-test"
        await jwt_service.revoke_refresh_token(user_id, jti)
        mock_redis.delete.assert_called_with(f"refresh:{user_id}:{jti}")

    async def test_is_refresh_token_valid(self, jwt_service: JWTService, user_id: UUID, mock_redis: AsyncMock) -> None:
        """is_refresh_token_valid checks Redis existence."""
        mock_redis.exists.return_value = 1
        assert await jwt_service.is_refresh_token_valid(user_id, "valid-jti") is True

        mock_redis.exists.return_value = 0
        assert await jwt_service.is_refresh_token_valid(user_id, "invalid-jti") is False


# ---------------------------------------------------------------------------
# get_current_user_id
# ---------------------------------------------------------------------------


class TestGetCurrentUserId:
    async def test_get_current_user_id(self, jwt_service: JWTService, user_id: UUID, mock_redis: AsyncMock) -> None:
        """get_current_user_id returns the user UUID from a valid access token."""
        token = jwt_service.create_access_token(user_id)
        mock_redis.exists.return_value = 0  # not blacklisted

        result = await jwt_service.get_current_user_id(token)
        assert result == user_id

    async def test_get_current_user_id_blacklisted(self, jwt_service: JWTService, user_id: UUID, mock_redis: AsyncMock) -> None:
        """get_current_user_id raises 401 for a blacklisted token."""
        # Create a token with a jti (refresh tokens have jti; we add one to access token manually for this test)
        from jose import jwt

        now = datetime.now(UTC)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": now + timedelta(minutes=15),
            "jti": "blacklisted-jti",
        }
        token = jwt.encode(
            payload,
            jwt_service._config.JWT_SECRET_KEY,
            algorithm=jwt_service._config.JWT_ALGORITHM,
        )
        mock_redis.exists.return_value = 1  # blacklisted

        with pytest.raises(HTTPException) as exc_info:
            await jwt_service.get_current_user_id(token)
        assert exc_info.value.status_code == 401

    async def test_get_current_user_id_wrong_type(self, jwt_service: JWTService, user_id: UUID) -> None:
        """get_current_user_id raises 401 when token type is not 'access'."""
        token = jwt_service.create_refresh_token(user_id)
        with pytest.raises(HTTPException) as exc_info:
            await jwt_service.get_current_user_id(token)
        assert exc_info.value.status_code == 401

    async def test_get_current_user_id_expired(self, jwt_service: JWTService, user_id: UUID) -> None:
        """get_current_user_id raises 401 for an expired token."""
        from jose import jwt

        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": datetime.now(UTC) - timedelta(seconds=10),
        }
        expired_token = jwt.encode(
            payload,
            jwt_service._config.JWT_SECRET_KEY,
            algorithm=jwt_service._config.JWT_ALGORITHM,
        )
        with pytest.raises(HTTPException) as exc_info:
            await jwt_service.get_current_user_id(expired_token)
        assert exc_info.value.status_code == 401
