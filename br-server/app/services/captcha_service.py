import logging

import httpx
import redis.asyncio as aioredis

from app.core.config import Settings

logger = logging.getLogger(__name__)

# Aliyun Captcha 2.0 verification endpoint
ALIYUN_CAPTCHA_VERIFY_URL = (
    "https://captcha.cn-shanghai.aliyuncs.com/action/VerifyIntelligentCaptcha"
)


class CaptchaService:
    """Aliyun Captcha 2.0 verification service."""

    def __init__(self, config: Settings, redis: aioredis.Redis) -> None:
        self._config = config
        self._redis = redis

    async def verify(self, captcha_token: str) -> bool:
        """Verify a captcha token.

        - If no ``ALIYUN_CAPTCHA_SCENE_ID`` is configured the check is
          bypassed (dev mode).
        - Otherwise the token is sent to Aliyun Captcha 2.0 for validation.
        - Previously used tokens are rejected to prevent replay attacks.
        """
        if not captcha_token or not captcha_token.strip():
            return False

        # Dev-mode bypass
        if not self._config.ALIYUN_CAPTCHA_SCENE_ID:
            logger.info("Captcha verification bypassed (no scene_id configured)")
            return True

        # Reject reused tokens
        if await self.is_used(captcha_token):
            logger.warning("Captcha token reuse detected: %s...", captcha_token[:8])
            return False

        # Call Aliyun verification API
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.post(
                    ALIYUN_CAPTCHA_VERIFY_URL,
                    json={
                        "SceneId": self._config.ALIYUN_CAPTCHA_SCENE_ID,
                        "CaptchaVerifyParam": captcha_token,
                    },
                )
                data = resp.json()

            if data.get("Result") is True:
                await self._redis.set(
                    f"captcha:used:{captcha_token}", "1", ex=300
                )
                return True

            logger.warning(
                "Captcha verification failed: %s", data.get("Msg", "unknown")
            )
            return False

        except httpx.HTTPError as exc:
            logger.error("Captcha API request error: %s", exc)
            return False

    async def is_used(self, captcha_token: str) -> bool:
        """Check whether a captcha token has already been consumed."""
        val = await self._redis.get(f"captcha:used:{captcha_token}")
        return val is not None
