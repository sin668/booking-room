"""WeChat mini program auth client."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Awaitable, Callable

import httpx

from app.core.config import Settings


RequestCallable = Callable[..., Awaitable[httpx.Response]]


class WechatAuthError(Exception):
    """Base exception for WeChat auth client failures."""


class WechatAuthConfigError(WechatAuthError):
    """Raised when WeChat mini program login config is disabled or incomplete."""


class WechatAuthHTTPError(WechatAuthError):
    """Raised when the HTTP request to WeChat fails."""


class WechatAuthAPIError(WechatAuthError):
    """Raised when WeChat returns a non-zero errcode."""

    def __init__(self, errcode: int, errmsg: str) -> None:
        self.errcode = errcode
        self.errmsg = errmsg
        super().__init__(f"WeChat API error [{errcode}] {errmsg}")


class WechatAuthResponseError(WechatAuthError):
    """Raised when WeChat returns an incomplete or malformed success payload."""


@dataclass(frozen=True)
class WechatSession:
    openid: str
    session_key: str
    unionid: str | None = None


@dataclass(frozen=True)
class WechatPhoneNumber:
    phone_number: str
    pure_phone_number: str | None = None
    country_code: str | None = None


class WechatAuthClient:
    """Small client that owns WeChat mini program auth protocol details."""

    def __init__(
        self,
        config: Settings,
        *,
        request: RequestCallable | None = None,
        transport: httpx.AsyncBaseTransport | None = None,
    ) -> None:
        self._config = config
        self._request = request
        self._transport = transport

    async def jscode2session(self, code: str) -> WechatSession:
        """Exchange a mini program login code for openid and session_key."""
        self._require_usable_config()
        response = await self._send(
            method="GET",
            path="/sns/jscode2session",
            params={
                "appid": self._config.WECHAT_MINI_APPID,
                "secret": self._config.WECHAT_MINI_SECRET,
                "js_code": code,
                "grant_type": "authorization_code",
            },
        )
        data = _parse_response(response)
        openid = _require_string(data, "openid")
        session_key = _require_string(data, "session_key")
        unionid = data.get("unionid")
        return WechatSession(
            openid=openid,
            session_key=session_key,
            unionid=str(unionid) if unionid else None,
        )

    async def get_phone_number(
        self,
        code: str,
        access_token: str,
    ) -> WechatPhoneNumber:
        """Exchange a mini program phone authorization code for phone info."""
        self._require_usable_config()
        response = await self._send(
            method="POST",
            path="/wxa/business/getuserphonenumber",
            params={"access_token": access_token},
            json={"code": code},
        )
        data = _parse_response(response)
        phone_info = data.get("phone_info")
        if not isinstance(phone_info, dict):
            raise WechatAuthResponseError(
                "WeChat phone number response missing phone_info"
            )
        phone_number = _require_string(phone_info, "phoneNumber")
        pure_phone_number = phone_info.get("purePhoneNumber")
        country_code = phone_info.get("countryCode")
        return WechatPhoneNumber(
            phone_number=phone_number,
            pure_phone_number=str(pure_phone_number) if pure_phone_number else None,
            country_code=str(country_code) if country_code else None,
        )

    def _require_usable_config(self) -> None:
        try:
            self._config.require_wechat_mini_login_usable()
        except ValueError as exc:
            raise WechatAuthConfigError(str(exc)) from exc

    async def _send(
        self,
        *,
        method: str,
        path: str,
        params: dict[str, Any] | None = None,
        json: dict[str, Any] | None = None,
    ) -> httpx.Response:
        try:
            if self._request is not None:
                return await self._request(
                    method=method,
                    path=path,
                    params=params,
                    json=json,
                )

            async with httpx.AsyncClient(
                base_url=self._config.WECHAT_MINI_API_BASE_URL,
                timeout=self._config.WECHAT_MINI_REQUEST_TIMEOUT_SECONDS,
                transport=self._transport,
            ) as client:
                return await client.request(
                    method,
                    path,
                    params=params,
                    json=json,
                )
        except httpx.HTTPError as exc:
            raise WechatAuthHTTPError(f"WeChat auth request failed: {exc}") from exc


def _parse_response(response: httpx.Response) -> dict[str, Any]:
    if not 200 <= response.status_code < 300:
        raise WechatAuthHTTPError(
            f"WeChat auth HTTP error [{response.status_code}]"
        )

    try:
        data = response.json()
    except Exception as exc:
        raise WechatAuthResponseError("WeChat auth returned a non-JSON response") from exc

    if not isinstance(data, dict):
        raise WechatAuthResponseError("WeChat auth returned an invalid JSON response")

    errcode = data.get("errcode")
    if errcode is not None and str(errcode) != "0":
        try:
            errcode_int = int(errcode)
        except (TypeError, ValueError):
            errcode_int = -1
        errmsg = str(data.get("errmsg", "unknown error"))
        raise WechatAuthAPIError(errcode_int, errmsg)

    return data


def _require_string(data: dict[str, Any], field: str) -> str:
    value = data.get(field)
    if not isinstance(value, str) or not value:
        raise WechatAuthResponseError(f"WeChat auth response missing {field}")
    return value
