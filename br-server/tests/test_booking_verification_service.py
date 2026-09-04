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
from app.services import booking_verification_service
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
        status="in_progress",
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
    pending_paid = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=today,
        start_time=time(9, 0),
        end_time=time(11, 0),
        status="pending_start",
        payment_status="paid",
        total_price=30.00,
    )
    pending_unpaid = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=today,
        start_time=time(14, 0),
        end_time=time(16, 0),
        status="pending_start",
        payment_status="pending",
        total_price=30.00,
    )
    db_session.add_all([confirmed, cancelled, completed, pending_paid, pending_unpaid])
    await db_session.flush()

    return {
        "user": user,
        "room": room,
        "seat": seat,
        "in_progress": confirmed,
        "cancelled": cancelled,
        "completed": completed,
        "pending_paid": pending_paid,
        "pending_unpaid": pending_unpaid,
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
    assert response.token.startswith("v1.")
    assert len(response.token) < 100
    assert response.verify_url.startswith("https://example.com/app/#/pages/verify-booking/index?token=")
    assert "/pages/verify-booking/index?token=" in response.verify_url
    assert 295 <= (response.expires_at - datetime.now(UTC)).total_seconds() <= 300
    assert response.booking.id == verification_data["in_progress"].id
    assert response.booking.user_id == str(USER_ID)
    assert response.booking.user_nickname == "Study User"
    assert response.booking.user_phone == "13800138000"
    assert response.booking.room_name == "Test Room"
    assert response.booking.seat_number == "A-01"
    assert response.booking.status == "in_progress"
    assert response.booking.can_verify is True


async def test_issue_verification_token_uses_relative_verify_url_without_frontend_base(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "")

    response = await issue_verification_token(db_session, USER_ID)

    assert response.token
    assert response.verify_url.startswith("/#/pages/verify-booking/index?token=")


async def test_issue_verification_token_allows_empty_jwt_secret_like_auth_service(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "")

    response = await issue_verification_token(db_session, USER_ID)

    assert response.token


def test_verification_window_uses_configured_business_timezone(verification_data):
    booking = verification_data["in_progress"]
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


async def test_issue_verification_token_without_verifiable_booking_raises(
    db_session: AsyncSession,
    verification_data,
):
    verification_data["in_progress"].status = "cancelled"
    verification_data["pending_paid"].status = "cancelled"
    await db_session.flush()

    with pytest.raises(NoVerifiableBookingError):
        await issue_verification_token(db_session, USER_ID)


async def test_issue_verification_token_for_future_booking_returns_token(
    db_session: AsyncSession,
    verification_data,
):
    verification_data["in_progress"].date = datetime.now(UTC).date() + timedelta(days=1)
    await db_session.flush()

    response = await issue_verification_token(db_session, USER_ID)

    assert response.token
    assert response.booking.id == verification_data["in_progress"].id
    assert response.booking.status == "in_progress"


async def test_issue_verification_token_selects_nearest_confirmed_booking(
    db_session: AsyncSession,
    verification_data,
):
    expired = verification_data["in_progress"]
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
        status="in_progress",
        total_price=45.00,
    )
    db_session.add(eligible)
    await db_session.flush()

    response = await issue_verification_token(db_session, USER_ID)

    assert response.booking.id == eligible.id


async def test_issue_verification_token_prefers_future_booking_over_stale_past(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    fixed_now = datetime(2026, 5, 12, 8, 40, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)
    stale = verification_data["in_progress"]
    room = verification_data["room"]
    seat = verification_data["seat"]
    stale.date = fixed_now.date()
    stale.start_time = time(8, 0)
    stale.end_time = time(8, 35)
    future = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=fixed_now.date(),
        start_time=time(12, 0),
        end_time=time(13, 0),
        status="in_progress",
        total_price=45.00,
    )
    db_session.add(future)
    await db_session.flush()

    response = await issue_verification_token(db_session, USER_ID)

    assert response.booking.id == future.id


