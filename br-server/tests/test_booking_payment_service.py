"""Tests for booking WeChat payment service."""

import uuid
from datetime import date, time
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.services.booking_payment_service import (
    BookingPaymentService,
    InvalidBookingPaymentCallbackError,
    PaymentProviderUnavailableError,
)

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
PAY_CONFIG = SimpleNamespace(WECHAT_PAY_APPID="appid", WECHAT_PAY_MCHID="mchid")


@pytest.fixture
async def booking_payment_seed(db_session: AsyncSession):
    room = StudyRoom(name="Alpha Room", address="123 Test St", status="open", min_price=10)
    db_session.add(room)
    await db_session.flush()

    seat = Seat(
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
    user = User(
        id=USER_ID,
        phone="18800000001",
        nickname="WeChat User",
        password_hash="hash",
        balance=Decimal("100.00"),
        wechat_openid="openid-123",
    )
    db_session.add_all([seat, user])
    await db_session.flush()

    booking = Booking(
        seat_id=seat.id,
        user_id=str(USER_ID),
        room_id=room.id,
        date=date(2026, 5, 1),
        start_time=time(9, 0),
        end_time=time(12, 0),
        status="confirmed",
        original_price=Decimal("45.00"),
        discount_amount=Decimal("0.00"),
        total_price=Decimal("45.00"),
        payment_method="wechat",
        payment_status="pending",
        payment_provider="wechat",
    )
    db_session.add(booking)
    await db_session.flush()
    return SimpleNamespace(room=room, seat=seat, user=user, booking=booking)


@pytest.mark.asyncio
async def test_create_booking_payment_sets_prepay_and_returns_params(
    db_session: AsyncSession,
    booking_payment_seed,
):
    wechat_client = Mock()
    wechat_client.create_jsapi_prepay = AsyncMock(return_value="prepay-123")
    wechat_client.build_jsapi_payment_params.return_value = {
        "timeStamp": "1",
        "nonceStr": "nonce",
        "package": "prepay_id=prepay-123",
        "signType": "RSA",
        "paySign": "sig",
    }
    service = BookingPaymentService(
        db_session,
        wechat_client=wechat_client,
        config=PAY_CONFIG,
    )

    params = await service.create_booking_payment(
        booking_payment_seed.booking,
        booking_payment_seed.user,
    )

    assert params["package"] == "prepay_id=prepay-123"
    assert booking_payment_seed.booking.prepay_id == "prepay-123"
    wechat_client.create_jsapi_prepay.assert_awaited_once()
    call = wechat_client.create_jsapi_prepay.await_args.kwargs
    assert call["openid"] == "openid-123"
    assert call["out_trade_no"] == f"BK-{booking_payment_seed.booking.id}"
    assert call["amount_cents"] == 4500
    assert "Alpha Room" in call["description"]
    assert "A-01" in call["description"]


@pytest.mark.asyncio
async def test_create_booking_payment_without_client_raises_unavailable(
    db_session: AsyncSession,
    booking_payment_seed,
):
    service = BookingPaymentService(db_session, wechat_client=None, config=PAY_CONFIG)

    with pytest.raises(PaymentProviderUnavailableError):
        await service.create_booking_payment(
            booking_payment_seed.booking,
            booking_payment_seed.user,
        )


@pytest.mark.asyncio
async def test_process_wechat_notify_marks_booking_paid(
    db_session: AsyncSession,
    booking_payment_seed,
):
    wechat_client = AsyncMock()
    wechat_client.verify_and_decrypt_notify.return_value = {
        "appid": "appid",
        "mchid": "mchid",
        "out_trade_no": f"BK-{booking_payment_seed.booking.id}",
        "transaction_id": "txn-123",
        "trade_state": "SUCCESS",
        "success_time": "2026-05-01T01:02:03+08:00",
        "amount": {"total": 4500, "currency": "CNY"},
    }
    service = BookingPaymentService(
        db_session,
        wechat_client=wechat_client,
        config=PAY_CONFIG,
    )

    result = await service.process_wechat_notify(headers={}, body=b"{}")

    assert result == {"code": "SUCCESS", "message": "success"}
    assert booking_payment_seed.booking.payment_status == "paid"
    assert booking_payment_seed.booking.transaction_id == "txn-123"
    assert booking_payment_seed.booking.paid_at is not None
    assert booking_payment_seed.booking.paid_at.tzinfo is None


@pytest.mark.asyncio
async def test_process_wechat_notify_duplicate_paid_is_idempotent(
    db_session: AsyncSession,
    booking_payment_seed,
):
    booking_payment_seed.booking.payment_status = "paid"
    booking_payment_seed.booking.transaction_id = "txn-existing"
    await db_session.flush()
    wechat_client = AsyncMock()
    wechat_client.verify_and_decrypt_notify.return_value = {
        "appid": "appid",
        "mchid": "mchid",
        "out_trade_no": f"BK-{booking_payment_seed.booking.id}",
        "transaction_id": "txn-duplicate",
        "trade_state": "SUCCESS",
        "success_time": "2026-05-01T01:02:03+08:00",
        "amount": {"total": 4500, "currency": "CNY"},
    }
    service = BookingPaymentService(
        db_session,
        wechat_client=wechat_client,
        config=PAY_CONFIG,
    )

    result = await service.process_wechat_notify(headers={}, body=b"{}")

    assert result == {"code": "SUCCESS", "message": "success"}
    assert booking_payment_seed.booking.transaction_id == "txn-existing"


@pytest.mark.asyncio
async def test_process_wechat_notify_amount_mismatch_rejected(
    db_session: AsyncSession,
    booking_payment_seed,
):
    wechat_client = AsyncMock()
    wechat_client.verify_and_decrypt_notify.return_value = {
        "appid": "appid",
        "mchid": "mchid",
        "out_trade_no": f"BK-{booking_payment_seed.booking.id}",
        "transaction_id": "txn-123",
        "trade_state": "SUCCESS",
        "success_time": "2026-05-01T01:02:03+08:00",
        "amount": {"total": 1, "currency": "CNY"},
    }
    service = BookingPaymentService(
        db_session,
        wechat_client=wechat_client,
        config=PAY_CONFIG,
    )

    with pytest.raises(InvalidBookingPaymentCallbackError):
        await service.process_wechat_notify(headers={}, body=b"{}")

    assert booking_payment_seed.booking.payment_status == "pending"
