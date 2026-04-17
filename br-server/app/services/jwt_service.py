"""JWT token utilities for authentication and token management."""

import uuid
from datetime import UTC, datetime, timedelta
from uuid import UUID

import redis.asyncio as aioredis
from fastapi import HTTPException, status
from jose import JWTError, jwt

from app.core.config import Settings


class JWTService:
    """Service for creating, verifying, and managing JWT tokens."""

    def __init__(self, config: Settings, redis: aioredis.Redis) -> None:
        self._config = config
        self._redis = redis

    def create_access_token(self, user_id: UUID) -> str:
        """Create a short-lived access token.

        Payload contains:
        - sub: user UUID as string
        - type: "access"
        - exp: now + ACCESS_TOKEN_EXPIRE_MINUTES
        """
        now = datetime.now(UTC)
        expire = now + timedelta(minutes=self._config.ACCESS_TOKEN_EXPIRE_MINUTES)
        payload = {
            "sub": str(user_id),
            "type": "access",
            "exp": expire,
        }
        return jwt.encode(payload, self._config.JWT_SECRET_KEY, algorithm=self._config.JWT_ALGORITHM)

    def create_refresh_token(self, user_id: UUID) -> str:
        """Create a long-lived refresh token with a unique jti.

        Payload contains:
        - sub: user UUID as string
        - type: "refresh"
        - exp: now + REFRESH_TOKEN_EXPIRE_DAYS
        - jti: unique token identifier (uuid4)
        """
        now = datetime.now(UTC)
        expire = now + timedelta(days=self._config.REFRESH_TOKEN_EXPIRE_DAYS)
        payload = {
            "sub": str(user_id),
            "type": "refresh",
            "exp": expire,
            "jti": str(uuid.uuid4()),
        }
        return jwt.encode(payload, self._config.JWT_SECRET_KEY, algorithm=self._config.JWT_ALGORITHM)

    def verify_token(self, token: str) -> dict:
        """Decode and return the token payload.

        Raises HTTPException 401 if the token is expired or invalid.
        """
        try:
            payload = jwt.decode(
                token,
                self._config.JWT_SECRET_KEY,
                algorithms=[self._config.JWT_ALGORITHM],
            )
            return payload
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的令牌",
            ) from exc

    async def blacklist_token(self, token: str, payload: dict) -> None:
        """Store the token in the Redis blacklist with TTL = remaining expiration.

        Key: ``token:blacklist:{jti}``  (falls back to sub if no jti).
        """
        jti = payload.get("jti", payload.get("sub", uuid.uuid4()))
        exp = payload.get("exp")
        if exp is None:
            return
        remaining_seconds = int(exp - datetime.now(UTC).timestamp())
        if remaining_seconds <= 0:
            return
        key = f"token:blacklist:{jti}"
        await self._redis.setex(key, remaining_seconds, "1")

    async def is_blacklisted(self, jti: str) -> bool:
        """Check whether a token (by jti) is in the Redis blacklist."""
        key = f"token:blacklist:{jti}"
        result = await self._redis.exists(key)
        return bool(result)

    async def store_refresh_token(self, user_id: UUID, jti: str) -> None:
        """Store a refresh token reference in Redis.

        Key: ``refresh:{user_id}:{jti}``, TTL = 7 days.
        """
        key = f"refresh:{user_id}:{jti}"
        ttl = self._config.REFRESH_TOKEN_EXPIRE_DAYS * 86400  # days -> seconds
        await self._redis.setex(key, ttl, "1")

    async def revoke_refresh_token(self, user_id: UUID, jti: str) -> None:
        """Delete a refresh token reference from Redis."""
        key = f"refresh:{user_id}:{jti}"
        await self._redis.delete(key)

    async def is_refresh_token_valid(self, user_id: UUID, jti: str) -> bool:
        """Check whether a refresh token is still valid (present in Redis)."""
        key = f"refresh:{user_id}:{jti}"
        result = await self._redis.exists(key)
        return bool(result)

    async def rotate_refresh_token(self, user_id: UUID, old_jti: str) -> tuple[str, str, str] | None:
        """Rotate a refresh token: create a new one, store it, revoke the old one.

        Returns (new_refresh_token, new_jti, user_id_str) on success.
        Returns ``None`` if the old token was already revoked (reuse detected),
        in which case **all** refresh tokens for the user are revoked.
        """
        old_valid = await self.is_refresh_token_valid(user_id, old_jti)
        if not old_valid:
            # Reuse detected -- revoke all refresh tokens for this user
            pattern = f"refresh:{user_id}:*"
            keys = await self._redis.keys(pattern)
            for key in keys:
                await self._redis.delete(key)
            return None

        # Revoke the old token
        await self.revoke_refresh_token(user_id, old_jti)

        # Create and store a new refresh token
        new_refresh_token = self.create_refresh_token(user_id)
        new_payload = jwt.decode(
            new_refresh_token,
            self._config.JWT_SECRET_KEY,
            algorithms=[self._config.JWT_ALGORITHM],
        )
        new_jti = new_payload["jti"]
        await self.store_refresh_token(user_id, new_jti)

        return (new_refresh_token, new_jti, str(user_id))

    async def get_current_user_id(self, token: str) -> UUID:
        """FastAPI Depends-compatible callable.

        Decodes the token, checks blacklist, and returns the user UUID.
        Raises HTTPException 401 on any failure.
        """
        payload = self.verify_token(token)

        token_type = payload.get("type")
        if token_type != "access":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌类型无效",
            )

        jti = payload.get("jti")
        if jti and await self.is_blacklisted(jti):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌已被撤销",
            )

        user_id_str = payload.get("sub")
        if user_id_str is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌无效",
            )

        try:
            return UUID(user_id_str)
        except ValueError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="令牌中用户标识无效",
            ) from exc
