"""Wallet recharge and balance management service."""

import uuid
from datetime import datetime
from decimal import Decimal

from sqlalchemy import func, select, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.coupon import Coupon
from app.models.user import User
from app.models.wallet import WalletTransaction
from app.schemas.wallet import (
    BalanceResponse,
    PromoCodeResponse,
    RechargeResponse,
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


class WalletService:
    def __init__(self, db: AsyncSession, redis, config: Settings) -> None:
        self._db = db
        self._redis = redis
        self._config = config

    async def get_balance(self, user_id: uuid.UUID) -> BalanceResponse:
        """Get user's current balance and total recharged amount."""
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError("用户不存在")

        # Sum completed recharge transactions
        total_stmt = (
            select(func.coalesce(func.sum(WalletTransaction.amount), 0))
            .where(
                WalletTransaction.user_id == str(user_id),
                WalletTransaction.type == "recharge",
                WalletTransaction.status == "completed",
            )
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
        """Create a pending recharge order."""
        # Validate user exists
        stmt = select(User).where(User.id == user_id)
        result = await self._db.execute(stmt)
        user = result.scalar_one_or_none()
        if not user:
            raise UserNotFoundError("用户不存在")

        bonus_amount = Decimal("0")
        promo_code_id = None

        # Validate promo code if provided
        if promo_code:
            bonus_amount, promo_code_id = await self._validate_promo_code(
                promo_code, amount
            )

        # Create pending transaction
        transaction = WalletTransaction(
            user_id=str(user_id),
            type="recharge",
            amount=Decimal(str(amount)),
            bonus_amount=bonus_amount,
            order_id=str(uuid.uuid4()),
            status="pending",
            promo_code_id=promo_code_id,
            payment_method=payment_method,
        )
        self._db.add(transaction)
        await self._db.flush()

        return RechargeResponse(
            order_id=uuid.UUID(transaction.order_id),
            amount=transaction.amount,
            bonus_amount=transaction.bonus_amount,
            status=transaction.status,
        )

    async def confirm_payment(
        self, order_id: uuid.UUID, user_id: uuid.UUID
    ) -> RechargeResponse:
        """Confirm payment and credit balance atomically."""
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
            raise OrderNotFoundError("订单不存在")
        if transaction.status != "pending":
            raise OrderAlreadyProcessedError("订单已处理")

        total = transaction.amount + transaction.bonus_amount
        user_id_text = transaction.user_id

        # Atomic balance update
        await self._db.execute(
            text("UPDATE users SET balance = balance + :amount WHERE id = :uid"),
            {"amount": total, "uid": user_id_text},
        )

        # Get updated balance
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

        # Fetch coupon description for the response
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
        """Validate promo code and return (bonus_amount, coupon_id).

        Raises InvalidPromoCodeError if invalid.
        """
        stmt = select(Coupon).where(
            Coupon.name == code,
            Coupon.is_active == True,
        )
        result = await self._db.execute(stmt)
        coupon = result.scalar_one_or_none()
        if not coupon:
            raise InvalidPromoCodeError("优惠码无效")

        now = datetime.now()  # naive datetime per BUG-15: no tzinfo for DB comparisons
        if coupon.expires_at < now:
            raise InvalidPromoCodeError("优惠码已过期")

        bonus = coupon.discount_amount if coupon.discount_amount else Decimal("0")

        if min_amount is not None and coupon.min_order_amount:
            if float(min_amount) < float(coupon.min_order_amount):
                raise InvalidPromoCodeError(
                    f"优惠码要求最低充值{coupon.min_order_amount}元"
                )

        return bonus, coupon.id
