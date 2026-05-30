from datetime import UTC, datetime, timedelta

import pytest

from app.domain.verification_rules import (
    TOKEN_TTL_SECONDS,
    CompactVerificationPayload,
    ExpiredVerificationToken,
    InvalidVerificationToken,
    create_compact_verification_token,
    decode_compact_verification_token,
)


def test_create_and_decode_compact_verification_token_round_trips_booking_id():
    now = datetime(2026, 5, 30, 10, 0, tzinfo=UTC)
    token, expires_at = create_compact_verification_token(
        booking_id=123,
        secret="secret",
        now=now,
        nonce="abc",
    )

    payload = decode_compact_verification_token(
        token=token,
        secret="secret",
        now=now,
    )

    assert expires_at == now + timedelta(seconds=TOKEN_TTL_SECONDS)
    assert payload == CompactVerificationPayload(
        booking_id=123,
        issued_at=now,
        nonce="abc",
    )


def test_decode_compact_verification_token_rejects_bad_signature():
    now = datetime(2026, 5, 30, 10, 0, tzinfo=UTC)
    token, _ = create_compact_verification_token(
        booking_id=123,
        secret="secret",
        now=now,
        nonce="abc",
    )

    with pytest.raises(InvalidVerificationToken):
        decode_compact_verification_token(token=token, secret="other", now=now)


def test_decode_compact_verification_token_rejects_expired_token():
    now = datetime(2026, 5, 30, 10, 0, tzinfo=UTC)
    token, _ = create_compact_verification_token(
        booking_id=123,
        secret="secret",
        now=now,
        nonce="abc",
    )

    with pytest.raises(ExpiredVerificationToken):
        decode_compact_verification_token(
            token=token,
            secret="secret",
            now=now + timedelta(seconds=TOKEN_TTL_SECONDS + 1),
        )
