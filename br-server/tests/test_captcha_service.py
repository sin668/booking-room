from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.config import Settings
from app.services.captcha_service import CaptchaService


@pytest.fixture
def mock_redis() -> AsyncMock:
    redis = AsyncMock()
    redis.get = AsyncMock(return_value=None)
    redis.set = AsyncMock(return_value=True)
    return redis


@pytest.fixture
def dev_settings() -> Settings:
    """Settings with no captcha scene_id (dev mode bypass)."""
    return Settings(ALIYUN_CAPTCHA_SCENE_ID="")


@pytest.fixture
def prod_settings() -> Settings:
    """Settings with a captcha scene_id configured."""
    return Settings(ALIYUN_CAPTCHA_SCENE_ID="test_scene_123")


@pytest.fixture
def captcha_service_dev(
    mock_redis: AsyncMock, dev_settings: Settings
) -> CaptchaService:
    return CaptchaService(config=dev_settings, redis=mock_redis)


@pytest.fixture
def captcha_service_prod(
    mock_redis: AsyncMock, prod_settings: Settings
) -> CaptchaService:
    return CaptchaService(config=prod_settings, redis=mock_redis)


# ---------------------------------------------------------------------------
# Tests
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_verify_captcha_pass_dev_mode(
    captcha_service_dev: CaptchaService,
) -> None:
    """When no scene_id is configured, any non-empty token passes."""
    result = await captcha_service_dev.verify("any-token")
    assert result is True


@pytest.mark.asyncio
async def test_verify_captcha_aliyun(
    captcha_service_prod: CaptchaService, mock_redis: AsyncMock
) -> None:
    """Aliyun API returns success; token is marked as used."""
    mock_response = MagicMock()
    mock_response.json.return_value = {"Result": True, "Msg": "success"}

    with patch("app.services.captcha_service.httpx.AsyncClient") as MockClient:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=mock_response)
        MockClient.return_value = mock_client

        result = await captcha_service_prod.verify("valid-token")

    assert result is True
    mock_redis.set.assert_called_once_with(
        "captcha:used:valid-token", "1", ex=300
    )


@pytest.mark.asyncio
async def test_captcha_token_reused(
    captcha_service_prod: CaptchaService, mock_redis: AsyncMock
) -> None:
    """A previously used token is rejected."""
    mock_redis.get = AsyncMock(return_value="1")

    result = await captcha_service_prod.verify("used-token")
    assert result is False


@pytest.mark.asyncio
async def test_missing_captcha_token(
    captcha_service_dev: CaptchaService,
) -> None:
    """Empty or missing token returns False."""
    assert await captcha_service_dev.verify("") is False
    assert await captcha_service_dev.verify("  ") is False


@pytest.mark.asyncio
async def test_is_used_true(mock_redis: AsyncMock, dev_settings: Settings) -> None:
    """is_used returns True when the key exists in Redis."""
    mock_redis.get = AsyncMock(return_value="1")
    svc = CaptchaService(config=dev_settings, redis=mock_redis)
    assert await svc.is_used("some-token") is True


@pytest.mark.asyncio
async def test_is_used_false(mock_redis: AsyncMock, dev_settings: Settings) -> None:
    """is_used returns False when the key does not exist in Redis."""
    mock_redis.get = AsyncMock(return_value=None)
    svc = CaptchaService(config=dev_settings, redis=mock_redis)
    assert await svc.is_used("new-token") is False
