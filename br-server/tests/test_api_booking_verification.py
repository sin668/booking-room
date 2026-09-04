"""Integration tests for Booking Verification API."""

import uuid
from datetime import UTC, date, datetime, time, timedelta

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_admin, get_current_user_id
from app.core.config import settings
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.services.booking_verification_service import _create_verification_token

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")


@pytest.fixture(autouse=True)
def verification_secret(monkeypatch):
    monkeypatch.setattr(settings, "JWT_SECRET_KEY", "test-verification-secret")
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "https://booking.example.com")
    monkeypatch.setattr(settings, "BOOKING_TIMEZONE", "Asia/Shanghai")


@pytest.fixture
async def seed_verifiable_booking(db_session: AsyncSession):
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
    booking = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=today,
        start_time=time(0, 0),
        end_time=time(23, 59),
        status="in_progress",
        total_price=45.00,
    )
    db_session.add(booking)
    await db_session.flush()

    return {"user": user, "room": room, "seat": seat, "booking": booking}


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


async def test_user_can_issue_verification_token(
    auth_client: AsyncClient,
    seed_verifiable_booking,
    monkeypatch,
):
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "https://booking.example.com")

    response = await auth_client.post("/api/v1/booking-verifications/token")

    assert response.status_code == 200
    data = response.json()
    assert data["token"]
    assert data["verify_url"].startswith("https://booking.example.com/#/pages/verify-booking/index?token=")
    assert "expires_at" in data
    assert data["booking"]["id"] == seed_verifiable_booking["booking"].id
    assert data["booking"]["can_verify"] is True


async def test_user_can_list_verifiable_bookings(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_verifiable_booking,
):
    seat = Seat(
        room_id=seed_verifiable_booking["room"].id,
        seat_number="A-02",
        zone="quiet",
        position="center",
        floor=3,
        price_per_hour=15.00,
        status="available",
        row=1,
        col=2,
    )
    db_session.add(seat)
    await db_session.flush()
    second_booking = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=seed_verifiable_booking["room"].id,
        date=datetime.now(UTC).date(),
        start_time=time(0, 0),
        end_time=time(23, 59),
        status="in_progress",
        total_price=45.00,
    )
    db_session.add(second_booking)
    await db_session.flush()

    response = await auth_client.get("/api/v1/booking-verifications/bookings")

    assert response.status_code == 200
    data = response.json()
    assert [item["id"] for item in data["items"]] == [
        seed_verifiable_booking["booking"].id,
        second_booking.id,
    ]


async def test_user_can_issue_verification_token_for_selected_booking(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_verifiable_booking,
):
    seat = Seat(
        room_id=seed_verifiable_booking["room"].id,
        seat_number="A-03",
        zone="vip",
        position="corner",
        floor=3,
        price_per_hour=30.00,
        status="available",
        row=1,
        col=3,
    )
    db_session.add(seat)
    await db_session.flush()
    selected_booking = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=seed_verifiable_booking["room"].id,
        date=datetime.now(UTC).date(),
        start_time=time(0, 0),
        end_time=time(23, 59),
        status="in_progress",
        total_price=90.00,
    )
    db_session.add(selected_booking)
    await db_session.flush()

    response = await auth_client.post(
        "/api/v1/booking-verifications/token",
        json={"booking_id": selected_booking.id},
    )

    assert response.status_code == 200
    assert response.json()["booking"]["id"] == selected_booking.id


async def test_user_can_issue_verification_token_without_frontend_base_url(
    auth_client: AsyncClient,
    seed_verifiable_booking,
    monkeypatch,
):
    monkeypatch.setattr(settings, "FRONTEND_BASE_URL", "")

    response = await auth_client.post("/api/v1/booking-verifications/token")

    assert response.status_code == 200
    assert response.json()["verify_url"].startswith("/#/pages/verify-booking/index?token=")


async def test_admin_can_inspect_verification_token(
    auth_client: AsyncClient,
    seed_verifiable_booking,
):
    token = (await auth_client.post("/api/v1/booking-verifications/token")).json()["token"]

    response = await auth_client.get(f"/api/v1/booking-verifications/{token}")

    assert response.status_code == 200
    data = response.json()
    assert data["booking"]["id"] == seed_verifiable_booking["booking"].id
    assert data["booking"]["status"] == "in_progress"
    assert data["booking"]["can_verify"] is True


async def test_admin_can_confirm_verification(
    auth_client: AsyncClient,
    seed_verifiable_booking,
    db_session: AsyncSession,
):
    booking = seed_verifiable_booking["booking"]
    # Set end_time in the past so confirm results in "completed"
    booking.end_time = time(0, 1)
    await db_session.flush()
    token = (await auth_client.post("/api/v1/booking-verifications/token")).json()["token"]

    response = await auth_client.post(f"/api/v1/booking-verifications/{token}/confirm")

    assert response.status_code == 200
    data = response.json()
    assert data["booking"]["status"] == "completed"
    assert data["booking"]["can_verify"] is False
    assert seed_verifiable_booking["booking"].status == "completed"


async def test_admin_can_confirm_future_booking_returns_confirmed(
    auth_client: AsyncClient,
    seed_verifiable_booking,
    db_session: AsyncSession,
):
    """Future pending+paid booking (now <= end_time) should become confirmed, not completed."""
    booking = seed_verifiable_booking["booking"]
    booking.status = "pending_start"
    booking.payment_status = "paid"
    # end_time=23:59 ensures real now <= end_time so status stays confirmed
    booking.start_time = time(0, 0)
    booking.end_time = time(23, 59)
    await db_session.flush()
    token = (await auth_client.post("/api/v1/booking-verifications/token")).json()["token"]

    response = await auth_client.post(f"/api/v1/booking-verifications/{token}/confirm")

    assert response.status_code == 200
    assert response.json()["booking"]["status"] == "in_progress"