async def test_issue_verification_token_prioritizes_early_arrival_window(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    fixed_now = datetime(2026, 5, 12, 8, 40, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)
    later = verification_data["in_progress"]
    room = verification_data["room"]
    seat = verification_data["seat"]
    later.date = fixed_now.date()
    later.start_time = time(12, 0)
    later.end_time = time(13, 0)
    early_arrival = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=fixed_now.date(),
        start_time=time(9, 0),
        end_time=time(10, 0),
        status="in_progress",
        total_price=45.00,
    )
    db_session.add(early_arrival)
    await db_session.flush()

    response = await issue_verification_token(db_session, USER_ID)

    assert response.booking.id == early_arrival.id


async def test_inspect_tampered_token_raises_invalid(
    db_session: AsyncSession,
    verification_data,
):
    response = await issue_verification_token(db_session, USER_ID)

    with pytest.raises(InvalidVerificationTokenError):
        await inspect_verification_token(db_session, response.token + "tampered")


async def test_legacy_jwt_verification_token_still_inspects(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["in_progress"]
    token, _ = booking_verification_service._create_legacy_jwt_verification_token(
        booking.id,
        str(USER_ID),
        datetime.now(UTC),
    )

    response = await inspect_verification_token(db_session, token)

    assert response.booking.id == booking.id


async def test_wrong_purpose_token_raises_invalid(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["in_progress"]
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
    booking = verification_data["in_progress"]
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
    booking = verification_data["in_progress"]
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
    booking = verification_data["in_progress"]
    token, _ = _create_verification_token(
        booking.id,
        str(USER_ID),
        datetime.now(UTC) - timedelta(minutes=6),
    )

    with pytest.raises(ExpiredVerificationTokenError):
        await inspect_verification_token(db_session, token)

    with pytest.raises(ExpiredVerificationTokenError):
        await confirm_verification(db_session, token)


async def test_confirm_verification_for_future_booking_returns_confirmed(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    """Future pending+paid booking (now <= end_time) should become confirmed."""
    booking = verification_data["pending_paid"]
    # end_time far in the future so real UTC now < end_time
    booking.start_time = time(0, 0)
    booking.end_time = time(23, 59)
    await db_session.flush()
    # Monkeypatch _booking_now to be before end_time for status determination
    today = booking.date
    fixed_now = datetime(today.year, today.month, today.day, 10, 0, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)
    # Token must use real UTC now because confirm_verification decodes with datetime.now(UTC)
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))

    confirmed = await confirm_verification(db_session, token)

    assert confirmed.booking.status == "in_progress"


async def test_confirm_verification_after_end_time_succeeds_with_valid_token(
    db_session: AsyncSession,
    verification_data,
):
    booking = verification_data["in_progress"]
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))
    booking.start_time = time(0, 0)
    booking.end_time = time(0, 1)
    await db_session.flush()

    confirmed = await confirm_verification(db_session, token)

    assert confirmed.booking.status == "completed"


