"""WeChat mini program login and phone binding orchestration."""

from __future__ import annotations

import random
from collections.abc import Awaitable, Callable
from decimal import Decimal
from uuid import UUID

import httpx
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.booking import Booking
from app.models.coupon import UserCoupon
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.user import TokenResponse
from app.services.auth_service import AuthService
from app.services.sms_service import SMSService
from app.services.username_service import UsernameService
from app.services.wechat_auth_client import (
    WechatAuthAPIError,
    WechatAuthConfigError,
    WechatAuthClient,
    WechatAuthHTTPError,
    WechatAuthResponseError,
)

SESSION_KEY_TTL_SECONDS = 1800
ACCESS_TOKEN_CACHE_SECONDS = 6600
AccessTokenProvider = Callable[[], Awaitable[str]]


class WechatAuthService:
    """Business rules for WeChat login, phone binding, and safe account merge."""

    def __init__(
        self,
        db: AsyncSession,
        redis: aioredis.Redis,
        config: Settings,
        *,
        wechat_client: WechatAuthClient | None = None,
        access_token_provider: AccessTokenProvider | None = None,
    ) -> None:
        self._db = db
        self._redis = redis
        self._config = config
        self._wechat_client = wechat_client or WechatAuthClient(config)
        self._access_token_provider = access_token_provider
        self._auth = AuthService(db, redis, config)

    async def wechat_login(self, code: str) -> TokenResponse:
        session = await self._exchange_login_code(code)
        await self._redis.setex(
            self._session_key_cache_key(session.openid),
            SESSION_KEY_TTL_SECONDS,
            session.session_key,
        )

        user = await self._get_user_by_openid(session.openid)
        if user is None:
            user = await self._create_wechat_user(session.openid)

        self._ensure_login_allowed(user)
        return await self._auth.issue_tokens(user.id)

    async def bind_phone_with_wechat_code(
        self,
        user_id: UUID,
        code: str,
    ) -> TokenResponse:
        access_token = await self._get_wechat_access_token()
        try:
            phone_info = await self._wechat_client.get_phone_number(
                code,
                access_token,
            )
        except WechatAuthAPIError as exc:
            raise self._map_wechat_phone_api_error(exc) from exc
        except (WechatAuthConfigError, WechatAuthHTTPError, WechatAuthResponseError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="微信手机号授权暂不可用",
            ) from exc

        return await self.bind_phone(user_id, phone_info.phone_number)

    async def bind_phone_with_sms(
        self,
        user_id: UUID,
        phone: str,
        sms_code: str,
    ) -> TokenResponse:
        sms_service = SMSService(self._redis, self._config)
        try:
            verified = await sms_service.verify_code(phone, sms_code)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="短信验证码服务暂不可用",
            ) from exc

        if not verified:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="短信验证码无效或已过期",
            )
        return await self.bind_phone(user_id, phone)

    async def bind_phone(self, user_id: UUID, phone: str) -> TokenResponse:
        current_user = await self._get_user_by_id(user_id)
        self._ensure_login_allowed(current_user)

        target_user = await self._get_user_by_phone(phone)
        if target_user is None:
            if current_user.phone is not None:
                raise self._merge_conflict()
            current_user.phone = phone
            await self._db.flush()
            return await self._auth.issue_tokens(current_user.id)

        if target_user.id == current_user.id:
            return await self._auth.issue_tokens(current_user.id)

        await self._merge_temp_wechat_user(current_user, target_user)
        return await self._auth.issue_tokens(target_user.id)

    async def _merge_temp_wechat_user(
        self,
        current_user: User,
        target_user: User,
    ) -> None:
        if not self._is_temp_wechat_user(current_user):
            raise self._merge_conflict()

        if target_user.user_type != "app":
            raise self._merge_conflict()

        if target_user.wechat_openid:
            raise self._merge_conflict("该手机号已绑定其他微信账号，无法合并")

        if await self._temp_user_has_assets(current_user):
            raise self._merge_conflict("临时微信账号存在资产，无法自动合并")

        openid = current_user.wechat_openid
        current_user.wechat_openid = None
        current_user.status = "disabled"
        await self._db.flush()
        target_user.wechat_openid = openid
        await self._revoke_all_refresh_tokens(current_user.id)
        await self._db.flush()

    async def _exchange_login_code(self, code: str):
        try:
            return await self._wechat_client.jscode2session(code)
        except WechatAuthAPIError as exc:
            raise self._map_wechat_api_error(exc) from exc
        except (WechatAuthConfigError, WechatAuthHTTPError, WechatAuthResponseError) as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="微信登录暂不可用",
            ) from exc

    def _map_wechat_api_error(self, exc: WechatAuthAPIError) -> HTTPException:
        if exc.errcode in {40029, 40163, 45011}:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="微信登录已过期，请重试",
            )
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信登录暂不可用",
        )

    def _map_wechat_phone_api_error(self, exc: WechatAuthAPIError) -> HTTPException:
        if exc.errcode in {40029, 40163, 45011}:
            return HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="手机号授权已过期，请重试",
            )
        return HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="微信手机号授权暂不可用",
        )

    async def _create_wechat_user(self, openid: str) -> User:
        username = await UsernameService(self._db).generate_unique_username()
        user = User(
            phone=None,
            username=username,
            nickname=f"微信用户{random.randint(100000, 999999)}",
            password_hash="",
            status="active",
            user_type="app",
            wechat_openid=openid,
        )
        self._db.add(user)
        await self._db.flush()
        return user

    async def _get_user_by_openid(self, openid: str) -> User | None:
        result = await self._db.execute(
            select(User).where(User.wechat_openid == openid)
        )
        return result.scalar_one_or_none()

    async def _get_user_by_phone(self, phone: str) -> User | None:
        result = await self._db.execute(select(User).where(User.phone == phone))
        return result.scalar_one_or_none()

    async def _get_user_by_id(self, user_id: UUID) -> User:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        return user

    def _ensure_login_allowed(self, user: User) -> None:
        if user.status in {"banned", "disabled"}:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号不可用",
            )

    def _is_temp_wechat_user(self, user: User) -> bool:
        return user.phone is None and bool(user.wechat_openid)

    async def _temp_user_has_assets(self, user: User) -> bool:
        if Decimal(str(user.balance or 0)) != Decimal("0"):
            return True
        user_id = str(user.id)
        checks = [
            select(exists().where(Booking.user_id == user_id)),
            select(exists().where(UserCoupon.user_id == user_id)),
            select(exists().where(WalletTransaction.user_id == user_id)),
        ]
        for stmt in checks:
            result = await self._db.execute(stmt)
            if result.scalar():
                return True
        return False

    async def _revoke_all_refresh_tokens(self, user_id: UUID) -> None:
        keys = await self._redis.keys(f"refresh:{user_id}:*")
        for key in keys:
            await self._redis.delete(key)

    async def _get_wechat_access_token(self) -> str:
        if self._access_token_provider is not None:
            try:
                return await self._access_token_provider()
            except HTTPException:
                raise
            except Exception as exc:
                raise HTTPException(
                    status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                    detail="微信手机号授权暂不可用",
                ) from exc

        cached = await self._redis.get("wechat:access_token")
        if cached:
            return cached.decode("utf-8") if isinstance(cached, bytes) else str(cached)

        try:
            self._config.require_wechat_mini_login_usable()
            async with httpx.AsyncClient(
                base_url=self._config.WECHAT_MINI_API_BASE_URL,
                timeout=self._config.WECHAT_MINI_REQUEST_TIMEOUT_SECONDS,
            ) as client:
                response = await client.get(
                    "/cgi-bin/token",
                    params={
                        "grant_type": "client_credential",
                        "appid": self._config.WECHAT_MINI_APPID,
                        "secret": self._config.WECHAT_MINI_SECRET,
                    },
                )
            data = response.json()
            if response.status_code < 200 or response.status_code >= 300:
                raise ValueError("wechat access token HTTP error")
            if data.get("errcode") not in (None, 0, "0"):
                raise ValueError("wechat access token API error")
            access_token = data.get("access_token")
            if not isinstance(access_token, str) or not access_token:
                raise ValueError("wechat access token missing")
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="微信手机号授权暂不可用",
            ) from exc

        await self._redis.setex(
            "wechat:access_token",
            ACCESS_TOKEN_CACHE_SECONDS,
            access_token,
        )
        return access_token

    @staticmethod
    def _session_key_cache_key(openid: str) -> str:
        return f"wechat:session:{openid}"

    @staticmethod
    def _merge_conflict(
        detail: str = "该手机号无法自动绑定当前微信账号",
    ) -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail,
        )
