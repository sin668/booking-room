"""Tencent Cloud IM UserSig generation utility."""

import base64
import hashlib
import hmac
import json
import time
import zlib

from app.core.config import settings


def gen_user_sig(user_id: str, expire: int = 180 * 24 * 60 * 60) -> str:
    """Generate a UserSig for the given user ID.

    Args:
        user_id: The IM user ID (maps to platform username).
        expire: Validity period in seconds (default 180 days).
    """
    sdk_app_id = settings.IM_SDK_APP_ID
    secret_key = settings.IM_SERVER_KEY
    now = int(time.time())

    base_str = (
        f"TLS.sdkappid:{sdk_app_id},"
        f"TLS.expire:{expire},"
        f"TLS.identifier:{user_id},"
        f"TLS.time:{now}"
    )

    hash_value = hmac.new(
        secret_key.encode("utf-8"),
        base_str.encode("utf-8"),
        hashlib.sha256,
    ).digest()

    sig = base64.b64encode(hash_value).decode("utf-8")

    raw = {
        "TLS.ver": "20151230",
        "TLS.sdkappid": sdk_app_id,
        "TLS.expire": expire,
        "TLS.time": now,
        "TLS.sig": sig,
        "TLS.identifier": user_id,
        "TLS.userbuf": "",
        "TLS.userbufaddr": 0,
        "TLS.accountType": 0,
    }

    json_str = json.dumps(raw, separators=(",", ":"), sort_keys=False)
    compressed = zlib.compress(json_str.encode("utf-8"))
    return base64.b64encode(compressed).decode("utf-8")