async def test_confirm_verification_marks_booking_completed(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    """Confirmed booking with end_time in the past should become completed."""
    booking = verification_data["in_progress"]
    booking.start_time = time(0, 0)
    booking.end_time = time(0, 1)
    # Move pending_paid out of the way
    verification_data["pending_paid"].status = "cancelled"
    await db_session.flush()
    response = await issue_verification_token(db_session, USER_ID)

    confirmed = await confirm_verification(db_session, response.token)

    assert confirmed.booking.id == verification_data["in_progress"].id
    assert confirmed.booking.status == "completed"
    assert confirmed.booking.can_verify is False
    assert verification_data["in_progress"].status == "completed"


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


async def test_confirm_verification_pending_paid_becomes_confirmed_when_before_end_time(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    """pending+paid booking with now <= end_time should become confirmed."""
    booking = verification_data["pending_paid"]
    # Fix now to be before end_time (11:00) on the same date as the booking
    today = booking.date
    fixed_now = datetime(today.year, today.month, today.day, 10, 0, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))

    result = await confirm_verification(db_session, token)

    assert result.booking.status == "in_progress"
    # confirmed status → can_verify is True by design
    assert result.booking.can_verify is True


async def test_confirm_verification_pending_paid_becomes_completed_when_after_end_time(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    """pending+paid booking with now > end_time should become completed."""
    booking = verification_data["pending_paid"]
    # Fix now to be after end_time (11:00) on the same date as the booking
    today = booking.date
    fixed_now = datetime(today.year, today.month, today.day, 12, 0, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))

    result = await confirm_verification(db_session, token)

    assert result.booking.status == "completed"
    assert result.booking.can_verify is False


async def test_confirm_verification_confirmed_becomes_completed_when_after_end_time(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    """confirmed booking with now > end_time should become completed."""
    booking = verification_data["in_progress"]
    today = datetime.now(UTC).date()
    booking.date = today
    booking.start_time = time(9, 0)
    booking.end_time = time(10, 0)
    await db_session.flush()
    # Fix now to be after end_time on the same date
    fixed_now = datetime(today.year, today.month, today.day, 11, 0, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))

    result = await confirm_verification(db_session, token)

    assert result.booking.status == "completed"
    assert result.booking.can_verify is False


async def test_confirm_verification_pending_unpaid_raises_not_verifiable(
    db_session: AsyncSession,
    verification_data,
):
    """pending (unpaid) booking should raise BookingNotVerifiableError."""
    booking = verification_data["pending_unpaid"]
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))

    with pytest.raises(BookingNotVerifiableError):
        await confirm_verification(db_session, token)


async def test_issue_verification_token_includes_pending_paid_booking(
    db_session: AsyncSession,
    verification_data,
):
    """pending+paid booking should be verifiable and can_verify should be True."""
    # Set confirmed booking to past so it's not selected; pending_paid is today
    verification_data["in_progress"].date = date(2026, 1, 1)
    verification_data["in_progress"].status = "completed"
    await db_session.flush()

    response = await issue_verification_token(db_session, USER_ID)

    assert response.booking.id == verification_data["pending_paid"].id
    assert response.booking.status == "pending_start"
    assert response.booking.can_verify is True


async def test_confirm_verification_already_confirmed_with_future_end_time_raises(
    db_session: AsyncSession,
    verification_data,
    monkeypatch,
):
    """Idempotent protection: confirmed booking with now <= end_time must raise BookingAlreadyVerifiedError."""
    booking = verification_data["in_progress"]
    # Ensure booking is confirmed+paid with end_time in the future
    booking.status = "in_progress"
    booking.payment_status = "paid"
    today = datetime.now(UTC).date()
    booking.date = today
    booking.start_time = time(0, 0)
    booking.end_time = time(23, 59)
    await db_session.flush()
    # Fix now to be before end_time
    fixed_now = datetime(today.year, today.month, today.day, 10, 0, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)
    token, _ = _create_verification_token(booking.id, str(USER_ID), datetime.now(UTC))

    with pytest.raises(BookingAlreadyVerifiedError):
        await confirm_verification(db_session, token)


async def test_load_verifiable_bookings_includes_pending_paid(
    db_session: AsyncSession,
    verification_data,
):
    """_load_verifiable_booking_rows should return both confirmed and pending+paid bookings."""
    rows = await booking_verification_service._load_verifiable_booking_rows(
        db_session, USER_ID
    )
    booking_ids = {row[0].id for row in rows}
    assert verification_data["in_progress"].id in booking_ids
    assert verification_data["pending_paid"].id in booking_ids
    assert verification_data["pending_unpaid"].id not in booking_ids
    assert verification_data["cancelled"].id not in booking_ids
    assert verification_data["completed"].id not in booking_ids
