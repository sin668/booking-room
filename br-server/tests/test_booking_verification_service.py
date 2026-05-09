"""Unit tests for booking verification service."""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from jose import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.services.booking_verification_service import (
    BookingAlreadyVerifiedError,
    BookingNotVerifiableError,
    ExpiredVerificationTokenError,
    InvalidVerificationTokenError,
    NoVerifiableBookingError,
    VERIFICATION_TOKEN_PURPOSE,
    _booking_timezone,
    _create_verification_token,
    _is_booking_in_verification_window,
    confirm_verification,
    inspect_verification_token,
    issue_verification_token,
)

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture(autouse=True)
def verification_secret(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-verification-secret")
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "https://booking.example.com")
    monkeypatch.setattr(settings, "BOOKING_TIMEZONE", "Asia/Shanghai")


@pytest.fixture
async def verification_data(db_session: AsyncSession):
    user = User(
        id=USER_ID,
        phone="13800138000",
        nickname="Study User",
        password_hash="hash",
        status="active",
    )
    room = StudyRoom(name="Test Room", address="123 Test St", status="open", min_price=10.00)
    db_session.add_all([user, room])
    await db_session.flush()

    seat = Seat(
        room_id=room.id,
        seat_number="A-01",
        zone="quiet",
        position="window",
        floor=3,
        price_per_hour=15.00,
        status="available",
        row=1,
        col=1,
    )
    db_session.add(seat)
    await db_session.flush()

    today = datetime.now(UTC).date()
    confirmed = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=today,
        start_time=time(0, 0),
        end_time=time(23, 59),
        status="confirmed",
        total_price=45.00,
    )
    cancelled = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=date(2026, 5, 11),
        start_time=time(9, 0),
        end_time=time(12, 0),
        status="cancelled",
        total_price=45.00,
    )
    completed = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=date(2026, 5, 12),
        start_time=time(9, 0),
        end_time=time(12, 0),
        status="completed",
        total_price=45.00,
    )
    db_session.add_all([confirmed, cancelled, completed])
    await db_session.flush()

    return {
        "user": user,
        "room": room,
        "seat": seat,
        "confirmed": confirmed,
        "cancelled": cancelled,
        "completed": completed,
    }


async def test_issue_verification_token_returns_short_lived_token_and_summary(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "https://example.com/app/")

    response = await issue_verification_token(
        db_session,
        USER_ID,
    )

    assert response.token
    assert response.verify_url.startswith("https://example.com/app/#/pages/verify-booking/index?token=")
    assert "/pages/verify-booking/index?token=" in response.verify_url
    assert 295 <= (response.expires_at - datetime.now(UTC)).total_seconds() <= 300
    assert response.booking.id == verification_data["confirmed"].id
    assert response.booking.user_id == str(USER_ID)
    assert response.booking.user_nickname == "Study User"
    assert response.booking.user_phone == "13800138000"
    assert response.booking.room_name == "Test Room"
    assert response.booking.seat_number == "A-01"
    assert response.booking.status == "confirmed"
    assert response.booking.can_verify is True


def test_verification_window_uses_configured_business_timezone(verification_data):
    booking = verification_data["confirmed"]
    booking.date = date(2026, 5, 10)
    booking.start_time = time(9, 0)
    booking.end_time = time(12, 0)

    shanghai = _booking_timezone()
    allowed = datetime(2026, 5, 10, 8, 45, tzinfo=shanghai)
    too_early = datetime(2026, 5, 10, 8, 29, tzinfo=shanghai)
    after_end = datetime(2026, 5, 10, 12, 1, tzinfo=shanghai)

    assert _is_booking_in_verification_window(booking, allowed) is True
    assert _is_booking_in_verification_window(booking, too_early) is False
    assert _is_booking_in_verification_window(booking, after_end) is False


async def test_issue_verification_token_without_confirmed_booking_raises(
    db_session: AsyncSession,
    verification_data,
):
    verification_data["confirmed"].status = "cancelled"
    await db_session.flush()

    with pytest.raises(NoVerifiableBookingError):
        await issue_verification_token(db_session, USER_ID)


async def test_issue_verification_token_for_future_booking_raises(
    db_session: AsyncSession,
    verification_data,
):
    verification_data["confirmed"].date = datetime.now(UTC).date() + timedelta(days=1)
    await db_session.flush()

    with pytest.raises(NoVerifiableBookingError):
        await issue_verification_token(db_session, USER_ID)


