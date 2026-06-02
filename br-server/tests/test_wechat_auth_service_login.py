"""Tests for WeChat login service behavior."""

from __future__ import annotations

import uuid
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy import select

from app.core.config import Settings
from app.models.user import User
from app.schemas.user import TokenResponse
from app.services.wechat_auth_client import (
    WechatAuthAPIError,
    WechatAuthConfigError,
    WechatAuthHTTPError,
    WechatSession,
)
from app.services.wechat_auth_service import WechatAuthService


@pytest.fixture
def settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret-key-for-wechat-auth",
        JWT_ALGORITHM="HS256",
        ACCESS_TOKEN_EXPIRE_MINUTES=15,
        REFRESH_TOKEN_EXPIRE_DAYS=7,
        WECHAT_MINI_LOGIN_ENABLED=True,
        WECHAT_MINI_APPID="wx-appid",
        WECHAT_MINI_SECRET="wx-secret",
    )


@pytest.fixture
def redis() -> AsyncMock:
    mock = AsyncMock()
    mock.get.return_value = None
    mock.keys.return_value = []
    return mock


@pytest.fixture
def wechat_client() -> AsyncMock:
    return AsyncMock()


def _token_sub(token: str, settings: Settings) -> str:
    payload = jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )
    return payload["sub"]


@pytest.mark.asyncio
async def test_first_wechat_login_creates_phone_null_user_and_caches_session_key(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    wechat_client.jscode2session.return_value = WechatSession(
        openid="openid-new",
        session_key="session-key-new",
    )

    result = await WechatAuthService(
        db_session,
        redis,
        settings,
        wechat_client=wechat_client,
    ).wechat_login("login-code")

    user = (
        await db_session.execute(
            select(User).where(User.wechat_openid == "openid-new")
        )
    ).scalar_one()
    assert user.phone is None
    assert user.status == "active"
    assert user.user_type == "app"
    assert user.nickname.startswith("微信用户")
    assert user.username
    assert _token_sub(result.access_token, settings) == str(user.id)
    redis.setex.assert_any_await(
        "wechat:session:openid-new",
        1800,
        "session-key-new",
    )


@pytest.mark.asyncio
async def test_repeat_wechat_login_reuses_bound_user(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    user = User(
        id=uuid.uuid4(),
        phone=None,
        username="wxuser1",
        nickname="微信用户",
        password_hash="",
        status="active",
        wechat_openid="openid-existing",
    )
    db_session.add(user)
    await db_session.flush()
    wechat_client.jscode2session.return_value = WechatSession(
        openid="openid-existing",
        session_key="session-key-existing",
    )

    result = await WechatAuthService(
        db_session,
        redis,
        settings,
        wechat_client=wechat_client,
    ).wechat_login("login-code")

    assert _token_sub(result.access_token, settings) == str(user.id)
    users = (await db_session.execute(select(User))).scalars().all()
    assert len(users) == 1


@pytest.mark.asyncio
async def test_invalid_or_expired_wechat_code_maps_to_400(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    wechat_client.jscode2session.side_effect = WechatAuthAPIError(
        40029,
        "invalid code",
    )

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).wechat_login("bad-code")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "微信登录已过期，请重试"


@pytest.mark.asyncio
@pytest.mark.parametrize(
    "error",
    [
        WechatAuthConfigError("missing config"),
        WechatAuthHTTPError("network unavailable"),
    ],
)
async def test_wechat_service_unavailable_maps_to_503(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
    error: Exception,
) -> None:
    wechat_client.jscode2session.side_effect = error

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).wechat_login("login-code")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "微信登录暂不可用"


@pytest.mark.asyncio
@pytest.mark.parametrize("blocked_status", ["banned", "disabled", "deleted"])
async def test_wechat_login_for_blocked_user_returns_403(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
    blocked_status: str,
) -> None:
    db_session.add(
        User(
            id=uuid.uuid4(),
            phone=None,
            username=f"blocked_{blocked_status}",
            nickname="Blocked",
            password_hash="",
            status=blocked_status,
            wechat_openid="openid-blocked",
        )
    )
    await db_session.flush()
    wechat_client.jscode2session.return_value = WechatSession(
        openid="openid-blocked",
        session_key="session-key",
    )

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).wechat_login("login-code")

    assert exc_info.value.status_code == 403


@pytest.mark.asyncio
@patch("app.api.routes.auth.WechatAuthService")
async def test_wechat_login_route_sets_refresh_cookie(
    MockWechatAuthService,
    client,
    settings: Settings,
) -> None:
    user_id = uuid.uuid4()
    mock_service = AsyncMock()
    mock_service.wechat_login.return_value = TokenResponse(
        access_token="access-token",
        refresh_token="refresh-token",
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    MockWechatAuthService.return_value = mock_service

    response = await client.post(
        "/api/v1/auth/wechat-login",
        json={"code": "login-code"},
    )

    assert response.status_code == 200
    assert response.json()["access_token"] == "access-token"
    assert response.cookies["refresh_token"] == "refresh-token"
    mock_service.wechat_login.assert_awaited_once_with("login-code")
