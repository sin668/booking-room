"""Integration tests for coupon API endpoints."""

import uuid
from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.models.coupon import Coupon, UserCoupon
from app.models.seat import Seat
from app.models.study_room import StudyRoom


USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
NOW = datetime.now(UTC)


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.clear()


@pytest.fixture
async def seed_coupon_data(db_session: AsyncSession):
    room = StudyRoom(name="Test Room", address="123 Test St", status="open", min_price=10.00)
    db_session.add(room)
    await db_session.flush()

    seat = Seat(
        room_id=room.id,
        seat_number="A-01",
        zone="vip",
        position="window",
        floor=3,
        price_per_hour=Decimal("20.00"),
        status="available",
        row=1,
        col=1,
    )
    db_session.add(seat)
    await db_session.flush()

    coupon_active = Coupon(
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
    coupon_expired = Coupon(
        name="过期券",
        description="已过期",
        type="amount_off",
        discount_amount=Decimal("5.00"),
        discount_percent=None,
        min_order_amount=Decimal("0.00"),
        scope="all",
        seat_zone=None,
        valid_from=NOW - timedelta(days=2),
        expires_at=NOW - timedelta(hours=1),
        is_active=True,
    )
    coupon_used = Coupon(
        name="已使用券",
        description="已使用",
        type="amount_off",
        discount_amount=Decimal("2.00"),
        discount_percent=None,
        min_order_amount=Decimal("0.00"),
        scope="all",
        seat_zone=None,
        valid_from=NOW - timedelta(days=1),
        expires_at=NOW + timedelta(days=1),
        is_active=True,
    )
    coupon_zone = Coupon(
        name="VIP专享8折",
        description="仅VIP座位",
        type="percentage_off",
        discount_amount=None,
        discount_percent=80,
        min_order_amount=Decimal("0.00"),
        scope="seat_zone",
        seat_zone="vip",
        valid_from=NOW - timedelta(days=1),
        expires_at=NOW + timedelta(days=1),
        is_active=True,
    )
    db_session.add_all([coupon_active, coupon_expired, coupon_used, coupon_zone])
    await db_session.flush()

    db_session.add_all(
        [
            UserCoupon(user_id=str(USER_ID), coupon_id=coupon_active.id, status="available"),
            UserCoupon(user_id=str(USER_ID), coupon_id=coupon_expired.id, status="available"),
            UserCoupon(user_id=str(USER_ID), coupon_id=coupon_used.id, status="used", used_booking_id=10, used_at=NOW),
            UserCoupon(user_id=str(USER_ID), coupon_id=coupon_zone.id, status="available"),
        ]
    )
    await db_session.flush()

    return {"room": room, "seat": seat}


class TestCouponListAPI:
    @pytest.mark.asyncio
    async def test_requires_auth(self, client: AsyncClient):
        resp = await client.get("/api/v1/coupons")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_status_available_filters_out_used(self, auth_client: AsyncClient, seed_coupon_data):
        resp = await auth_client.get("/api/v1/coupons", params={"status": "available"})
        assert resp.status_code == 200
        data = resp.json()
        assert all(item["status"] == "available" for item in data)
        assert "已使用券" not in [item["name"] for item in data]

    @pytest.mark.asyncio
    async def test_status_expired_includes_dynamic_expired(self, auth_client: AsyncClient, seed_coupon_data):
        resp = await auth_client.get("/api/v1/coupons", params={"status": "expired"})
        assert resp.status_code == 200
        names = [item["name"] for item in resp.json()]
        assert "过期券" in names


class TestAvailableCouponsAPI:
    @pytest.mark.asyncio
    async def test_available_for_booking(self, auth_client: AsyncClient, seed_coupon_data):
        resp = await auth_client.get(
            "/api/v1/coupons/available-for-booking",
            params={
                "seat_id": seed_coupon_data["seat"].id,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["original_price"] == "60.00"
        names = [item["name"] for item in data["items"]]
        assert "满20减3" in names
        assert "VIP专享8折" in names
        assert "已使用券" not in names

    @pytest.mark.asyncio
    async def test_missing_seat_returns_404(self, auth_client: AsyncClient):
        resp = await auth_client.get(
            "/api/v1/coupons/available-for-booking",
            params={
                "seat_id": 99999,
                "date": "2026-05-01",
                "start_time": "09:00",
                "end_time": "12:00",
            },
        )
        assert resp.status_code == 404

