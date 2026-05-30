from __future__ import annotations

from decimal import Decimal

from sqlalchemy.ext.asyncio import AsyncSession

from app.models.wallet import WalletTransaction


class WalletRepository:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def create_transaction(
        self,
        *,
        user_id: str,
        transaction_type: str,
        amount: Decimal,
        bonus_amount: Decimal,
        order_id: str,
        status: str,
        promo_code_id: int | None = None,
        payment_method: str | None = None,
        booking_id: int | None = None,
    ) -> WalletTransaction:
        transaction = WalletTransaction(
            user_id=user_id,
            type=transaction_type,
            amount=amount,
            bonus_amount=bonus_amount,
            order_id=order_id,
            status=status,
            promo_code_id=promo_code_id,
            payment_method=payment_method,
            booking_id=booking_id,
        )
        self._db.add(transaction)
        await self._db.flush()
        return transaction
