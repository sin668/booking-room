"""Tencent Cloud IM UserSig generation utility.

Algorithm aligned with official TLSSigAPIv2.py reference implementation.
"""

import base64
import hashlib
import hmac
import json
import time
import zlib

from app.core.config import settings


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
        user_id: The IM user ID (maps to platform username).
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
