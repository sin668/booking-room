from decimal import Decimal

import pytest

from app.repositories.wallet_repository import WalletRepository


@pytest.mark.asyncio
async def test_create_transaction_flushes_wallet_transaction(db_session):
    repository = WalletRepository(db_session)

    transaction = await repository.create_transaction(
        user_id="00000000-0000-0000-0000-000000000001",
        transaction_type="recharge",
        amount=Decimal("12.30"),
        bonus_amount=Decimal("1.00"),
        order_id="00000000-0000-0000-0000-000000000099",
        status="pending",
        promo_code_id=None,
        payment_method="wechat",
    )

    assert transaction.id is not None
    assert transaction.type == "recharge"
    assert transaction.amount == Decimal("12.30")
    assert transaction.bonus_amount == Decimal("1.00")
    assert transaction.order_id == "00000000-0000-0000-0000-000000000099"
