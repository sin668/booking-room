"""Unit tests for SMS service (extended coverage)."""

from datetime import date
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from app.core.config import Settings
from app.services.sms_service import AliyunSMSProvider, SMSService


@pytest.fixture
def mock_redis() -> AsyncMock:
    """Return a mock async Redis client."""
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    redis.delete = AsyncMock(return_value=True)
    redis.incr = AsyncMock(return_value=1)
    redis.expire = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def settings() -> Settings:
    """Return settings with no credentials (dev mode)."""
    return Settings(
        ALIYUN_SMS_ACCESS_KEY_ID="",
        ALIYUN_SMS_ACCESS_KEY_SECRET="",
        ALIYUN_SMS_SIGN_NAME="测试",
        ALIYUN_SMS_TEMPLATE_CODE="SMS_000000",
        ALIYUN_CAPTCHA_SCENE_ID="",
    )


@pytest.fixture
def settings_with_creds() -> Settings:
    """Return settings with Aliyun SMS credentials."""
    return Settings(
        ALIYUN_SMS_ACCESS_KEY_ID="test_key_id",
        ALIYUN_SMS_ACCESS_KEY_SECRET="test_key_secret",
        ALIYUN_SMS_SIGN_NAME="测试签名",
        ALIYUN_SMS_TEMPLATE_CODE="SMS_123456",
        ALIYUN_CAPTCHA_SCENE_ID="",
    )


@pytest.fixture
def sms_service(mock_redis: AsyncMock, settings: Settings) -> SMSService:
    """Return an SMSService with mocked Redis and dev-mode settings."""
    return SMSService(redis=mock_redis, config=settings)


@pytest.fixture
def sms_service_prod(mock_redis: AsyncMock, settings_with_creds: Settings) -> SMSService:
    """Return an SMSService with real credentials (for provider tests)."""
    return SMSService(redis=mock_redis, config=settings_with_creds)


@pytest.fixture
def captcha_token() -> str:
    return "fake-captcha-token"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


async def _send_and_expect_code(
    sms: SMSService, phone: str = "13800138000", token: str = "token"
) -> str:
    """Call send_code and extract the code from Redis.set call args."""
    await sms.send_code(phone, token)
    set_calls = sms._redis.set.call_args_list
    verify_call = [c for c in set_calls if "sms:verify:" in str(c)]
    return verify_call[0][0][1]


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
@patch.object(AliyunSMSProvider, "send", new_callable=AsyncMock, return_value={"Code": "OK"})
async def test_send_code_success(
    mock_send: AsyncMock,
    sms_service: SMSService,
    mock_redis: AsyncMock,
    captcha_token: str,
) -> None:
    """Happy path: code is generated, stored, and sent."""
    await sms_service.send_code("13800138000", captcha_token)

    mock_redis.set.assert_any_call("sms:rate:13800138000", "1", ex=60)
    today = date.today().isoformat()
    mock_redis.incr.assert_called_once_with(f"sms:daily:13800138000:{today}")
    verify_calls = [
        c for c in mock_redis.set.call_args_list if "sms:verify:" in str(c)
    ]
    assert len(verify_calls) == 1
    args, kwargs = verify_calls[0]
    assert args[0] == "sms:verify:13800138000"
    code = args[1]
    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
@patch.object(AliyunSMSProvider, "send", new_callable=AsyncMock, return_value={"Code": "OK"})
async def test_rate_limit_per_minute(
    mock_send: AsyncMock,
    sms_service: SMSService,
    mock_redis: AsyncMock,
    captcha_token: str,
) -> None:
    """Second send within 60 s is rejected with 429."""
    await sms_service.send_code("13800138000", captcha_token)
    mock_redis.get = AsyncMock(return_value="1")

    with pytest.raises(HTTPException) as exc_info:
        await sms_service.send_code("13800138000", captcha_token)
    assert exc_info.value.status_code == 429
    assert "发送过于频繁" in exc_info.value.detail


@pytest.mark.asyncio
async def test_daily_limit_exceeded(
    sms_service: SMSService, mock_redis: AsyncMock, captcha_token: str
) -> None:
    """The 11th send in one day is rejected with 429."""
    today = date.today().isoformat()
    mock_redis.incr = AsyncMock(return_value=11)

    with pytest.raises(HTTPException) as exc_info:
        await sms_service.send_code("13800138000", captcha_token)
    assert exc_info.value.status_code == 429
    assert "今日发送次数已达上限" in exc_info.value.detail


@pytest.mark.asyncio
@patch.object(AliyunSMSProvider, "send", new_callable=AsyncMock, return_value={"Code": "OK"})
async def test_captcha_validation_failure(
    mock_send: AsyncMock,
    sms_service: SMSService,
    mock_redis: AsyncMock,
) -> None:
    """Invalid captcha token returns 400."""
    with patch.object(sms_service._captcha_service, "verify", new_callable=AsyncMock, return_value=False):
        with pytest.raises(HTTPException) as exc_info:
            await sms_service.send_code("13800138000", "bad-captcha-token")
        assert exc_info.value.status_code == 400
        assert "人机验证失败" in exc_info.value.detail


