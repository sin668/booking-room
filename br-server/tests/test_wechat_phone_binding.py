"""Tests for WeChat phone binding and account merge behavior."""

from __future__ import annotations

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import HTTPException
from jose import jwt
from sqlalchemy import select

from app.core.config import settings as app_settings
from app.core.config import Settings
from app.models.coupon import Coupon, UserCoupon
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.user import TokenResponse
from app.services.wechat_auth_client import (
    WechatAuthAPIError,
    WechatPhoneNumber,
)
from app.services.wechat_auth_service import WechatAuthService


@pytest.fixture
def settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret-key-for-wechat-bind",
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


def _access_token(user_id: uuid.UUID, settings: Settings) -> str:
    return jwt.encode(
        {
            "sub": str(user_id),
            "type": "access",
            "exp": int((datetime.now(UTC) + timedelta(minutes=15)).timestamp()),
        },
        settings.JWT_SECRET_KEY,
        algorithm=settings.JWT_ALGORITHM,
    )


def _token_sub(token: str, settings: Settings) -> str:
    return jwt.decode(
        token,
        settings.JWT_SECRET_KEY,
        algorithms=[settings.JWT_ALGORITHM],
    )["sub"]


async def _temp_wechat_user(db_session) -> User:
    user = User(
        id=uuid.uuid4(),
        phone=None,
        username=f"wx{uuid.uuid4().hex[:8]}",
        nickname="微信用户",
        password_hash="",
        status="active",
        wechat_openid=f"openid-{uuid.uuid4().hex[:8]}",
    )
    db_session.add(user)
    await db_session.flush()
    return user