async def test_real_admin_header_can_inspect_and_confirm(
    auth_client: AsyncClient,
    seed_verifiable_booking,
    db_session: AsyncSession,
    monkeypatch,
):
    booking = seed_verifiable_booking["booking"]
    booking.end_time = time(0, 1)
    await db_session.flush()
    token = (await auth_client.post("/api/v1/booking-verifications/token")).json()["token"]
    app = auth_client._transport.app
    app.dependency_overrides.pop(get_current_admin, None)
    monkeypatch.setattr(settings, "ADMIN_TOKEN", "real-admin-token")
    headers = {"X-Admin-Token": "real-admin-token"}

    inspect_response = await auth_client.get(
        f"/api/v1/booking-verifications/{token}",
        headers=headers,
    )
    confirm_response = await auth_client.post(
        f"/api/v1/booking-verifications/{token}/confirm",
        headers=headers,
    )

    assert inspect_response.status_code == 200
    assert confirm_response.status_code == 200
    assert confirm_response.json()["booking"]["status"] == "completed"


async def test_issue_requires_user_auth(client: AsyncClient, seed_verifiable_booking):
    app = client._transport.app
    app.dependency_overrides.pop(get_current_user_id, None)

    response = await client.post("/api/v1/booking-verifications/token")

    assert response.status_code == 401


async def test_inspect_and_confirm_require_admin_auth(
    auth_client: AsyncClient,
    seed_verifiable_booking,
):
    token = (await auth_client.post("/api/v1/booking-verifications/token")).json()["token"]
    app = auth_client._transport.app
    app.dependency_overrides.pop(get_current_admin, None)

    inspect_response = await auth_client.get(f"/api/v1/booking-verifications/{token}")
    confirm_response = await auth_client.post(f"/api/v1/booking-verifications/{token}/confirm")

    assert inspect_response.status_code == 401
    assert confirm_response.status_code == 401


async def test_expired_token_returns_410(
    auth_client: AsyncClient,
    seed_verifiable_booking,
):
    booking = seed_verifiable_booking["booking"]
    token, _ = _create_verification_token(
        booking.id,
        str(USER_ID),
        datetime.now(UTC) - timedelta(minutes=6),
    )

    response = await auth_client.get(f"/api/v1/booking-verifications/{token}")

    assert response.status_code == 410


async def test_repeated_confirm_returns_409(
    auth_client: AsyncClient,
    seed_verifiable_booking,
    db_session: AsyncSession,
):
    booking = seed_verifiable_booking["booking"]
    # Set end_time in the past so first confirm results in "completed"
    booking.end_time = time(0, 1)
    await db_session.flush()
    token = (await auth_client.post("/api/v1/booking-verifications/token")).json()["token"]
    first = await auth_client.post(f"/api/v1/booking-verifications/{token}/confirm")
    second = await auth_client.post(f"/api/v1/booking-verifications/{token}/confirm")

    assert first.status_code == 200
    assert second.status_code == 409


async def test_admin_can_confirm_pending_paid_booking(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_verifiable_booking,
    monkeypatch,
):
    """pending+paid booking can be verified via API and returns confirmed/completed."""
    from app.services.booking_verification_service import _booking_timezone
    from app.services import booking_verification_service

    booking = seed_verifiable_booking["booking"]
    booking.status = "pending_start"
    booking.payment_status = "paid"
    booking.start_time = time(9, 0)
    booking.end_time = time(23, 59)  # end_time far in the future today
    await db_session.flush()

    # Issue token first (uses real _booking_now for token timestamp)
    token_resp = await auth_client.post("/api/v1/booking-verifications/token")
    assert token_resp.status_code == 200
    token = token_resp.json()["token"]

    # Now patch _booking_now to be before end_time for the confirm step
    today = booking.date
    fixed_now = datetime(today.year, today.month, today.day, 10, 0, tzinfo=_booking_timezone())
    monkeypatch.setattr(booking_verification_service, "_booking_now", lambda: fixed_now)

    response = await auth_client.post(f"/api/v1/booking-verifications/{token}/confirm")

    assert response.status_code == 200
    assert response.json()["booking"]["status"] == "in_progress"


async def test_confirm_already_confirmed_booking_returns_409(
    auth_client: AsyncClient,
    seed_verifiable_booking,
    db_session: AsyncSession,
):
    """Idempotent protection: confirming a confirmed booking with now <= end_time returns 409."""
    booking = seed_verifiable_booking["booking"]
    # confirmed+paid with end_time=23:59 ensures real now <= end_time
    booking.status = "in_progress"
    booking.payment_status = "paid"
    booking.start_time = time(0, 0)
    booking.end_time = time(23, 59)
    await db_session.flush()
    token = (await auth_client.post("/api/v1/booking-verifications/token")).json()["token"]

    response = await auth_client.post(f"/api/v1/booking-verifications/{token}/confirm")

    assert response.status_code == 409


async def test_pending_unpaid_booking_cannot_be_verified(
    auth_client: AsyncClient,
    db_session: AsyncSession,
    seed_verifiable_booking,
):
    """pending (unpaid) booking should return 400 when trying to verify."""
    booking = seed_verifiable_booking["booking"]
    booking.status = "pending_start"
    booking.payment_status = "pending"
    await db_session.flush()

    response = await auth_client.post("/api/v1/booking-verifications/token")

    assert response.status_code == 404