@pytest.mark.asyncio
@patch.object(AliyunSMSProvider, "send", new_callable=AsyncMock, return_value={"Code": "OK"})
async def test_no_captcha_token_skips_validation(
    mock_send: AsyncMock,
    sms_service: SMSService,
    mock_redis: AsyncMock,
) -> None:
    """No captcha_token skips captcha validation entirely."""
    await sms_service.send_code("13800138000", None)
    # If we reach here, no captcha exception was raised
    mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_verify_code_correct(
    sms_service: SMSService, mock_redis: AsyncMock
) -> None:
    """Correct code returns True and deletes the key."""
    mock_redis.get = AsyncMock(return_value="123456")
    result = await sms_service.verify_code("13800138000", "123456")
    assert result is True
    mock_redis.delete.assert_called_once_with("sms:verify:13800138000")


@pytest.mark.asyncio
async def test_verify_code_incorrect(
    sms_service: SMSService, mock_redis: AsyncMock
) -> None:
    """Incorrect code returns False and keeps the key."""
    mock_redis.get = AsyncMock(return_value="123456")
    result = await sms_service.verify_code("13800138000", "654321")
    assert result is False
    mock_redis.delete.assert_not_called()


@pytest.mark.asyncio
async def test_verify_code_expired(
    sms_service: SMSService, mock_redis: AsyncMock
) -> None:
    """Expired / missing code returns False."""
    mock_redis.get = AsyncMock(return_value=None)
    result = await sms_service.verify_code("13800138000", "123456")
    assert result is False


@pytest.mark.asyncio
async def test_generate_code_format(sms_service: SMSService) -> None:
    """Generated code is a 6-digit numeric string."""
    for _ in range(20):
        code = await sms_service.generate_code()
        assert len(code) == 6
        assert code.isdigit()


@pytest.mark.asyncio
async def test_aliyun_sms_provider_missing_credentials(settings: Settings) -> None:
    """Provider raises HTTPException when credentials are not configured."""
    provider = AliyunSMSProvider(settings)
    with pytest.raises(HTTPException) as exc_info:
        await provider.send("13800138000", "123456")
    assert exc_info.value.status_code == 500
    assert "未配置" in exc_info.value.detail


# ---------------------------------------------------------------------------
# AliyunSMSProvider.send with real credentials (mocked HTTP)
# ---------------------------------------------------------------------------


class TestAliyunSMSProviderSend:
    @pytest.mark.asyncio
    async def test_send_success(self, settings_with_creds: Settings) -> None:
        """Provider successfully sends SMS and returns response data."""
        provider = AliyunSMSProvider(settings_with_creds)

        mock_response = MagicMock()
        mock_response.json.return_value = {"Code": "OK", "RequestId": "req-123"}

        with patch("app.services.sms_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            result = await provider.send("13800138000", "123456")
            assert result["Code"] == "OK"

    @pytest.mark.asyncio
    async def test_send_api_error(self, settings_with_creds: Settings) -> None:
        """Provider raises HTTPException when API returns error code."""
        provider = AliyunSMSProvider(settings_with_creds)

        mock_response = MagicMock()
        mock_response.json.return_value = {"Code": "isv.BUSINESS_LIMIT_CONTROL", "Message": "触发业务流控"}

        with patch("app.services.sms_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(return_value=mock_response)
            MockClient.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await provider.send("13800138000", "123456")
            assert exc_info.value.status_code == 500
            assert "isv.BUSINESS_LIMIT_CONTROL" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_send_http_error(self, settings_with_creds: Settings) -> None:
        """Provider raises HTTPException when HTTP request fails."""
        import httpx

        provider = AliyunSMSProvider(settings_with_creds)

        with patch("app.services.sms_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=httpx.HTTPError("connection failed"))
            MockClient.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await provider.send("13800138000", "123456")
            assert exc_info.value.status_code == 500
            assert "请求失败" in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_send_unexpected_error(self, settings_with_creds: Settings) -> None:
        """Provider raises HTTPException on unexpected errors."""
        provider = AliyunSMSProvider(settings_with_creds)

        with patch("app.services.sms_service.httpx.AsyncClient") as MockClient:
            mock_client = AsyncMock()
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=False)
            mock_client.get = AsyncMock(side_effect=RuntimeError("unexpected"))
            MockClient.return_value = mock_client

            with pytest.raises(HTTPException) as exc_info:
                await provider.send("13800138000", "123456")
            assert exc_info.value.status_code == 500
            assert "异常" in exc_info.value.detail


# ---------------------------------------------------------------------------
# _percent_encode / _sign_request tests
# ---------------------------------------------------------------------------


class TestSignRequest:
    def test_percent_encode(self) -> None:
        """_percent_encode encodes per Aliyun spec."""
        from app.services.sms_service import _percent_encode

        assert _percent_encode("hello world") == "hello%20world"
        assert _percent_encode("a+b") == "a%2Bb"
        assert _percent_encode("a*b") == "a%2Ab"
        assert _percent_encode("a~b") == "a~b"

    def test_sign_request(self) -> None:
        """_sign_request produces a Signature field."""
        from app.services.sms_service import _sign_request

        params = {"Action": "SendSms", "PhoneNumbers": "13800138000"}
        result = _sign_request(params, "secret&")
        assert "Signature" in result
        assert isinstance(result["Signature"], str)
        assert len(result["Signature"]) > 0
