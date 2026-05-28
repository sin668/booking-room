"""Integration tests for Booking API."""

import uuid
from datetime import UTC, date, datetime, timedelta, time
from decimal import Decimal
from unittest.mock import AsyncMock, patch

import pytest
from httpx import AsyncClient
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.services.booking_payment_service import PaymentProviderUnavailableError

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")
NOW = datetime.now(UTC)


@pytest.fixture
async def seed_room_seat(db_session: AsyncSession):
    """Insert a study room with seats into the test database."""
    room = StudyRoom(
        name="Test Room",
        address="123 Test St",
        status="open",
        min_price=10.00,
    )
    db_session.add(room)
    await db_session.flush()

    seat_a = Seat(
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
    seat_b = Seat(
        room_id=room.id,
        seat_number="A-02",
        zone="quiet",
        position="center",
        floor=3,
        price_per_hour=20.00,
        status="available",
        row=1,
        col=2,
    )
    seat_m = Seat(
        room_id=room.id,
        seat_number="B-01",
        zone="vip",
        position="corner",
        floor=3,
        price_per_hour=30.00,
        status="maintenance",
        row=2,
        col=1,
    )
    db_session.add(seat_a)
    db_session.add(seat_b)
    db_session.add(seat_m)
    await db_session.flush()

    return {"room": room, "seat_a": seat_a, "seat_b": seat_b, "seat_m": seat_m}


@pytest.fixture
async def seed_booking_coupon(db_session: AsyncSession):
    coupon = Coupon(
        name="满20减3",
        description="全场通用",
        type="threshold_amount_off",
        discount_amount=Decimal("3.00"),
        discount_percent=None,
        min_order_amount=Decimal("20.00"),
        scope="all",
        seat_zone=None,
        valid_from=NOW - timedelta(days=1),
        expires_at=NOW + timedelta(days=1),
        is_active=True,
    )
    db_session.add(coupon)
    await db_session.flush()

    user_coupon = UserCoupon(
        user_id=str(USER_ID),
        coupon_id=coupon.id,
        status="available",
    )
    db_session.add(user_coupon)
    await db_session.flush()

    return user_coupon


@pytest.fixture
async def auth_client(client: AsyncClient):
    """Create a client with mocked auth returning USER_ID."""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def other_auth_client(client: AsyncClient):
    """Create a client with mocked auth returning OTHER_USER_ID."""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: OTHER_USER_ID
    yield client
    app.dependency_overrides.clear()


class TestCreateBooking:
    """POST /api/v1/bookings"""

    @pytest.mark.asyncio
    async def test_create_booking_success(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        db_session.add(
            User(
                id=USER_ID,
                phone="18800000010",
                nickname="Balance User",
                password_hash="hash",
                balance=Decimal("100.00"),
            )
        )
        await db_session.flush()

        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["seat_id"] == seat.id
        assert data["user_id"] == str(USER_ID)
        assert data["date"] == "2026-05-01"
        assert data["start_time"] == "09:00:00"
        assert data["end_time"] == "12:00:00"
        assert data["status"] == "confirmed"
        assert data["original_price"] == "45.00"
        assert data["discount_amount"] == "0.00"
        assert data["total_price"] == "45.00"  # 3 hours * 15.00
        assert data["coupon_id"] is None
        assert data["payment_method"] == "balance"
        assert data["payment_status"] == "paid"
        assert data["seat"]["seat_number"] == "A-01"
        assert data["seat"]["zone"] == "quiet"
        assert data["seat"]["position"] == "window"
        assert data["seat"]["price_per_hour"] in ("15.00", "15.0")
        assert data["room"]["name"] == "Test Room"
        assert data["room"]["address"] == "123 Test St"
        assert "id" in data
        assert "created_at" in data

    @pytest.mark.asyncio
    async def test_create_booking_with_coupon_marks_coupon_used(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
        seed_booking_coupon: UserCoupon,
    ):
        db_session.add(
            User(
                id=USER_ID,
                phone="18800000011",
                nickname="Coupon Balance User",
                password_hash="hash",
                balance=Decimal("100.00"),
            )
        )
        await db_session.flush()

        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
                "coupon_id": seed_booking_coupon.id,
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["original_price"] == "45.00"
        assert data["discount_amount"] == "3.00"
        assert data["total_price"] == "42.00"
        assert data["coupon_id"] == seed_booking_coupon.id

        await db_session.refresh(seed_booking_coupon)
        assert seed_booking_coupon.status == "used"
        assert seed_booking_coupon.used_booking_id == data["id"]
        assert seed_booking_coupon.used_at is not None
        assert seed_booking_coupon.used_at.tzinfo is None

    @pytest.mark.asyncio
    async def test_create_booking_with_invalid_coupon_does_not_create_booking_or_mutate_coupon(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
        seed_booking_coupon: UserCoupon,
    ):
        seed_booking_coupon.user_id = str(OTHER_USER_ID)
        await db_session.flush()

        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
                "coupon_id": seed_booking_coupon.id,
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "卡券不可用，请重新选择"

        bookings = (
            await db_session.execute(
                Booking.__table__.select().where(Booking.user_id == str(USER_ID))
            )
        ).all()
        assert bookings == []
        await db_session.refresh(seed_booking_coupon)
        assert seed_booking_coupon.status == "available"
        assert seed_booking_coupon.used_booking_id is None
        assert seed_booking_coupon.used_at is None

    @pytest.mark.asyncio
    async def test_create_booking_with_balance_payment_deducts_balance_and_creates_consume_transaction(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        db_session.add(
            User(
                id=USER_ID,
                phone="18800000001",
                nickname="Wallet User",
                password_hash="hash",
                balance=Decimal("100.00"),
            )
        )
        await db_session.flush()

        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 201
        data = resp.json()
        assert data["total_price"] == "45.00"
        assert data["payment_method"] == "balance"
        assert data["payment_status"] == "paid"

        user = await db_session.get(User, USER_ID)
        assert user is not None
        assert user.balance == Decimal("55.00")

        tx_result = await db_session.execute(
            select(WalletTransaction).where(WalletTransaction.user_id == str(USER_ID))
        )
        tx = tx_result.scalar_one()
        assert tx.type == "consume"
        assert tx.amount == Decimal("45.00")
        assert tx.status == "completed"
        assert tx.payment_method == "balance"
        assert tx.balance_after == Decimal("55.00")

    @pytest.mark.asyncio
    async def test_create_booking_with_balance_payment_insufficient_balance_does_not_create_booking_or_transaction(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        db_session.add(
            User(
                id=USER_ID,
                phone="18800000002",
                nickname="Poor Wallet User",
                password_hash="hash",
                balance=Decimal("10.00"),
            )
        )
        await db_session.flush()

        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
                "payment_method": "balance",
            },
        )
        assert resp.status_code == 402

        bookings = (
            await db_session.execute(
                Booking.__table__.select().where(Booking.user_id == str(USER_ID))
            )
        ).all()
        assert bookings == []

        tx_count = await db_session.scalar(
            select(func.count()).select_from(WalletTransaction).where(WalletTransaction.user_id == str(USER_ID))
        )
        assert tx_count == 0

    @pytest.mark.asyncio
    async def test_create_booking_with_wechat_payment_returns_params_without_deducting_balance(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        user = User(
            id=USER_ID,
            phone="18800000003",
            nickname="WeChat Booking User",
            password_hash="hash",
            balance=Decimal("100.00"),
            wechat_openid="openid-123",
        )
        db_session.add(user)
        await db_session.flush()
        payment_service = AsyncMock()
        payment_service.create_booking_payment.return_value = {
            "timeStamp": "1",
            "nonceStr": "nonce",
            "package": "prepay_id=prepay-123",
            "signType": "RSA",
            "paySign": "sig",
        }

        seat = seed_room_seat["seat_a"]
        with patch("app.api.routes.booking._payment_service", return_value=payment_service):
            resp = await auth_client.post(
                "/api/v1/bookings",
                json={
                    "seat_id": seat.id,
                    "date": "2026-05-01",
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "payment_method": "wechat",
                },
            )

        assert resp.status_code == 201
        data = resp.json()
        assert data["status"] == "pending"
        assert data["payment_method"] == "wechat"
        assert data["payment_status"] == "pending"
        assert data["payment_params"]["package"] == "prepay_id=prepay-123"
        await db_session.refresh(user)
        assert user.balance == Decimal("100.00")

        tx_count = await db_session.scalar(
            select(func.count()).select_from(WalletTransaction).where(WalletTransaction.user_id == str(USER_ID))
        )
        assert tx_count == 0

    @pytest.mark.asyncio
    async def test_pending_wechat_payment_appears_in_all_but_not_confirmed_booking_list(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        user = User(
            id=USER_ID,
            phone="18800000014",
            nickname="WeChat Cancel User",
            password_hash="hash",
            balance=Decimal("100.00"),
            wechat_openid="openid-123",
        )
        db_session.add(user)
        await db_session.flush()
        payment_service = AsyncMock()
        payment_service.create_booking_payment.return_value = {
            "timeStamp": "1",
            "nonceStr": "nonce",
            "package": "prepay_id=prepay-123",
            "signType": "RSA",
            "paySign": "sig",
        }

        seat = seed_room_seat["seat_a"]
        with patch("app.api.routes.booking._payment_service", return_value=payment_service):
            resp = await auth_client.post(
                "/api/v1/bookings",
                json={
                    "seat_id": seat.id,
                    "date": "2026-05-01",
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "payment_method": "wechat",
                },
            )

        assert resp.status_code == 201
        assert resp.json()["status"] == "pending"

        confirmed_resp = await auth_client.get("/api/v1/bookings", params={"status": "confirmed"})

        assert confirmed_resp.status_code == 200
        confirmed_data = confirmed_resp.json()
        assert confirmed_data["total"] == 0
        assert confirmed_data["items"] == []

        all_resp = await auth_client.get("/api/v1/bookings")

        assert all_resp.status_code == 200
        all_data = all_resp.json()
        assert all_data["total"] == 1
        assert all_data["items"][0]["status"] == "pending"

    @pytest.mark.asyncio
    async def test_pending_wechat_payment_locks_seat_until_cancelled(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        db_session.add(
            User(
                id=USER_ID,
                phone="18800000015",
                nickname="Seat Lock User",
                password_hash="hash",
                balance=Decimal("100.00"),
            )
        )
        await db_session.flush()
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="pending",
            total_price=Decimal("45.00"),
            payment_method="wechat",
            payment_status="pending",
            payment_provider="wechat",
        )
        db_session.add(booking)
        await db_session.flush()

        locked_resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
                "payment_method": "balance",
            },
        )

        assert locked_resp.status_code == 409

        booking.status = "cancelled"
        booking.payment_status = "failed"
        await db_session.flush()

        unlocked_resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
                "payment_method": "balance",
            },
        )

        assert unlocked_resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_booking_with_wechat_payment_unavailable_returns_503(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        user = User(
            id=USER_ID,
            phone="18800000013",
            nickname="WeChat Unavailable User",
            password_hash="hash",
            balance=Decimal("100.00"),
            wechat_openid="openid-123",
        )
        db_session.add(user)
        await db_session.flush()

        payment_service = AsyncMock()
        payment_service.create_booking_payment.side_effect = (
            PaymentProviderUnavailableError("WeChat Pay is disabled or misconfigured")
        )

        seat = seed_room_seat["seat_a"]
        with patch("app.api.routes.booking._payment_service", return_value=payment_service):
            resp = await auth_client.post(
                "/api/v1/bookings",
                json={
                    "seat_id": seat.id,
                    "date": "2026-05-01",
                    "start_time": "09:00",
                    "end_time": "12:00",
                    "payment_method": "wechat",
                },
            )

        assert resp.status_code == 503
        booking_count = await db_session.scalar(
            select(func.count()).select_from(Booking).where(Booking.user_id == str(USER_ID))
        )
        assert booking_count == 0

    @pytest.mark.asyncio
    async def test_create_booking_no_auth(self, client: AsyncClient, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        resp = await client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_create_booking_nonexistent_seat(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": 99999,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 404
        assert resp.json()["detail"] == "座位不存在"

    @pytest.mark.asyncio
    async def test_create_booking_time_conflict(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        # Create existing booking: 08:00-10:00
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id="other-user",
                room_id=room.id,
                date=date(2026, 5, 1),
                start_time=time(8, 0),
                end_time=time(10, 0),
                status="confirmed",
                total_price=30.00,
            )
        )
        await db_session.flush()

        # Try booking 09:00-12:00 (overlaps with 08:00-10:00)
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 409
        assert resp.json()["detail"] == "该座位该时段已被预约"

    @pytest.mark.asyncio
    async def test_create_booking_invalid_time_range(self, auth_client: AsyncClient, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "12:00",
                "end_time": "09:00",
            },
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_create_booking_seat_under_maintenance(self, auth_client: AsyncClient, seed_room_seat):
        seat = seed_room_seat["seat_m"]
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "该座位正在维护中"

    @pytest.mark.asyncio
    async def test_create_booking_cancelled_does_not_conflict(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        db_session.add(
            User(
                id=USER_ID,
                phone="18800000012",
                nickname="Conflict Balance User",
                password_hash="hash",
                balance=Decimal("100.00"),
            )
        )
        await db_session.flush()

        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        # Create cancelled booking
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id="other-user",
                room_id=room.id,
                date=date(2026, 5, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                status="cancelled",
                total_price=45.00,
            )
        )
        await db_session.flush()

        # Should succeed since previous booking was cancelled
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={
                "seat_id": seat.id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 201

    @pytest.mark.asyncio
    async def test_create_booking_missing_fields(self, auth_client: AsyncClient):
        resp = await auth_client.post(
            "/api/v1/bookings",
            json={"seat_id": 1},
        )
        assert resp.status_code == 422


class TestListBookings:
    """GET /api/v1/bookings"""

    @pytest.mark.asyncio
    async def test_list_bookings_default_pagination(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        for i in range(3):
            db_session.add(
                Booking(
                    seat_id=seat.id,
                    user_id=str(USER_ID),
                    room_id=room.id,
                    date=date(2026, 5, 1 + i),
                    start_time=time(9, 0),
                    end_time=time(12, 0),
                    status="confirmed",
                    total_price=45.00,
                )
            )
        await db_session.flush()

        resp = await auth_client.get("/api/v1/bookings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert data["page"] == 1
        assert data["page_size"] == 10
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_bookings_filter_by_status(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id=str(USER_ID),
                room_id=room.id,
                date=date(2026, 5, 1),
                start_time=time(9, 0),
                end_time=time(12, 0),
                status="confirmed",
                total_price=45.00,
            )
        )
        db_session.add(
            Booking(
                seat_id=seat.id,
                user_id=str(USER_ID),
                room_id=room.id,
                date=date(2026, 5, 2),
                start_time=time(14, 0),
                end_time=time(17, 0),
                status="cancelled",
                total_price=45.00,
            )
        )
        await db_session.flush()

        resp = await auth_client.get("/api/v1/bookings", params={"status": "confirmed"})
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["status"] == "confirmed"

    @pytest.mark.asyncio
    async def test_list_bookings_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/bookings")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_list_bookings_empty(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/v1/bookings")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 0
        assert data["items"] == []


class TestGetBooking:
    """GET /api/v1/bookings/{booking_id}"""

    @pytest.mark.asyncio
    async def test_get_own_booking(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=45.00,
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.get(f"/api/v1/bookings/{booking.id}")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == booking.id
        assert data["seat"]["seat_number"] == "A-01"
        assert data["room"]["name"] == "Test Room"

    @pytest.mark.asyncio
    async def test_get_other_users_booking_404(self, other_auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=45.00,
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await other_auth_client.get(f"/api/v1/bookings/{booking.id}")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_get_nonexistent_booking(self, auth_client: AsyncClient):
        resp = await auth_client.get("/api/v1/bookings/99999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_get_booking_no_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/bookings/1")
        assert resp.status_code == 401


class TestBookingPaymentEndpoints:
    @pytest.mark.asyncio
    async def test_get_payment_status_own_booking(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        paid_at = datetime(2026, 5, 1, 10, 0, 0)
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="wechat",
            payment_status="paid",
            payment_provider="wechat",
            paid_at=paid_at,
            transaction_id="txn-123",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.get(f"/api/v1/bookings/{booking.id}/payment-status")

        assert resp.status_code == 200
        data = resp.json()
        assert data["booking_id"] == booking.id
        assert data["payment_status"] == "paid"
        assert data["transaction_id"] == "txn-123"
        assert data["paid_at"] == "2026-05-01T10:00:00"

    @pytest.mark.asyncio
    async def test_get_payment_status_other_user_returns_404(
        self,
        other_auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
    ):
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date(2026, 5, 1),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="wechat",
            payment_status="pending",
            payment_provider="wechat",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await other_auth_client.get(f"/api/v1/bookings/{booking.id}/payment-status")

        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_wechat_notify_success(self, client: AsyncClient):
        payment_service = AsyncMock()
        payment_service.process_wechat_notify.return_value = {
            "code": "SUCCESS",
            "message": "success",
        }

        with patch("app.api.routes.booking._payment_service", return_value=payment_service):
            resp = await client.post(
                "/api/v1/bookings/wechat/notify",
                content=b"{}",
                headers={"Wechatpay-Signature": "valid"},
            )

        assert resp.status_code == 200
        assert resp.json() == {"code": "SUCCESS", "message": "success"}
        payment_service.process_wechat_notify.assert_awaited_once()


class TestCancelBooking:
    """POST /api/v1/bookings/{booking_id}/cancel"""

    async def _seed_user(self, db_session: AsyncSession, balance=Decimal("10.00")) -> User:
        user = User(
            id=USER_ID,
            phone="18800009999",
            nickname="Cancel User",
            password_hash="hash",
            balance=balance,
        )
        db_session.add(user)
        await db_session.flush()
        return user

    @pytest.mark.asyncio
    async def test_cancel_booking_success(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        user = await self._seed_user(db_session, Decimal("10.00"))
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date.today() + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "cancelled"
        assert data["cancel_policy"] == "over_48h"
        assert data["penalty_amount"] == "0.00"
        assert data["refund_amount"] == "45.00"
        assert data["can_cancel"] is False
        assert data["refund_transaction_id"] is not None

        await db_session.refresh(user)
        assert user.balance == Decimal("55.00")
        tx = (
            await db_session.execute(
                select(WalletTransaction).where(
                    WalletTransaction.booking_id == booking.id,
                    WalletTransaction.type == "booking_refund",
                )
            )
        ).scalar_one()
        assert tx.amount == Decimal("45.00")
        assert tx.balance_after == Decimal("55.00")
        assert tx.status == "completed"

    @pytest.mark.asyncio
    async def test_cancel_booking_restores_used_coupon(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
        seed_booking_coupon: UserCoupon,
    ):
        await self._seed_user(db_session, Decimal("10.00"))
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date.today() + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            original_price=Decimal("45.00"),
            discount_amount=Decimal("3.00"),
            total_price=Decimal("42.00"),
            coupon_id=seed_booking_coupon.id,
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()
        seed_booking_coupon.status = "used"
        seed_booking_coupon.used_booking_id = booking.id
        seed_booking_coupon.used_at = NOW
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        assert resp.status_code == 200
        assert resp.json()["status"] == "cancelled"

        await db_session.refresh(seed_booking_coupon)
        assert seed_booking_coupon.status == "available"
        assert seed_booking_coupon.used_booking_id is None
        assert seed_booking_coupon.used_at is None

    @pytest.mark.asyncio
    async def test_cancel_already_cancelled(self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        await self._seed_user(db_session)
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date.today() + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="cancelled",
            total_price=Decimal("45.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        assert resp.status_code == 400
        assert resp.json()["detail"] == "该预约已取消"

    @pytest.mark.asyncio
    async def test_cancel_other_users_booking(self, other_auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat):
        await self._seed_user(db_session)
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date.today() + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await other_auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_cancel_nonexistent_booking(self, auth_client: AsyncClient):
        resp = await auth_client.post("/api/v1/bookings/99999/cancel/")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "预约不存在"

    @pytest.mark.asyncio
    async def test_cancel_no_auth(self, client: AsyncClient):
        resp = await client.post("/api/v1/bookings/1/cancel/")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_cancel_booking_24_to_48_hours_charges_10_percent(
        self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat
    ):
        user = await self._seed_user(db_session, Decimal("0.00"))
        start_at = datetime.now() + timedelta(hours=36)
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=start_at.date(),
            start_time=start_at.time().replace(microsecond=0),
            end_time=(start_at + timedelta(hours=2)).time().replace(microsecond=0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="wechat",
            payment_status="paid",
            payment_provider="wechat",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")

        assert resp.status_code == 200
        assert resp.json()["penalty_amount"] == "4.50"
        assert resp.json()["refund_amount"] == "40.50"
        await db_session.refresh(user)
        assert user.balance == Decimal("40.50")

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        ("hours_before_start", "expected_policy", "expected_penalty", "expected_refund"),
        [
            (12, "2h_24h", "20.00", "80.00"),
            (1, "within_2h", "50.00", "50.00"),
        ],
    )
    async def test_cancel_booking_refund_tiers(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
        seed_room_seat,
        hours_before_start,
        expected_policy,
        expected_penalty,
        expected_refund,
    ):
        user = await self._seed_user(db_session, Decimal("0.00"))
        start_at = datetime.now() + timedelta(hours=hours_before_start)
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=start_at.date(),
            start_time=start_at.time().replace(microsecond=0),
            end_time=(start_at + timedelta(hours=2)).time().replace(microsecond=0),
            status="confirmed",
            total_price=Decimal("100.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["cancel_policy"] == expected_policy
        assert data["penalty_amount"] == expected_penalty
        assert data["refund_amount"] == expected_refund
        await db_session.refresh(user)
        assert user.balance == Decimal(expected_refund)

    @pytest.mark.asyncio
    async def test_cancel_started_booking_marks_completed_and_no_refund(
        self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat
    ):
        user = await self._seed_user(db_session, Decimal("0.00"))
        started_at = datetime.now() - timedelta(minutes=1)
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=started_at.date(),
            start_time=started_at.time().replace(microsecond=0),
            end_time=(started_at + timedelta(hours=2)).time().replace(microsecond=0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")

        assert resp.status_code == 400
        assert resp.json()["detail"] == "预约已开始不可取消"
        await db_session.refresh(booking)
        await db_session.refresh(user)
        assert booking.status == "completed"
        assert user.balance == Decimal("0.00")
        count = (
            await db_session.execute(
                select(func.count()).select_from(WalletTransaction).where(
                    WalletTransaction.booking_id == booking.id,
                    WalletTransaction.type == "booking_refund",
                )
            )
        ).scalar_one()
        assert count == 0

    @pytest.mark.asyncio
    async def test_cancel_unpaid_booking_rejected_without_refund(
        self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat
    ):
        user = await self._seed_user(db_session, Decimal("0.00"))
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date.today() + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="wechat",
            payment_status="pending",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")

        assert resp.status_code == 400
        assert resp.json()["detail"] == "未支付预约不可取消"
        await db_session.refresh(user)
        assert user.balance == Decimal("0.00")

    @pytest.mark.asyncio
    async def test_duplicate_cancel_does_not_refund_twice(
        self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat
    ):
        user = await self._seed_user(db_session, Decimal("0.00"))
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=date.today() + timedelta(days=3),
            start_time=time(9, 0),
            end_time=time(12, 0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        first = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")
        second = await auth_client.post(f"/api/v1/bookings/{booking.id}/cancel/")

        assert first.status_code == 200
        assert second.status_code == 400
        await db_session.refresh(user)
        assert user.balance == Decimal("45.00")
        count = (
            await db_session.execute(
                select(func.count()).select_from(WalletTransaction).where(
                    WalletTransaction.booking_id == booking.id,
                    WalletTransaction.type == "booking_refund",
                )
            )
        ).scalar_one()
        assert count == 1

    @pytest.mark.asyncio
    async def test_list_and_detail_sync_started_booking_to_completed(
        self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat
    ):
        await self._seed_user(db_session, Decimal("0.00"))
        started_at = datetime.now() - timedelta(minutes=1)
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=started_at.date(),
            start_time=started_at.time().replace(microsecond=0),
            end_time=(started_at + timedelta(hours=2)).time().replace(microsecond=0),
            status="confirmed",
            total_price=Decimal("45.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        list_resp = await auth_client.get("/api/v1/bookings")
        detail_resp = await auth_client.get(f"/api/v1/bookings/{booking.id}")

        assert list_resp.status_code == 200
        assert list_resp.json()["items"][0]["status"] == "completed"
        assert list_resp.json()["items"][0]["can_cancel"] is False
        assert detail_resp.status_code == 200
        assert detail_resp.json()["status"] == "completed"
        assert detail_resp.json()["can_cancel"] is False

    @pytest.mark.asyncio
    async def test_list_future_same_day_booking_returns_cancel_penalty_preview(
        self, auth_client: AsyncClient, db_session: AsyncSession, seed_room_seat
    ):
        await self._seed_user(db_session, Decimal("0.00"))
        start_at = datetime.now() + timedelta(hours=3)
        seat = seed_room_seat["seat_a"]
        room = seed_room_seat["room"]
        booking = Booking(
            seat_id=seat.id,
            user_id=str(USER_ID),
            room_id=room.id,
            date=start_at.date(),
            start_time=start_at.time().replace(microsecond=0),
            end_time=(start_at + timedelta(hours=2)).time().replace(microsecond=0),
            status="confirmed",
            total_price=Decimal("100.00"),
            payment_method="balance",
            payment_status="paid",
        )
        db_session.add(booking)
        await db_session.flush()

        resp = await auth_client.get("/api/v1/bookings")

        assert resp.status_code == 200
        item = resp.json()["items"][0]
        assert item["can_cancel"] is True
        assert Decimal(item["penalty_amount"]) == Decimal("0.00")
        assert Decimal(item["cancel_penalty_amount"]) == Decimal("20.00")
        assert Decimal(item["cancel_refund_amount"]) == Decimal("80.00")