async def _phone_user(db_session, phone: str = "13800138000") -> User:
    user = User(
        id=uuid.uuid4(),
        phone=phone,
        username=f"phone{uuid.uuid4().hex[:8]}",
        nickname="手机号用户",
        password_hash="hashed",
        status="active",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_bind_wechat_phone_code_to_new_phone(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    user = await _temp_wechat_user(db_session)
    wechat_client.get_phone_number.return_value = WechatPhoneNumber(
        phone_number="13800138000"
    )

    result = await WechatAuthService(
        db_session,
        redis,
        settings,
        wechat_client=wechat_client,
        access_token_provider=AsyncMock(return_value="wechat-access-token"),
    ).bind_phone_with_wechat_code(user.id, "phone-code")

    await db_session.refresh(user)
    assert user.phone == "13800138000"
    assert _token_sub(result.access_token, settings) == str(user.id)


@pytest.mark.asyncio
async def test_bind_phone_with_sms_to_new_phone(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    user = await _temp_wechat_user(db_session)

    with patch("app.services.wechat_auth_service.SMSService") as MockSMS:
        sms = AsyncMock()
        sms.verify_code.return_value = True
        MockSMS.return_value = sms

        result = await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).bind_phone_with_sms(user.id, "13800138000", "123456")

    await db_session.refresh(user)
    assert user.phone == "13800138000"
    assert _token_sub(result.access_token, settings) == str(user.id)


@pytest.mark.asyncio
async def test_wechat_phone_code_failure_maps_to_400(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    user = await _temp_wechat_user(db_session)
    wechat_client.get_phone_number.side_effect = WechatAuthAPIError(
        40029,
        "invalid code",
    )

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
            access_token_provider=AsyncMock(return_value="wechat-access-token"),
        ).bind_phone_with_wechat_code(user.id, "bad-phone-code")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "手机号授权已过期，请重试"


@pytest.mark.asyncio
async def test_wechat_access_token_failure_maps_to_phone_503(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    user = await _temp_wechat_user(db_session)

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
            access_token_provider=AsyncMock(side_effect=RuntimeError("token down")),
        ).bind_phone_with_wechat_code(user.id, "phone-code")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "微信手机号授权暂不可用"


@pytest.mark.asyncio
async def test_sms_code_failure_maps_to_400(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    user = await _temp_wechat_user(db_session)

    with patch("app.services.wechat_auth_service.SMSService") as MockSMS:
        sms = AsyncMock()
        sms.verify_code.return_value = False
        MockSMS.return_value = sms

        with pytest.raises(HTTPException) as exc_info:
            await WechatAuthService(
                db_session,
                redis,
                settings,
                wechat_client=wechat_client,
            ).bind_phone_with_sms(user.id, "13800138000", "000000")

    assert exc_info.value.status_code == 400
    assert exc_info.value.detail == "短信验证码无效或已过期"


@pytest.mark.asyncio
async def test_sms_service_error_maps_to_503(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    user = await _temp_wechat_user(db_session)

    with patch("app.services.wechat_auth_service.SMSService") as MockSMS:
        sms = AsyncMock()
        sms.verify_code.side_effect = RuntimeError("redis unavailable")
        MockSMS.return_value = sms

        with pytest.raises(HTTPException) as exc_info:
            await WechatAuthService(
                db_session,
                redis,
                settings,
                wechat_client=wechat_client,
            ).bind_phone_with_sms(user.id, "13800138000", "000000")

    assert exc_info.value.status_code == 503
    assert exc_info.value.detail == "短信验证码服务暂不可用"


@pytest.mark.asyncio
async def test_merge_success_moves_openid_revokes_temp_tokens_and_switches_token_subject(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    temp = await _temp_wechat_user(db_session)
    target = await _phone_user(db_session, "13800138000")
    redis.keys.return_value = [
        f"refresh:{temp.id}:old-jti",
        f"refresh:{temp.id}:other-jti",
    ]

    result = await WechatAuthService(
        db_session,
        redis,
        settings,
        wechat_client=wechat_client,
    ).bind_phone(temp.id, "13800138000")

    await db_session.refresh(temp)
    await db_session.refresh(target)
    assert target.wechat_openid is not None
    assert target.wechat_openid == temp.wechat_openid or temp.wechat_openid is None
    assert temp.wechat_openid is None
    assert temp.status == "disabled"
    assert _token_sub(result.access_token, settings) == str(target.id)
    redis.delete.assert_any_await(f"refresh:{temp.id}:old-jti")
    redis.delete.assert_any_await(f"refresh:{temp.id}:other-jti")


@pytest.mark.asyncio
async def test_merge_openid_conflict_returns_409(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    temp = await _temp_wechat_user(db_session)
    target = await _phone_user(db_session, "13800138000")
    target.wechat_openid = "other-openid"
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).bind_phone(temp.id, "13800138000")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "该手机号已绑定其他微信账号，无法合并"


@pytest.mark.asyncio
async def test_merge_temp_user_with_assets_returns_409(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    temp = await _temp_wechat_user(db_session)
    await _phone_user(db_session, "13800138000")
    db_session.add(
        WalletTransaction(
            user_id=str(temp.id),
            amount=Decimal("10.00"),
            order_id=f"order-{uuid.uuid4().hex}",
            status="paid",
        )
    )
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).bind_phone(temp.id, "13800138000")

    assert exc_info.value.status_code == 409
    assert exc_info.value.detail == "临时微信账号存在资产，无法自动合并"


@pytest.mark.asyncio
async def test_non_temp_user_binding_existing_phone_returns_409(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    current = await _phone_user(db_session, "13900139000")
    await _phone_user(db_session, "13800138000")

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).bind_phone(current.id, "13800138000")

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_bound_user_binding_unused_phone_returns_409(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    current = await _phone_user(db_session, "13900139000")

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).bind_phone(current.id, "13800138000")

    await db_session.refresh(current)
    assert exc_info.value.status_code == 409
    assert current.phone == "13900139000"


@pytest.mark.asyncio
async def test_merge_target_must_be_app_user(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    temp = await _temp_wechat_user(db_session)
    admin_user = await _phone_user(db_session, "13800138000")
    admin_user.user_type = "admin"
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).bind_phone(temp.id, "13800138000")

    await db_session.refresh(admin_user)
    assert exc_info.value.status_code == 409
    assert admin_user.wechat_openid is None


@pytest.mark.asyncio
async def test_temp_user_with_coupon_asset_returns_409(
    db_session,
    redis: AsyncMock,
    wechat_client: AsyncMock,
    settings: Settings,
) -> None:
    temp = await _temp_wechat_user(db_session)
    await _phone_user(db_session, "13800138000")
    coupon = Coupon(
        name="测试券",
        type="amount",
        discount_amount=Decimal("5.00"),
        min_order_amount=Decimal("10.00"),
        valid_from=datetime.now(UTC),
        expires_at=datetime.now(UTC) + timedelta(days=1),
    )
    db_session.add(coupon)
    await db_session.flush()
    db_session.add(UserCoupon(user_id=str(temp.id), coupon_id=coupon.id))
    await db_session.flush()

    with pytest.raises(HTTPException) as exc_info:
        await WechatAuthService(
            db_session,
            redis,
            settings,
            wechat_client=wechat_client,
        ).bind_phone(temp.id, "13800138000")

    assert exc_info.value.status_code == 409


@pytest.mark.asyncio
async def test_bind_phone_route_requires_bearer(client) -> None:
    response = await client.post(
        "/api/v1/auth/wechat/bind-phone",
        json={"code": "phone-code"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
@patch("app.api.routes.auth.WechatAuthService")
async def test_bind_phone_route_sets_refresh_cookie_and_uses_bearer_user(
    MockWechatAuthService,
    client,
) -> None:
    user_id = uuid.uuid4()
    token = _access_token(user_id, app_settings)
    mock_service = AsyncMock()
    mock_service.bind_phone_with_wechat_code.return_value = TokenResponse(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
        expires_in=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    MockWechatAuthService.return_value = mock_service

    response = await client.post(
        "/api/v1/auth/wechat/bind-phone",
        json={"code": "phone-code"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.cookies["refresh_token"] == "new-refresh-token"
    mock_service.bind_phone_with_wechat_code.assert_awaited_once_with(
        user_id,
        "phone-code",
    )


@pytest.mark.asyncio
@patch("app.api.routes.auth.WechatAuthService")
async def test_bind_phone_sms_route_sets_refresh_cookie_and_uses_bearer_user(
    MockWechatAuthService,
    client,
) -> None:
    user_id = uuid.uuid4()
    token = _access_token(user_id, app_settings)
    mock_service = AsyncMock()
    mock_service.bind_phone_with_sms.return_value = TokenResponse(
        access_token="new-access-token",
        refresh_token="new-refresh-token",
        expires_in=app_settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    MockWechatAuthService.return_value = mock_service

    response = await client.post(
        "/api/v1/auth/wechat/bind-phone/sms",
        json={"phone": "13800138000", "sms_code": "123456"},
        headers={"Authorization": f"Bearer {token}"},
    )

    assert response.status_code == 200
    assert response.cookies["refresh_token"] == "new-refresh-token"
    mock_service.bind_phone_with_sms.assert_awaited_once_with(
        user_id,
        "13800138000",
        "123456",
    )
