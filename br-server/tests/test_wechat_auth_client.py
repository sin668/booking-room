"""Offline tests for the WeChat mini program auth client."""

from __future__ import annotations

import httpx
import pytest

from app.core.config import Settings
from app.services.wechat_auth_client import (
    WechatAuthAPIError,
    WechatAuthClient,
    WechatAuthConfigError,
    WechatAuthHTTPError,
    WechatAuthResponseError,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        WECHAT_MINI_LOGIN_ENABLED=True,
        WECHAT_MINI_APPID="wx-test-appid",
        WECHAT_MINI_SECRET="test-secret",
    )


@pytest.mark.asyncio
async def test_jscode2session_success(settings: Settings) -> None:
    async def request(**kwargs) -> httpx.Response:
        assert kwargs["method"] == "GET"
        assert kwargs["path"] == "/sns/jscode2session"
        assert kwargs["params"]["appid"] == "wx-test-appid"
        assert kwargs["params"]["secret"] == "test-secret"
        assert kwargs["params"]["js_code"] == "login-code"
        return httpx.Response(
            200,
            json={
                "openid": "openid-1",
                "session_key": "session-key-1",
                "unionid": "union-1",
            },
        )

    client = WechatAuthClient(settings, request=request)

    result = await client.jscode2session("login-code")

    assert result.openid == "openid-1"
    assert result.session_key == "session-key-1"
    assert result.unionid == "union-1"


@pytest.mark.asyncio
async def test_jscode2session_accepts_string_zero_errcode(settings: Settings) -> None:
    async def request(**kwargs) -> httpx.Response:
        return httpx.Response(
            200,
            json={
                "errcode": "0",
                "openid": "openid-1",
                "session_key": "session-key-1",
            },
        )

    client = WechatAuthClient(settings, request=request)

    result = await client.jscode2session("login-code")

    assert result.openid == "openid-1"


@pytest.mark.asyncio
async def test_jscode2session_wechat_error_raises_api_error(
    settings: Settings,
) -> None:
    async def request(**kwargs) -> httpx.Response:
        return httpx.Response(
            200,
            json={"errcode": 40029, "errmsg": "invalid code"},
        )

    client = WechatAuthClient(settings, request=request)

    with pytest.raises(WechatAuthAPIError) as exc_info:
        await client.jscode2session("bad-code")

    assert exc_info.value.errcode == 40029
    assert "invalid code" in str(exc_info.value)
    assert "test-secret" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_jscode2session_missing_openid_raises_response_error(
    settings: Settings,
) -> None:
    async def request(**kwargs) -> httpx.Response:
        return httpx.Response(200, json={"session_key": "session-key-1"})

    client = WechatAuthClient(settings, request=request)

    with pytest.raises(WechatAuthResponseError) as exc_info:
        await client.jscode2session("login-code")

    assert "openid" in str(exc_info.value)


@pytest.mark.asyncio
async def test_jscode2session_missing_session_key_raises_response_error(
    settings: Settings,
) -> None:
    async def request(**kwargs) -> httpx.Response:
        return httpx.Response(200, json={"openid": "openid-1"})

    client = WechatAuthClient(settings, request=request)

    with pytest.raises(WechatAuthResponseError) as exc_info:
        await client.jscode2session("login-code")

    assert "session_key" in str(exc_info.value)


@pytest.mark.asyncio
async def test_get_phone_number_success(settings: Settings) -> None:
    async def request(**kwargs) -> httpx.Response:
        assert kwargs["method"] == "POST"
        assert kwargs["path"] == "/wxa/business/getuserphonenumber"
        assert kwargs["params"] == {"access_token": "access-token-1"}
        assert kwargs["json"] == {"code": "phone-code"}
        return httpx.Response(
            200,
            json={
                "errcode": 0,
                "phone_info": {
                    "phoneNumber": "13800138000",
                    "purePhoneNumber": "13800138000",
                    "countryCode": "86",
                },
            },
        )

    client = WechatAuthClient(settings, request=request)

    result = await client.get_phone_number("phone-code", "access-token-1")

    assert result.phone_number == "13800138000"
    assert result.pure_phone_number == "13800138000"
    assert result.country_code == "86"


@pytest.mark.asyncio
async def test_get_phone_number_missing_phone_raises_response_error(
    settings: Settings,
) -> None:
    async def request(**kwargs) -> httpx.Response:
        return httpx.Response(200, json={"errcode": 0, "phone_info": {}})

    client = WechatAuthClient(settings, request=request)

    with pytest.raises(WechatAuthResponseError) as exc_info:
        await client.get_phone_number("phone-code", "access-token-1")

    assert "phoneNumber" in str(exc_info.value)


@pytest.mark.asyncio
async def test_missing_config_raises_config_error() -> None:
    settings = Settings(WECHAT_MINI_LOGIN_ENABLED=True, WECHAT_MINI_APPID="")
    client = WechatAuthClient(settings)

    with pytest.raises(WechatAuthConfigError) as exc_info:
        await client.jscode2session("login-code")

    assert "WECHAT_MINI_APPID" in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_failure_raises_http_error(settings: Settings) -> None:
    async def request(**kwargs) -> httpx.Response:
        raise httpx.ConnectError("network unavailable")

    client = WechatAuthClient(settings, request=request)

    with pytest.raises(WechatAuthHTTPError) as exc_info:
        await client.jscode2session("login-code")

    assert "network unavailable" in str(exc_info.value)
    assert "test-secret" not in str(exc_info.value)


@pytest.mark.asyncio
async def test_http_error_status_raises_http_error(settings: Settings) -> None:
    async def request(**kwargs) -> httpx.Response:
        return httpx.Response(502, text="<html>bad gateway</html>")

    client = WechatAuthClient(settings, request=request)

    with pytest.raises(WechatAuthHTTPError) as exc_info:
        await client.jscode2session("login-code")

    assert "502" in str(exc_info.value)
