"""Unit tests for coupon_service module."""

from datetime import UTC, datetime, timedelta, date, time
from decimal import Decimal
import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.services import coupon_service


USER_ID = str(uuid.UUID("11111111-1111-1111-1111-111111111111"))
OTHER_USER_ID = str(uuid.UUID("22222222-2222-2222-2222-222222222222"))
NOW = datetime.now(UTC)


@pytest.fixture
async def seed_room_and_seats(db_session: AsyncSession):
    room = StudyRoom(name="Test Room", address="123 Test St", status="open", min_price=10.00)
    db_session.add(room)
    await db_session.flush()

    quiet_seat = Seat(
        room_id=room.id,
        seat_number="A-01",
        zone="quiet",
        position="window",
        floor=3,
        price_per_hour=Decimal("15.00"),
        status="available",
        row=1,
        col=1,
    )
    vip_seat = Seat(
        room_id=room.id,
        seat_number="B-01",
        zone="vip",
        position="corner",
        floor=3,
        price_per_hour=Decimal("20.00"),
        status="available",
        row=2,
        col=1,
    )
    db_session.add_all([quiet_seat, vip_seat])
    await db_session.flush()

    return {"room": room, "quiet": quiet_seat, "vip": vip_seat}


@pytest.fixture
async def seed_coupons(db_session: AsyncSession):
    active_coupon = Coupon(
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
    expired_coupon = Coupon(
        name="过期券",
        description="已过期",
        type="amount_off",
        discount_amount=Decimal("5.00"),
        discount_percent=None,
        min_order_amount=Decimal("0.00"),
        scope="all",
        seat_zone=None,
        valid_from=NOW - timedelta(days=5),
        expires_at=NOW - timedelta(hours=1),
        is_active=True,
    )
    first_booking_coupon = Coupon(
        name="首单立减20",
        description="首次预约可用",
        type="amount_off",
        discount_amount=Decimal("20.00"),
        discount_percent=None,
        min_order_amount=Decimal("0.00"),
        scope="first_booking",
        seat_zone=None,
        valid_from=NOW - timedelta(days=1),
        expires_at=NOW + timedelta(days=1),
        is_active=True,
    )
    vip_coupon = Coupon(
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
    used_coupon = Coupon(
        name="已使用券",
        description="已使用",
        type="amount_off",
        discount_amount=Decimal("3.00"),
        discount_percent=None,
        min_order_amount=Decimal("0.00"),
        scope="all",
        seat_zone=None,
        valid_from=NOW - timedelta(days=1),
        expires_at=NOW + timedelta(days=1),
        is_active=True,
    )
    future_coupon = Coupon(
        name="未生效券",
        description="明天生效",
        type="amount_off",
        discount_amount=Decimal("3.00"),
        discount_percent=None,
        min_order_amount=Decimal("0.00"),
        scope="all",
        seat_zone=None,
        valid_from=NOW + timedelta(days=1),
        expires_at=NOW + timedelta(days=2),
        is_active=True,
    )
    inactive_coupon = Coupon(
        name="停用券",
        description="已停用",
        type="amount_off",
        discount_amount=Decimal("3.00"),
        discount_percent=None,
        min_order_amount=Decimal("0.00"),
        scope="all",
        seat_zone=None,
        valid_from=NOW - timedelta(days=1),
        expires_at=NOW + timedelta(days=1),
        is_active=False,
    )
    db_session.add_all(
        [
            active_coupon,
            expired_coupon,
            first_booking_coupon,
            vip_coupon,
            used_coupon,
            future_coupon,
            inactive_coupon,
        ]
    )
    await db_session.flush()

    db_session.add_all(
        [
            UserCoupon(user_id=USER_ID, coupon_id=active_coupon.id, status="available"),
            UserCoupon(user_id=USER_ID, coupon_id=expired_coupon.id, status="available"),
            UserCoupon(user_id=USER_ID, coupon_id=first_booking_coupon.id, status="available"),
            UserCoupon(user_id=USER_ID, coupon_id=vip_coupon.id, status="available"),
            UserCoupon(user_id=USER_ID, coupon_id=used_coupon.id, status="used", used_booking_id=99, used_at=NOW),
            UserCoupon(user_id=USER_ID, coupon_id=future_coupon.id, status="available"),
            UserCoupon(user_id=USER_ID, coupon_id=inactive_coupon.id, status="available"),
            UserCoupon(user_id=OTHER_USER_ID, coupon_id=active_coupon.id, status="available"),
        ]
    )
    await db_session.flush()

    return {
        "active": active_coupon,
        "expired": expired_coupon,
        "first_booking": first_booking_coupon,
        "vip": vip_coupon,
        "used": used_coupon,
        "future": future_coupon,
        "inactive": inactive_coupon,
    }


class TestListUserCoupons:
    @pytest.mark.asyncio
    async def test_filters_current_user_only(self, db_session: AsyncSession, seed_coupons):
        result = await coupon_service.list_user_coupons(db_session, USER_ID)
        assert len(result) == 7
        assert {item.name for item in result} == {
            "满20减3",
            "过期券",
            "首单立减20",
            "VIP专享8折",
            "已使用券",
            "未生效券",
            "停用券",
        }

    @pytest.mark.asyncio
    async def test_filters_available_status(self, db_session: AsyncSession, seed_coupons):
        result = await coupon_service.list_user_coupons(db_session, USER_ID, status="available")
        assert len(result) == 3
        assert {item.status for item in result} == {"available"}
        assert {item.name for item in result} == {"满20减3", "首单立减20", "VIP专享8折"}

    @pytest.mark.asyncio
    async def test_filters_expired_status(self, db_session: AsyncSession, seed_coupons):
        result = await coupon_service.list_user_coupons(db_session, USER_ID, status="expired")
        assert len(result) == 3
        assert {item.name for item in result} == {"过期券", "未生效券", "停用券"}
        assert {item.status for item in result} == {"expired"}


class TestAvailableCouponsForBooking:
    @pytest.mark.asyncio
    async def test_amount_off_threshold_and_first_booking(self, db_session: AsyncSession, seed_room_and_seats, seed_coupons):
        result = await coupon_service.list_available_coupons_for_booking(
            db_session,
            USER_ID,
            seed_room_and_seats["quiet"].id,
            date(2026, 5, 1),
            time(9, 0),
            time(12, 0),
        )
        assert result.original_price == Decimal("45.00")
        names = [item.name for item in result.items]
        assert "满20减3" in names
        assert "首单立减20" in names
        assert "VIP专享8折" not in names

    @pytest.mark.asyncio
    async def test_discount_and_zone_scope(self, db_session: AsyncSession, seed_room_and_seats, seed_coupons):
        db_session.add(
            Booking(
                seat_id=seed_room_and_seats["quiet"].id,
                user_id=USER_ID,
                room_id=seed_room_and_seats["room"].id,
                date=date(2026, 4, 30),
                start_time=time(8, 0),
                end_time=time(10, 0),
                status="confirmed",
                total_price=Decimal("30.00"),
            )
        )
        await db_session.flush()

        result = await coupon_service.list_available_coupons_for_booking(
            db_session,
            USER_ID,
            seed_room_and_seats["vip"].id,
            date(2026, 5, 1),
            time(9, 0),
            time(12, 0),
        )
        vip_item = next(item for item in result.items if item.name == "VIP专享8折")
        assert vip_item.discount_amount == Decimal("12.00")
        assert vip_item.payable_amount == Decimal("48.00")

    @pytest.mark.asyncio
    async def test_threshold_too_low_excluded(self, db_session: AsyncSession, seed_room_and_seats, seed_coupons):
        result = await coupon_service.list_available_coupons_for_booking(
            db_session,
            USER_ID,
            seed_room_and_seats["quiet"].id,
            date(2026, 5, 1),
            time(9, 0),
            time(10, 0),
        )
        assert "满20减3" not in [item.name for item in result.items]

    @pytest.mark.asyncio
    async def test_expired_coupon_excluded(self, db_session: AsyncSession, seed_room_and_seats, seed_coupons):
        result = await coupon_service.list_available_coupons_for_booking(
            db_session,
            USER_ID,
            seed_room_and_seats["quiet"].id,
            date(2026, 5, 1),
            time(9, 0),
            time(12, 0),
        )
        assert "过期券" not in [item.name for item in result.items]

    @pytest.mark.asyncio
    async def test_future_and_inactive_coupons_excluded(self, db_session: AsyncSession, seed_room_and_seats, seed_coupons):
        result = await coupon_service.list_available_coupons_for_booking(
            db_session,
            USER_ID,
            seed_room_and_seats["quiet"].id,
            date(2026, 5, 1),
            time(9, 0),
            time(12, 0),
        )
        names = [item.name for item in result.items]
        assert "未生效券" not in names
        assert "停用券" not in names

    @pytest.mark.asyncio
    async def test_first_booking_excluded_with_history(self, db_session: AsyncSession, seed_room_and_seats, seed_coupons):
        db_session.add(
            Booking(
                seat_id=seed_room_and_seats["quiet"].id,
                user_id=USER_ID,
                room_id=seed_room_and_seats["room"].id,
                date=date(2026, 4, 29),
                start_time=time(8, 0),
                end_time=time(10, 0),
                status="completed",
                total_price=Decimal("30.00"),
            )
        )
        await db_session.flush()

        result = await coupon_service.list_available_coupons_for_booking(
            db_session,
            USER_ID,
            seed_room_and_seats["quiet"].id,
            date(2026, 5, 1),
            time(9, 0),
            time(12, 0),
        )
        assert "首单立减20" not in [item.name for item in result.items]

    @pytest.mark.asyncio
    async def test_available_result_not_include_used_coupon(self, db_session: AsyncSession, seed_room_and_seats, seed_coupons):
        result = await coupon_service.list_available_coupons_for_booking(
            db_session,
            USER_ID,
            seed_room_and_seats["quiet"].id,
            date(2026, 5, 1),
            time(9, 0),
            time(12, 0),
        )
        assert "已使用券" not in [item.name for item in result.items]
