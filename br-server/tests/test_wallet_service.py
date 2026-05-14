"""Unit tests for WalletService."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.wallet_service import (
    InvalidPromoCodeError,
    OrderAlreadyProcessedError,
    WalletService,
)


@pytest.fixture
def settings() -> Settings:
    return Settings(
        JWT_SECRET_KEY="test-secret-key-for-wallet-tests",
        JWT_ALGORITHM="HS256",
    )


@pytest.fixture
def mock_db() -> AsyncMock:
    session = AsyncMock(spec=AsyncSession)
    return session


@pytest.fixture
def mock_redis() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def wallet_service(
    mock_db: AsyncMock, mock_redis: AsyncMock, settings: Settings
) -> WalletService:
    return WalletService(mock_db, mock_redis, settings)


def _mock_scalar_result(value):
    result = MagicMock()
    result.scalar_one_or_none.return_value = value
    return result


def _mock_scalar_one_result(value):
    result = MagicMock()
    result.scalar_one.return_value = value
    return result


def _test_user_id() -> uuid.UUID:
    return uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


async def test_get_balance(
    wallet_service: WalletService, mock_db: AsyncMock
) -> None:
    user_id = _test_user_id()
    user = MagicMock()
    user.id = user_id
    user.balance = Decimal("256.00")

    mock_db.execute = AsyncMock(
        side_effect=[
            _mock_scalar_result(user),
            _mock_scalar_one_result(Decimal("1200.00")),
        ]
    )

    result = await wallet_service.get_balance(user_id)

    assert result.balance == Decimal("256.00")
    assert result.total_recharged == Decimal("1200.00")


async def test_create_recharge_order(
    wallet_service: WalletService, mock_db: AsyncMock
) -> None:
    user_id = _test_user_id()
    user = MagicMock()
    user.id = user_id
    user.balance = Decimal("256.00")

    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(user))
    mock_db.flush = AsyncMock()

    result = await wallet_service.create_recharge_order(user_id, 100, "wechat")

    assert result.amount == Decimal("100")
    assert result.status == "pending"
    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()


async def test_confirm_payment(
    wallet_service: WalletService, mock_db: AsyncMock
) -> None:
    user_id = _test_user_id()
    order_id = uuid.UUID("11111111-2222-3333-4444-555555555555")

    transaction = MagicMock()
    transaction.order_id = str(order_id)
    transaction.user_id = str(user_id)
    transaction.status = "pending"
    transaction.amount = Decimal("100.00")
    transaction.bonus_amount = Decimal("0")
    transaction.balance_after = None

    user = MagicMock()
    user.id = user_id
    user.balance = Decimal("256.00")

    async def execute_side_effect(*args, **kwargs):
        call_number = mock_db.execute.await_count
        if call_number == 1:
            return _mock_scalar_result(transaction)
        if call_number == 2:
            assert kwargs == {}
            assert args[1] == {"amount": Decimal("100.00"), "uid": str(user_id)}
            user.balance += args[1]["amount"]
            return MagicMock()
        return _mock_scalar_one_result(user)

    mock_db.execute = AsyncMock(side_effect=execute_side_effect)

    result = await wallet_service.confirm_payment(order_id, user_id)

    assert result.status == "completed"
    assert result.balance_after == Decimal("356.00")
    assert transaction.status == "completed"
    assert transaction.balance_after == Decimal("356.00")


async def test_confirm_payment_already_completed(
    wallet_service: WalletService, mock_db: AsyncMock
) -> None:
    user_id = _test_user_id()
    order_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    transaction = MagicMock()
    transaction.order_id = str(order_id)
    transaction.user_id = str(user_id)
    transaction.status = "completed"

    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(transaction))

    with pytest.raises(OrderAlreadyProcessedError) as exc_info:
        await wallet_service.confirm_payment(order_id, user_id)

    assert exc_info.value.detail == "订单已处理"
    mock_db.execute.assert_awaited_once()


async def test_confirm_payment_failed_order_rejected_without_balance_update(
    wallet_service: WalletService, mock_db: AsyncMock
) -> None:
    user_id = _test_user_id()
    order_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    transaction = MagicMock()
    transaction.order_id = str(order_id)
    transaction.user_id = str(user_id)
    transaction.status = "failed"

    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(transaction))

    with pytest.raises(OrderAlreadyProcessedError) as exc_info:
        await wallet_service.confirm_payment(order_id, user_id)

    assert exc_info.value.detail == "订单已处理"
    mock_db.execute.assert_awaited_once()


async def test_redeem_promo_code_invalid(
    wallet_service: WalletService, mock_db: AsyncMock
) -> None:
    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(None))

    with pytest.raises(InvalidPromoCodeError) as exc_info:
        await wallet_service.redeem_promo_code("INVALID")

    assert "优惠码无效" in exc_info.value.detail