async def test_issue_verification_token_skips_expired_booking_window(
    db_session: AsyncSession,
    verification_data,
):
    expired = verification_data["confirmed"]
    room = verification_data["room"]
    seat = verification_data["seat"]
    today = datetime.now(UTC).date()
    expired.start_time = time(0, 0)
    expired.end_time = time(0, 1)
    eligible = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=today,
        start_time=time(0, 0),
        end_time=time(23, 59),
        status="confirmed",
        total_price=45.00,
    )
    db_session.add(eligible)
    await db_session.flush()

    response = await issue_verification_token(db_session, USER_ID)

    assert response.booking.id == eligible.id


async def test_inspect_tampered_token_raises_invalid(
    db_session: AsyncSession,
    verification_data,
):
    response = await issue_verification_token(db_session, USER_ID)

    with pytest.raises(InvalidVerificationTokenError):
        await inspect_verification_token(db_session, response.token + "tampered")


async def test_wrong_purpose_token_raises_invalid(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["confirmed"]
    payload = {
        "booking_id": booking.id,
        "user_id": str(USER_ID),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        "nonce": "not-for-booking-verification",
        "purpose": "access",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(InvalidVerificationTokenError):
        await inspect_verification_token(db_session, token)


async def test_missing_audience_token_raises_invalid(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["confirmed"]
    payload = {
        "booking_id": booking.id,
        "user_id": str(USER_ID),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        "nonce": "missing-audience",
        "purpose": VERIFICATION_TOKEN_PURPOSE,
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(InvalidVerificationTokenError):
        await inspect_verification_token(db_session, token)


async def test_wrong_audience_token_raises_invalid(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["confirmed"]
    payload = {
        "booking_id": booking.id,
        "user_id": str(USER_ID),
        "iat": int(datetime.now(UTC).timestamp()),
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        "nonce": "wrong-audience",
        "purpose": VERIFICATION_TOKEN_PURPOSE,
        "aud": "ordinary-auth",
    }
    token = jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=settings.JWT_ALGORITHM)

    with pytest.raises(InvalidVerificationTokenError):
        await inspect_verification_token(db_session, token)


async def test_expired_token_raises_for_inspect_and_confirm(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["confirmed"]
    token, _ = _create_verification_token(
        booking.id,
        str(USER_ID),
        datetime.now(UTC) - timedelta(minutes=6),
    )

    with pytest.raises(ExpiredVerificationTokenError):
        await inspect_verification_token(db_session, token)

    with pytest.raises(ExpiredVerificationTokenError):
        await confirm_verification(db_session, token)


async def test_confirm_verification_for_future_booking_raises(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["confirmed"]
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))
    booking.date = datetime.now(UTC).date() + timedelta(days=1)
    await db_session.flush()

    with pytest.raises(BookingNotVerifiableError):
        await confirm_verification(db_session, token)


async def test_confirm_verification_after_end_time_raises(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["confirmed"]
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))
    booking.start_time = time(0, 0)
    booking.end_time = time(0, 1)
    await db_session.flush()

    with pytest.raises(BookingNotVerifiableError):
        await confirm_verification(db_session, token)


async def test_confirm_verification_marks_booking_completed(
    db_session: AsyncSession,
    verification_data,
):
    response = await issue_verification_token(db_session, USER_ID)

    confirmed = await confirm_verification(db_session, response.token)

    assert confirmed.booking.id == verification_data["confirmed"].id
    assert confirmed.booking.status == "completed"
    assert confirmed.booking.can_verify is False
    assert verification_data["confirmed"].status == "completed"


async def test_completed_and_cancelled_bookings_cannot_be_confirmed(
    db_session: AsyncSession,
    verification_data,
):
    now = datetime.now(UTC)
    completed = verification_data["completed"]
    cancelled = verification_data["cancelled"]
    completed_token, _ = _create_verification_token(completed.id, str(USER_ID), now)
    cancelled_token, _ = _create_verification_token(cancelled.id, str(USER_ID), now)

    with pytest.raises(BookingAlreadyVerifiedError):
        await confirm_verification(db_session, completed_token)

    with pytest.raises(BookingNotVerifiableError):
        await confirm_verification(db_session, cancelled_token)
