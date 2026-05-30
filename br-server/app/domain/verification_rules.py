from __future__ import annotations

import base64
import hashlib
import hmac
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta


TOKEN_TTL_SECONDS = 5 * 60
COMPACT_TOKEN_VERSION = "v1"


class InvalidVerificationToken(ValueError):
    pass


class ExpiredVerificationToken(ValueError):
    pass


@dataclass(frozen=True)
class CompactVerificationPayload:
    booking_id: int
    issued_at: datetime
    nonce: str


def create_compact_verification_token(
    *,
    booking_id: int,
    secret: str,
    now: datetime,
    nonce: str,
) -> tuple[str, datetime]:
    issued_at = ensure_utc(now)
    expires_at = issued_at + timedelta(seconds=TOKEN_TTL_SECONDS)
    signing_input = (
        f"{COMPACT_TOKEN_VERSION}.{booking_id}.{int(expires_at.timestamp())}.{nonce}"
    )
    signature = sign_compact_token(signing_input=signing_input, secret=secret)
    return f"{signing_input}.{signature}", expires_at


def decode_compact_verification_token(
    *,
    token: str,
    secret: str,
    now: datetime,
) -> CompactVerificationPayload:
    parts = token.split(".")
    if len(parts) != 5 or parts[0] != COMPACT_TOKEN_VERSION:
        raise InvalidVerificationToken("无效的核销码")

    signing_input = ".".join(parts[:4])
    expected_signature = sign_compact_token(signing_input=signing_input, secret=secret)
    if not hmac.compare_digest(parts[4], expected_signature):
        raise InvalidVerificationToken("无效的核销码")

    try:
        booking_id = int(parts[1])
        expires_at = datetime.fromtimestamp(int(parts[2]), tz=UTC)
        nonce = parts[3]
    except (TypeError, ValueError, OSError) as exc:
        raise InvalidVerificationToken("无效的核销码") from exc

    if not nonce:
        raise InvalidVerificationToken("无效的核销码")

    current_time = ensure_utc(now)
    if expires_at <= current_time:
        raise ExpiredVerificationToken("核销码已过期")

    return CompactVerificationPayload(
        booking_id=booking_id,
        issued_at=expires_at - timedelta(seconds=TOKEN_TTL_SECONDS),
        nonce=nonce,
    )


def sign_compact_token(*, signing_input: str, secret: str) -> str:
    digest = hmac.new(
        secret.encode("utf-8"),
        signing_input.encode("utf-8"),
        hashlib.sha256,
    ).digest()
    return base64url_encode(digest[:16])


def base64url_encode(value: bytes) -> str:
    return base64.urlsafe_b64encode(value).decode("ascii").rstrip("=")


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=UTC)
    return value.astimezone(UTC)
