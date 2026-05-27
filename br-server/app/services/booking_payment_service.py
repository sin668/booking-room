"""Booking direct payment orchestration."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.booking import Booking
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User
from app.schemas.booking import PaymentStatusResponse
from app.services.wechat_pay_client import (
    WechatPayConfigError,
    WechatPayDecryptError,
    WechatPayRequestError,
    WechatPaySignatureError,
)


class BookingPaymentError(ValueError):
    """Base exception for booking payment operations."""

    @property
    def detail(self) -> str:
        return str(self)


class PaymentProviderUnavailableError(BookingPaymentError):
    pass


class WechatOpenIdRequiredError(BookingPaymentError):
    pass


class BookingPaymentNotFoundError(BookingPaymentError):
    pass


class InvalidBookingPaymentCallbackError(BookingPaymentError):
    pass


class BookingPaymentSignatureError(BookingPaymentError):
    pass


class BookingPaymentAlreadyProcessedError(BookingPaymentError):
    pass


class BookingPaymentService:
    """Service for booking WeChat payment creation and callbacks."""

    def __init__(
        self,
        db: AsyncSession,
        *,
        wechat_client: Any | None,
        config=settings,
    ) -> None:
        self._db = db
        self._wechat_client = wechat_client
        self._config = config

    async def create_booking_payment(
        self,
        booking: Booking,
        user: User,
    ) -> dict[str, str]:
        """Create a WeChat JSAPI payment order for a pending booking."""
        if self._wechat_client is None:
            raise PaymentProviderUnavailableError("WeChat Pay is disabled or misconfigured")
        if not getattr(user, "wechat_openid", None):
            raise WechatOpenIdRequiredError("WeChat OpenID is required")

        description = await self._build_description(booking)
        out_trade_no = self._booking_out_trade_no(booking.id)
        notify_url = (
            getattr(self._config, "WECHAT_PAY_BOOKING_NOTIFY_URL", "")
            or getattr(self._config, "WECHAT_PAY_NOTIFY_URL", "")
        )
        try:
            prepay_id = await self._wechat_client.create_jsapi_prepay(
                openid=user.wechat_openid,
                out_trade_no=out_trade_no,
                amount_cents=self._decimal_to_cents(Decimal(str(booking.total_price))),
                description=description,
                notify_url=notify_url,
            )
            payment_params = self._wechat_client.build_jsapi_payment_params(prepay_id)
            if inspect.isawaitable(payment_params):
                payment_params = await payment_params
        except (WechatPayConfigError, WechatPayRequestError) as exc:
            raise PaymentProviderUnavailableError(str(exc)) from exc

        booking.prepay_id = prepay_id
        await self._db.flush()
        return payment_params

    async def process_wechat_notify(
        self,
        *,
        headers: dict[str, str],
        body: bytes,
    ) -> dict[str, str]:
        """Verify a WeChat callback and mark a booking payment as paid once."""
        if self._wechat_client is None:
            raise PaymentProviderUnavailableError("WeChat Pay is disabled or misconfigured")

        try:
            notify = await self._wechat_client.verify_and_decrypt_notify(headers, body)
        except WechatPaySignatureError as exc:
            raise BookingPaymentSignatureError(
                "WeChat Pay callback verification failed"
            ) from exc
        except WechatPayDecryptError as exc:
            raise InvalidBookingPaymentCallbackError(
                "Malformed WeChat Pay callback"
            ) from exc

        if hasattr(notify, "model_dump"):
            notify = notify.model_dump()

        self._validate_notify_payload(notify)
        booking_id = self._parse_booking_out_trade_no(notify["out_trade_no"])
        result = await self._db.execute(
            select(Booking).where(Booking.id == booking_id).with_for_update()
        )
        booking = result.scalar_one_or_none()
        if booking is None:
            raise BookingPaymentNotFoundError("Booking payment not found")

        expected_cents = self._decimal_to_cents(Decimal(str(booking.total_price)))
        paid_cents = int(notify.get("amount", {}).get("total", -1))
        if paid_cents != expected_cents:
            raise InvalidBookingPaymentCallbackError("WeChat Pay amount mismatch")

        if booking.payment_status == "paid":
            return {"code": "SUCCESS", "message": "success"}
        if booking.payment_status != "pending":
            raise BookingPaymentAlreadyProcessedError("Booking payment already processed")

        booking.payment_status = "paid"
        booking.transaction_id = notify.get("transaction_id")
        booking.paid_at = self._parse_wechat_success_time(notify.get("success_time")) or datetime.now()
        await self._db.flush()
        return {"code": "SUCCESS", "message": "success"}

    async def query_payment_status(
        self,
        booking_id: int,
        user_id: uuid.UUID,
    ) -> PaymentStatusResponse:
        result = await self._db.execute(
            select(Booking).where(
                Booking.id == booking_id,
                Booking.user_id == str(user_id),
            )
        )
        booking = result.scalar_one_or_none()
        if booking is None:
            raise BookingPaymentNotFoundError("Booking payment not found")

        return PaymentStatusResponse(
            booking_id=booking.id,
            payment_status=booking.payment_status,
            paid_at=booking.paid_at,
            transaction_id=booking.transaction_id,
        )

    async def _build_description(self, booking: Booking) -> str:
        seat_result = await self._db.execute(select(Seat).where(Seat.id == booking.seat_id))
        seat = seat_result.scalar_one()
        room_result = await self._db.execute(select(StudyRoom).where(StudyRoom.id == booking.room_id))
        room = room_result.scalar_one()
        return (
            f"{room.name} {seat.seat_number} {booking.date.isoformat()} "
            f"{booking.start_time.strftime('%H:%M')}-{booking.end_time.strftime('%H:%M')}"
        )[:127]

    def _validate_notify_payload(self, notify: dict[str, Any]) -> None:
        if notify.get("trade_state") != "SUCCESS":
            raise InvalidBookingPaymentCallbackError("WeChat Pay trade state is not SUCCESS")
        if notify.get("amount", {}).get("currency") != "CNY":
            raise InvalidBookingPaymentCallbackError("WeChat Pay currency mismatch")

        expected_appid = getattr(self._config, "WECHAT_PAY_APPID", "")
        if expected_appid and notify.get("appid") != expected_appid:
            raise InvalidBookingPaymentCallbackError("WeChat Pay appid mismatch")

        expected_mchid = getattr(self._config, "WECHAT_PAY_MCHID", "")
        if expected_mchid and notify.get("mchid") != expected_mchid:
            raise InvalidBookingPaymentCallbackError("WeChat Pay mchid mismatch")

        if not notify.get("out_trade_no") or not notify.get("transaction_id"):
            raise InvalidBookingPaymentCallbackError("WeChat Pay callback missing fields")

    def _parse_booking_out_trade_no(self, value: str) -> int:
        prefix = "BK-"
        if not value.startswith(prefix):
            raise InvalidBookingPaymentCallbackError("Invalid booking payment order")
        try:
            return int(value[len(prefix):])
        except ValueError as exc:
            raise InvalidBookingPaymentCallbackError("Invalid booking payment order") from exc

    def _booking_out_trade_no(self, booking_id: int) -> str:
        return f"BK-{booking_id:03d}"

    def _parse_wechat_success_time(self, value: str | None) -> datetime | None:
        if not value:
            return None
        parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
        return parsed.replace(tzinfo=None)

    def _decimal_to_cents(self, value: Decimal) -> int:
        cents = (value * Decimal("100")).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
        return int(cents)
