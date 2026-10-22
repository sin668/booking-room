"""Tencent Cloud IM UserSig generation utility.

Algorithm aligned with official TLSSigAPIv2.py reference implementation.
"""

import base64
import hashlib
import hmac
import json
import time
import uuid
import zlib

from app.core.config import settings


def to_im_user_id(user_id: uuid.UUID) -> str:
    """腾讯云 IM UserID 最长 32 字节，UUID 带连字符是 36 位，所以取其 hex 形式。"""
    return user_id.hex


def from_im_user_id(im_user_id: str | None) -> uuid.UUID | None:
    """to_im_user_id 的逆运算；账号不是本系统派生的 IM UserID 时返回 None。"""
    if not im_user_id:
        return None
    try:
        return uuid.UUID(hex=im_user_id)
    except (ValueError, AttributeError):
        return None


def verify_callback_sign(sdk_appid: str | None, request_time: str | None, sign: str | None) -> bool:
    """校验腾讯云第三方回调的 SdkAppid 与 Sign。

    官方公式 Sign = sha256(Token + RequestTime)，两者都在 URL 参数上。
    SdkAppid 是通过 /api/v1/chat/user-sig 下发给客户端的公开值，单独校验它等于没有鉴权，
    因此未配置 IM_CALLBACK_TOKEN 时一律拒绝，回调接口不落任何数据。
    """
    if str(settings.IM_SDK_APP_ID) != str(sdk_appid or ""):
        return False

    token = settings.IM_CALLBACK_TOKEN
    if not token:
        return False

    try:
        ts_ms = int(request_time or "")
    except ValueError:
        return False
    if ts_ms < 10**12:
        ts_ms *= 1000  # 兼容秒级时间戳
    # 官方建议时间戳误差超过 1 分钟直接丢弃，防重放
    if abs(int(time.time() * 1000) - ts_ms) > 60_000:
        return False

    expected = hashlib.sha256(f"{token}{request_time}".encode("utf-8")).hexdigest()
    return hmac.compare_digest(expected, sign or "")


def _base64_encode_url(data: bytes) -> str:
    """URL-safe base64 with Tencent's custom character mapping."""
    s = base64.b64encode(data).decode("utf-8")
    s = s.replace("+", "*")
    s = s.replace("/", "-")
    s = s.replace("=", "_")
    return s


def gen_user_sig(user_id: str, expire: int = 180 * 24 * 60 * 60) -> str:
    """Generate a UserSig for the given user ID.

    Args:
        user_id: The IM user ID (see to_im_user_id).
        expire: Validity period in seconds (default 180 days).
    """
    sdk_app_id = settings.IM_SDK_APP_ID
    secret_key = settings.IM_SERVER_KEY
    now = int(time.time())

    raw_content = (
        f"TLS.identifier:{user_id}\n"
        f"TLS.sdkappid:{sdk_app_id}\n"
        f"TLS.time:{now}\n"
        f"TLS.expire:{expire}\n"
    )

    sig = base64.b64encode(
        hmac.new(
            secret_key.encode("utf-8"),
            raw_content.encode("utf-8"),
            hashlib.sha256,
        ).digest()
    ).decode("utf-8")

    payload = {
        "TLS.ver": "2.0",
        "TLS.identifier": str(user_id),
        "TLS.sdkappid": int(sdk_app_id),
        "TLS.expire": int(expire),
        "TLS.time": int(now),
        "TLS.sig": sig,
    }

    compressed = zlib.compress(json.dumps(payload).encode("utf-8"))
    return _base64_encode_url(compressed)
