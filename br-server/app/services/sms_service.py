import base64
import hashlib
import hmac
import logging
import random
import string
import urllib.parse
from datetime import date, datetime, timezone
from uuid import uuid4

import httpx
import redis.asyncio as aioredis
from fastapi import HTTPException

from app.core.config import Settings
from app.services.captcha_service import CaptchaService

logger = logging.getLogger(__name__)

ALIYUN_SMS_API_URL = "https://dysmsapi.aliyuncs.com/"


def _percent_encode(s: str) -> str:
    """URL-encode per Aliyun signature spec (uppercase hex, encode / += etc)."""
    return urllib.parse.quote(str(s), safe="~").replace("+", "%20").replace("*", "%2A").replace("%7E", "~")


def _sign_request(params: dict, access_key_secret: str) -> dict:
    """Sign Aliyun API request parameters with HMAC-SHA1."""
    # 1. Sort by key
    sorted_params = sorted(params.items())

    # 2. Build canonical query string
    canonical_qs = "&".join(f"{_percent_encode(k)}={_percent_encode(v)}" for k, v in sorted_params)

    # 3. String to sign
    string_to_sign = f"GET&{_percent_encode('/')}&{_percent_encode(canonical_qs)}"

    # 4. HMAC-SHA1 with key = AccessKeySecret + "&"
    key = (access_key_secret + "&").encode("utf-8")
    signature = hmac.new(key, string_to_sign.encode("utf-8"), hashlib.sha1).digest()

    # 5. Base64 encode
    params["Signature"] = base64.b64encode(signature).decode("utf-8")
    return params


class AliyunSMSProvider:
    """Aliyun Dysms API client for sending SMS verification codes."""

    def __init__(self, config: Settings) -> None:
        self._config = config

    async def send(self, phone: str, code: str) -> dict:
        """Send a verification code via Aliyun Dysms API.

        Returns the API response dict on success.
        Raises HTTPException on failure.
        """
        access_key_id = self._config.ALIYUN_SMS_ACCESS_KEY_ID
        access_key_secret = self._config.ALIYUN_SMS_ACCESS_KEY_SECRET

        if not access_key_id or not access_key_secret:
            raise HTTPException(
                status_code=500,
                detail="短信服务未配置：缺少 ALIYUN_SMS_ACCESS_KEY_ID 或 ALIYUN_SMS_ACCESS_KEY_SECRET",
            )

        params = {
            "Action": "SendSms",
            "Version": "2017-05-25",
            "Format": "JSON",
            "RegionId": "cn-hangzhou",
            "AccessKeyId": access_key_id,
            "SignatureMethod": "HMAC-SHA1",
            "SignatureVersion": "1.0",
            "SignatureNonce": uuid4().hex,
            "Timestamp": datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
            "PhoneNumbers": phone,
            "SignName": self._config.ALIYUN_SMS_SIGN_NAME,
            "TemplateCode": self._config.ALIYUN_SMS_TEMPLATE_CODE,
            "TemplateParam": f'{{"code":"{code}"}}',
        }

        signed_params = _sign_request(params, access_key_secret)

        try:
            async with httpx.AsyncClient(timeout=10) as client:
                resp = await client.get(ALIYUN_SMS_API_URL, params=signed_params)
                data = resp.json()
        except httpx.HTTPError as exc:
            logger.error("SMS API request error: %s", exc)
            raise HTTPException(status_code=500, detail=f"短信服务请求失败: {exc}")
        except Exception as exc:
            logger.error("SMS API unexpected error: %s", exc)
            raise HTTPException(status_code=500, detail=f"短信服务异常: {exc}")

        if data.get("Code") == "OK":
            logger.info("SMS sent successfully to %s, RequestId: %s", phone, data.get("RequestId"))
            return data

        error_code = data.get("Code", "UNKNOWN")
        error_msg = data.get("Message", "未知错误")
        logger.error("Aliyun SMS error for %s: %s – %s", phone, error_code, error_msg)
        raise HTTPException(
            status_code=500,
            detail=f"短信发送失败: [{error_code}] {error_msg}",
        )


class SMSService:
    """SMS verification code service with rate-limiting."""

    def __init__(self, redis: aioredis.Redis, config: Settings) -> None:
        self._redis = redis
        self._config = config
        self._sms_provider = AliyunSMSProvider(config)
        self._captcha_service = CaptchaService(config, redis)

    async def generate_code(self) -> str:
        """Return a 6-digit random numeric string."""
        return "".join(random.choices(string.digits, k=6))

    async def send_code(self, phone: str, captcha_token: str | None = None) -> None:
        """Send a verification code to *phone*.

        Workflow:
        1. Validate captcha token (skip if not provided).
        2. Enforce per-minute rate limit (1 request / 60 s).
        3. Enforce daily limit (max 10 requests / day).
        4. Generate code, store in Redis with 300 s TTL.
        5. Dispatch via ``AliyunSMSProvider``.
        """
        # 1. Validate captcha (skip if disabled)
        if captcha_token:
            captcha_ok = await self._captcha_service.verify(captcha_token)
            if not captcha_ok:
                raise HTTPException(status_code=400, detail="人机验证失败，请重试")

        # 2. Per-minute rate limit
        rate_key = f"sms:rate:{phone}"
        if await self._redis.get(rate_key):
            raise HTTPException(
                status_code=429, detail="发送过于频繁，请60秒后重试"
            )
        await self._redis.set(rate_key, "1", ex=60)

        # 3. Daily limit
        today = date.today().isoformat()
        daily_key = f"sms:daily:{phone}:{today}"
        daily_count = await self._redis.incr(daily_key)
        if daily_count == 1:
            await self._redis.expire(daily_key, 86400)
        if daily_count > 10:
            raise HTTPException(
                status_code=429, detail="今日发送次数已达上限"
            )

        # 4. Generate & store code
        code = await self.generate_code()
        await self._redis.set(f"sms:verify:{phone}", code, ex=300)

        # 5. Send SMS
        await self._sms_provider.send(phone, code)

    async def verify_code(self, phone: str, code: str) -> bool:
        """Verify an SMS code.

        - If the code matches, the key is deleted (one-time use).
        - If the code does not match, the key is kept so the user may retry.
        - Returns ``False`` when the code is missing / expired.
        """
        key = f"sms:verify:{phone}"
        stored = await self._redis.get(key)

        if stored is None:
            return False

        if stored == code:
            await self._redis.delete(key)
            return True

        return False
