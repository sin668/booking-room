"""Authentication business logic service."""

import random
import uuid
from uuid import UUID

import bcrypt
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from jose import jwt as jose_jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.user import User
from app.schemas.user import TokenResponse, UserCreate, UserLogin
from app.services.jwt_service import JWTService


class AuthService:
    """Business logic for user registration, login, token refresh, and logout."""

    def __init__(self, db: AsyncSession, redis: aioredis.Redis, config: Settings) -> None:
        self._db = db
        self._redis = redis
        self._config = config
        self._jwt = JWTService(config, redis)

    async def register(self, data: UserCreate) -> TokenResponse:
        """Register a new user and return JWT tokens.

        Steps:
        1. Verify captcha_token via CaptchaService
        2. Verify SMS code via SMSService
        3. Check phone uniqueness
        4. Validate password length (handled by Pydantic)
        5. Generate default nickname if not provided
        6. Hash password and create User record
        7. Handle invite_code if present
        8. Create JWT tokens and store refresh token
        """
        # --- Step 1: Verify captcha (skip if not configured) ---
        # When captcha_token is provided, verify it.
        # When None, captcha is disabled (e.g. dev environment).
        if data.captcha_token:
            # TODO: integrate CaptchaService when captcha is enabled
            # captcha_service = CaptchaService(self._config)
            # await captcha_service.verify(data.captcha_token)
            pass

        # --- Step 2: Verify SMS code (placeholder for SMSService integration) ---
        # In a real implementation you would call:
        #   sms_service = SMSService(self._config, self._redis)
        #   if not await sms_service.verify_code(data.phone, data.sms_code):
        #       raise HTTPException(...)
        # We import lazily to keep the module usable without sms_service present.
        try:
            from app.services.sms_service import SMSService

            sms_service = SMSService(self._redis, self._config)
            if not await sms_service.verify_code(data.phone, data.sms_code):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="短信验证码无效或已过期",
                )
        except ImportError:
            # SMSService not yet implemented -- skip SMS verification
            pass

        # --- Step 3: Check phone uniqueness ---
        stmt = select(User).where(User.phone == data.phone)
        result = await self._db.execute(stmt)
        existing_user = result.scalar_one_or_none()
        if existing_user is not None:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该手机号已注册",
            )

        # --- Step 4: Password length validation (handled by Pydantic min/max) ---
        # The UserCreate schema enforces 6 <= len(password) <= 20.

        # --- Step 5: Default nickname ---
        nickname = data.nickname
        if nickname is None:
            nickname = f"学习者{random.randint(100000, 999999)}"

        # --- Step 6: Hash password & create user ---
        password_hash = bcrypt.hashpw(
            data.password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        user = User(
            phone=data.phone,
            nickname=nickname,
            password_hash=password_hash,
            status="active",
        )
        self._db.add(user)
        await self._db.flush()  # get user.id without committing

        # --- Step 7: Invite code (placeholder) ---
        if data.invite_code:
            # TODO: implement invitation relationship logic
            # e.g. look up inviter, create an Invitation record, etc.
            pass

        # --- Step 8: Create tokens ---
        access_token = self._jwt.create_access_token(user.id)
        refresh_token = self._jwt.create_refresh_token(user.id)
        rt_payload = jose_jwt.decode(
            refresh_token,
            self._config.JWT_SECRET_KEY,
            algorithms=[self._config.JWT_ALGORITHM],
        )
        await self._jwt.store_refresh_token(user.id, rt_payload["jti"])

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self._config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def login(self, data: UserLogin) -> TokenResponse:
        """Authenticate a user by phone + password and return JWT tokens."""
        # --- Find user by phone ---
        stmt = select(User).where(User.phone == data.phone)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )

        # --- Check banned status ---
        if user.status == "banned":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已被封禁",
            )

        # --- Verify password ---
        if not bcrypt.checkpw(
            data.password.encode("utf-8"), user.password_hash.encode("utf-8")
        ):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="手机号或密码错误",
            )

        # --- Create tokens ---
        access_token = self._jwt.create_access_token(user.id)
        refresh_token = self._jwt.create_refresh_token(user.id)
        rt_payload = jose_jwt.decode(
            refresh_token,
            self._config.JWT_SECRET_KEY,
            algorithms=[self._config.JWT_ALGORITHM],
        )
        await self._jwt.store_refresh_token(user.id, rt_payload["jti"])

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self._config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def refresh_token(self, refresh_token_str: str) -> TokenResponse | None:
        """Rotate a refresh token and return new tokens.

        - If valid: rotate (new AT + new RT), return TokenResponse.
        - If reused (old RT already revoked): revoke all RT for user, return None.
        - If expired: return None.
        """
        try:
            payload = self._jwt.verify_token(refresh_token_str)
        except HTTPException:
            # Token expired or invalid
            return None

        if payload.get("type") != "refresh":
            return None

        user_id = UUID(payload["sub"])
        jti = payload.get("jti")
        if jti is None:
            return None

        result = await self._jwt.rotate_refresh_token(user_id, jti)
        if result is None:
            # Reuse detected -- caller should force re-login
            return None

        new_rt, _new_jti, _user_id_str = result
        access_token = self._jwt.create_access_token(user_id)

        return TokenResponse(
            access_token=access_token,
            token_type="bearer",
            expires_in=self._config.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
        )

    async def logout(self, token: str, payload: dict) -> None:
        """Blacklist the access token and revoke its associated refresh token."""
        # Blacklist the access token
        await self._jwt.blacklist_token(token, payload)

        # Best-effort: also revoke the refresh token if we can identify the user
        user_id_str = payload.get("sub")
        if user_id_str:
            try:
                user_id = UUID(user_id_str)
                pattern = f"refresh:{user_id}:*"
                keys = await self._redis.keys(pattern)
                for key in keys:
                    await self._redis.delete(key)
            except (ValueError, Exception):
                pass
