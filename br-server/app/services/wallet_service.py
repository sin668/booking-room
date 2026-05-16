"""Wallet recharge and balance management service."""

from __future__ import annotations

import inspect
import uuid
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
from typing import Any

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.coupon import Coupon
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.wallet import (
    BalanceResponse,
    PromoCodeResponse,
    RechargeOrderResponse,
    RechargeResponse,
)
from app.services.wechat_pay_client import (
    WechatPayConfigError,
    WechatPayDecryptError,
    WechatPayRequestError,
    WechatPaySignatureError,
)


class WalletServiceError(Exception):
    """Base exception for wallet service domain errors."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
        super().__init__(detail)


class UserNotFoundError(WalletServiceError):
    pass


class OrderNotFoundError(WalletServiceError):
    pass


class OrderAlreadyProcessedError(WalletServiceError):
    pass


class InvalidPromoCodeError(WalletServiceError):
    pass


class UnsupportedPaymentMethodError(WalletServiceError):
    pass


class PaymentProviderUnavailableError(WalletServiceError):
    pass


class InvalidPaymentCallbackError(WalletServiceError):
    pass


class PaymentSignatureError(WalletServiceError):
    pass


class SimulatedPaymentDisabledError(WalletServiceError):
    pass


class WechatOpenIdRequiredError(WalletServiceError):
    pass


class WalletService:
    def __init__(
        self,
        db: AsyncSession,
        redis,
        config: Settings,
        wechat_client: Any | None = None,
    ) -> None:
        self._db = db
        self._redis = redis
        self._config = config
        self._wechat_client = wechat_client

    async def get_balance(self, user_id: uuid.UUID) -> BalanceResponse:
        """Get user's current balance and total recharged amount."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError("User not found")

        total_stmt = select(func.coalesce(func.sum(WalletTransaction.amount), 0)).where(
            WalletTransaction.user_id == str(user_id),
            WalletTransaction.type == "recharge",
            WalletTransaction.status == "completed",
        )
        total_result = await self._db.execute(total_stmt)
        total_recharged = total_result.scalar_one()

        return BalanceResponse(
            balance=user.balance,
            total_recharged=Decimal(str(total_recharged)),
        )

    async def create_recharge_order(
        self,
        user_id: uuid.UUID,
        amount: float,
        payment_method: str,
        promo_code: str | None = None,
    ) -> RechargeResponse:
        """Create a pending WeChat JSAPI recharge order."""
        if payment_method == "alipay":
            raise UnsupportedPaymentMethodError("Alipay is not implemented")
        if payment_method != "wechat":
            raise UnsupportedPaymentMethodError("Unsupported payment method")
        if self._wechat_client is None:
            raise PaymentProviderUnavailableError(
                "WeChat Pay is disabled or misconfigured"
            )

        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError("User not found")
        if not getattr(user, "wechat_openid", None):
            raise WechatOpenIdRequiredError("WeChat OpenID is required")

        bonus_amount = Decimal("0")
        promo_code_id = None
        if promo_code:
            bonus_amount, promo_code_id = await self._validate_promo_code(
                promo_code, amount
            )

        transaction = WalletTransaction(
            user_id=str(user_id),
            type="recharge",
            amount=Decimal(str(amount)).quantize(Decimal("0.01")),
            bonus_amount=bonus_amount,
            order_id=str(uuid.uuid4()),
            status="pending",
            promo_code_id=promo_code_id,
            payment_method=payment_method,
        )
        self._set_payment_attr(transaction, "payment_provider", "wechat")
        self._set_payment_attr(transaction, "payment_status", "pending")
        self._db.add(transaction)
        await self._db.flush()

        try:
            prepay_id = await self._wechat_client.create_jsapi_prepay(
                openid=user.wechat_openid,
                out_trade_no=transaction.order_id,
                amount_cents=self._decimal_to_cents(transaction.amount),
                description="Wallet recharge",
                notify_url=getattr(self._config, "WECHAT_PAY_NOTIFY_URL", ""),
            )
            payment_params = self._wechat_client.build_jsapi_payment_params(prepay_id)
        except (WechatPayConfigError, WechatPayRequestError) as exc:
            raise PaymentProviderUnavailableError(str(exc)) from exc
        if inspect.isawaitable(payment_params):
            payment_params = await payment_params

        self._set_payment_attr(transaction, "prepay_id", prepay_id)

        return self._transaction_payload(
            transaction,
            payment_provider="wechat",
            payment_status="pending",
            payment_params=payment_params,
        )

    async def get_recharge_order(
        self,
        order_id: uuid.UUID,
        user_id: uuid.UUID,
    ) -> RechargeOrderResponse:
        """Return a user-owned recharge order."""
        stmt = select(WalletTransaction).where(
            WalletTransaction.order_id == str(order_id),
            WalletTransaction.user_id == str(user_id),
        )
        result = await self._db.execute(stmt)
        transaction = result.scalar_one_or_none()
        if not transaction:
            raise OrderNotFoundError("Order not found")

        return self._transaction_payload(transaction)

    async def handle_wechat_notify(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> dict[str, str]:
        """Verify a WeChat Pay callback and credit the wallet exactly once."""
        if self._wechat_client is None:
            raise PaymentProviderUnavailableError(
                "WeChat Pay is disabled or misconfigured"
            )

        try:
            notify = await self._wechat_client.verify_and_decrypt_notify(headers, body)
        except WechatPaySignatureError as exc:
            raise PaymentSignatureError("WeChat Pay callback verification failed") from exc
        except WechatPayDecryptError as exc:
            raise InvalidPaymentCallbackError("Malformed WeChat Pay callback") from exc

        if hasattr(notify, "model_dump"):
            notify = notify.model_dump()

        self._validate_notify_payload(notify)
        order_id = notify["out_trade_no"]

        stmt = (
            select(WalletTransaction)
            .where(WalletTransaction.order_id == order_id)
            .with_for_update()
        )
        result = await self._db.execute(stmt)
        transaction = result.scalar_one_or_none()
        if not transaction:
            raise OrderNotFoundError("Order not found")

        expected_cents = self._decimal_to_cents(transaction.amount)
        paid_cents = int(notify.get("amount", {}).get("total", -1))
        if paid_cents != expected_cents:
            raise InvalidPaymentCallbackError("WeChat Pay amount mismatch")

        payment_status = getattr(transaction, "payment_status", None)
        if transaction.status == "completed" or payment_status == "paid":
            self._set_payment_attr(transaction, "notify_payload", self._sanitize_notify(notify))
            self._set_payment_attr(transaction, "notify_processed_at", datetime.now())
            return {"code": "SUCCESS", "message": "success"}

        if transaction.status != "pending":
            raise OrderAlreadyProcessedError("Order already processed")

        total = Decimal(str(transaction.amount)) + Decimal(str(transaction.bonus_amount))
        await self._db.execute(
            text("UPDATE users SET balance = balance + :amount WHERE id = :uid"),
            {"amount": total, "uid": transaction.user_id},
        )

        user_stmt = select(User).where(User.id == uuid.UUID(transaction.user_id))
        user_result = await self._db.execute(user_stmt)
        user = user_result.scalar_one()

        paid_at = self._parse_wechat_success_time(notify.get("success_time"))
        now = datetime.now()
        transaction.status = "completed"
        transaction.balance_after = user.balance
        self._set_payment_attr(transaction, "payment_status", "paid")
        self._set_payment_attr(transaction, "transaction_id", notify.get("transaction_id"))
        self._set_payment_attr(transaction, "paid_at", paid_at or now)
        self._set_payment_attr(transaction, "notify_payload", self._sanitize_notify(notify))
        self._set_payment_attr(transaction, "notify_processed_at", now)

        return {"code": "SUCCESS", "message": "success"}

    async def confirm_payment(
        self, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> RechargeResponse:
        """Simulate payment confirmation when explicitly enabled for tests/dev."""
        if not getattr(self._config, "WALLET_SIMULATED_CONFIRM_ENABLED", False):
            raise SimulatedPaymentDisabledError("Simulated payment is disabled")

        stmt = (
            select(WalletTransaction)
            .where(
                WalletTransaction.order_id == str(order_id),
                WalletTransaction.user_id == str(user_id),
            )
            .with_for_update()
        )
        result = await self._db.execute(stmt)
        transaction = result.scalar_one_or_none()
        if not transaction:
            raise OrderNotFoundError("Order not found")
        if transaction.status != "pending":
            raise OrderAlreadyProcessedError("Order already processed")

        total = transaction.amount + transaction.bonus_amount
        await self._db.execute(
            text("UPDATE users SET balance = balance + :amount WHERE id = :uid"),
            {"amount": total, "uid": transaction.user_id},
        )

        user_stmt = select(User).where(User.id == user_id)
        user_result = await self._db.execute(user_stmt)
        user = user_result.scalar_one()

        transaction.status = "completed"
        transaction.balance_after = user.balance

        return RechargeResponse(
            order_id=uuid.UUID(transaction.order_id),
            amount=transaction.amount,
            bonus_amount=transaction.bonus_amount,
            status=transaction.status,
            balance_after=transaction.balance_after,
        )

    async def redeem_promo_code(self, code: str) -> PromoCodeResponse:
        """Validate and return promo code details."""
        bonus_amount, coupon_id = await self._validate_promo_code(code)

        stmt = select(Coupon).where(Coupon.id == coupon_id)
        result = await self._db.execute(stmt)
        coupon = result.scalar_one()
        return PromoCodeResponse(
            code=code,
            description=coupon.description or "",
            bonus_amount=bonus_amount,
        )

    async def _validate_promo_code(
        self, code: str, min_amount: float | None = None
    ) -> tuple[Decimal, int | None]:
        """Validate promo code and return bonus amount and coupon ID."""
        stmt = select(Coupon).where(
            Coupon.name == code,
            Coupon.is_active == True,
        )
        result = await self._db.execute(stmt)
        coupon = result.scalar_one_or_none()
        if not coupon:
            raise InvalidPromoCodeError("Invalid promo code")

        now = datetime.now()
        if coupon.expires_at < now:
            raise InvalidPromoCodeError("Promo code expired")

        bonus = coupon.discount_amount if coupon.discount_amount else Decimal("0")

        if min_amount is not None and coupon.min_order_amount:
            if float(min_amount) < float(coupon.min_order_amount):
                raise InvalidPromoCodeError(
                    f"Promo code requires minimum recharge {coupon.min_order_amount}"
                )

        return bonus, coupon.id

    def _transaction_payload(
        self,
        transaction: WalletTransaction,
        **overrides: Any,
    ) -> RechargeResponse | RechargeOrderResponse:
        payment_status = overrides.pop(
            "payment_status",
            getattr(transaction, "payment_status", transaction.status),
        )
        payment_provider = overrides.pop(
            "payment_provider",
            getattr(transaction, "payment_provider", "wechat"),
        )
        payload = {
            "order_id": uuid.UUID(transaction.order_id),
            "amount": Decimal(str(transaction.amount)),
            "bonus_amount": Decimal(str(transaction.bonus_amount)),
            "status": transaction.status,
            "payment_provider": payment_provider,
            "payment_status": payment_status,
            "balance_after": (
                Decimal(str(transaction.balance_after))
                if getattr(transaction, "balance_after", None) is not None
                else None
            ),
        }
        payload.update(overrides)
        if "payment_params" in payload:
            return RechargeResponse.model_validate(payload)
        return RechargeOrderResponse.model_validate(payload)

    def _validate_notify_payload(self, notify: dict[str, Any]) -> None:
        if notify.get("trade_state") != "SUCCESS":
            raise InvalidPaymentCallbackError("WeChat Pay trade state is not SUCCESS")
        if notify.get("amount", {}).get("currency") != "CNY":
            raise InvalidPaymentCallbackError("WeChat Pay currency mismatch")

        expected_appid = getattr(self._config, "WECHAT_PAY_APPID", "")
        if expected_appid and notify.get("appid") != expected_appid:
            raise InvalidPaymentCallbackError("WeChat Pay appid mismatch")

        expected_mchid = getattr(self._config, "WECHAT_PAY_MCHID", "")
        if expected_mchid and notify.get("mchid") != expected_mchid:
            raise InvalidPaymentCallbackError("WeChat Pay mchid mismatch")

        if not notify.get("out_trade_no") or not notify.get("transaction_id"):
            raise InvalidPaymentCallbackError("WeChat Pay callback missing fields")

    def _sanitize_notify(self, notify: dict[str, Any]) -> dict[str, Any]:
        return {
            "appid": notify.get("appid"),
            "mchid": notify.get("mchid"),
            "out_trade_no": notify.get("out_trade_no"),
            "transaction_id": notify.get("transaction_id"),
            "trade_state": notify.get("trade_state"),
            "success_time": notify.get("success_time"),
            "amount": notify.get("amount"),
        }

    def _parse_wechat_success_time(self, value: str | None) -> datetime | None:
        if not value:
            return None
        normalized = value.replace("Z", "+00:00")
        parsed = datetime.fromisoformat(normalized)
        return parsed.replace(tzinfo=None)

    def _decimal_to_cents(self, value: Decimal) -> int:
        cents = (Decimal(str(value)) * Decimal("100")).quantize(
            Decimal("1"),
            rounding=ROUND_HALF_UP,
        )
        return int(cents)

    def _set_payment_attr(
        self,
        transaction: WalletTransaction,
        name: str,
        value: Any,
    ) -> None:
        setattr(transaction, name, value)
