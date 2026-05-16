"""Unit tests for WalletService."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.services.wallet_service import (
    InvalidPaymentCallbackError,
    InvalidPromoCodeError,
    OrderAlreadyProcessedError,
    OrderNotFoundError,
    SimulatedPaymentDisabledError,
    UnsupportedPaymentMethodError,
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
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def mock_redis() -> AsyncMock:
    return AsyncMock()


@pytest.fixture
def wechat_client() -> AsyncMock:
    client = AsyncMock()
    client.create_jsapi_prepay.return_value = "wx-prepay-id"
    client.build_jsapi_payment_params.return_value = {
        "timeStamp": "1710000000",
        "nonceStr": "nonce",
        "package": "prepay_id=wx-prepay-id",
        "signType": "RSA",
        "paySign": "signature",
    }
    return client


@pytest.fixture
def wallet_service(
    mock_db: AsyncMock,
    mock_redis: AsyncMock,
    settings: Settings,
    wechat_client: AsyncMock,
) -> WalletService:
    return WalletService(mock_db, mock_redis, settings, wechat_client=wechat_client)


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
    user = SimpleNamespace(id=user_id, balance=Decimal("256.00"))

    mock_db.execute = AsyncMock(
        side_effect=[
            _mock_scalar_result(user),
            _mock_scalar_one_result(Decimal("1200.00")),
        ]
    )

    result = await wallet_service.get_balance(user_id)

    assert result.balance == Decimal("256.00")
    assert result.total_recharged == Decimal("1200.00")


async def test_create_wechat_recharge_order_returns_payment_params(
    wallet_service: WalletService,
    mock_db: AsyncMock,
    wechat_client: AsyncMock,
) -> None:
    user_id = _test_user_id()
    user = SimpleNamespace(id=user_id, balance=Decimal("256.00"), wechat_openid="openid-1")

    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(user))
    mock_db.flush = AsyncMock()

    result = await wallet_service.create_recharge_order(user_id, 100, "wechat")

    assert result.amount == Decimal("100.00")
    assert result.status == "pending"
    assert result.payment_provider == "wechat"
    assert result.payment_status == "pending"
    assert result.payment_params is not None
    assert result.payment_params.package == "prepay_id=wx-prepay-id"
    wechat_client.create_jsapi_prepay.assert_awaited_once()
    _, kwargs = wechat_client.create_jsapi_prepay.await_args
    assert kwargs["openid"] == "openid-1"
    assert kwargs["amount_cents"] == 10000
    mock_db.add.assert_called_once()
    mock_db.flush.assert_awaited_once()


async def test_create_recharge_order_rejects_unsupported_alipay(
    wallet_service: WalletService,
    mock_db: AsyncMock,
    wechat_client: AsyncMock,
) -> None:
    with pytest.raises(UnsupportedPaymentMethodError):
        await wallet_service.create_recharge_order(_test_user_id(), 100, "alipay")

    mock_db.execute.assert_not_called()
    wechat_client.create_jsapi_prepay.assert_not_called()


async def test_get_recharge_order_for_owner_succeeds(
    wallet_service: WalletService,
    mock_db: AsyncMock,
) -> None:
    user_id = _test_user_id()
    order_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    transaction = SimpleNamespace(
        order_id=str(order_id),
        user_id=str(user_id),
        amount=Decimal("100.00"),
        bonus_amount=Decimal("10.00"),
        status="completed",
        payment_status="paid",
        balance_after=Decimal("366.00"),
    )
    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(transaction))

    result = await wallet_service.get_recharge_order(order_id, user_id)

    assert result.order_id == order_id
    assert result.status == "completed"
    assert result.payment_status == "paid"
    assert result.balance_after == Decimal("366.00")


async def test_get_recharge_order_for_another_user_fails(
    wallet_service: WalletService,
    mock_db: AsyncMock,
) -> None:
    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(None))

    with pytest.raises(OrderNotFoundError):
        await wallet_service.get_recharge_order(
            uuid.UUID("11111111-2222-3333-4444-555555555555"),
            _test_user_id(),
        )


async def test_successful_wechat_callback_credits_balance_once(
    wallet_service: WalletService,
    mock_db: AsyncMock,
    wechat_client: AsyncMock,
) -> None:
    user_id = _test_user_id()
    order_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    transaction = SimpleNamespace(
        order_id=str(order_id),
        user_id=str(user_id),
        status="pending",
        payment_status="pending",
        amount=Decimal("100.00"),
        bonus_amount=Decimal("5.00"),
        balance_after=None,
        transaction_id=None,
        paid_at=None,
        notify_payload=None,
        notify_processed_at=None,
    )
    user = SimpleNamespace(id=user_id, balance=Decimal("200.00"))
    notify = {
        "appid": "",
        "mchid": "",
        "out_trade_no": str(order_id),
        "transaction_id": "wx-txn-1",
        "trade_state": "SUCCESS",
        "success_time": "2026-05-16T10:20:30+08:00",
        "amount": {"total": 10000, "currency": "CNY"},
    }
    wechat_client.verify_and_decrypt_notify.return_value = notify

    async def execute_side_effect(*args, **kwargs):
        call_number = mock_db.execute.await_count
        if call_number == 1:
            return _mock_scalar_result(transaction)
        if call_number == 2:
            assert args[1] == {"amount": Decimal("105.00"), "uid": str(user_id)}
            user.balance += args[1]["amount"]
            return MagicMock()
        return _mock_scalar_one_result(user)

    mock_db.execute = AsyncMock(side_effect=execute_side_effect)

    result = await wallet_service.handle_wechat_notify({"Wechatpay-Signature": "ok"}, b"{}")

    assert result == {"code": "SUCCESS", "message": "success"}
    assert transaction.status == "completed"
    assert transaction.payment_status == "paid"
    assert transaction.transaction_id == "wx-txn-1"
    assert transaction.balance_after == Decimal("305.00")
    assert transaction.paid_at.tzinfo is None
    assert transaction.notify_processed_at.tzinfo is None


async def test_duplicate_wechat_callback_does_not_double_credit(
    wallet_service: WalletService,
    mock_db: AsyncMock,
    wechat_client: AsyncMock,
) -> None:
    order_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    transaction = SimpleNamespace(
        order_id=str(order_id),
        status="completed",
        payment_status="paid",
        amount=Decimal("100.00"),
        bonus_amount=Decimal("0.00"),
        transaction_id="wx-txn-1",
        notify_payload=None,
        notify_processed_at=None,
    )
    wechat_client.verify_and_decrypt_notify.return_value = {
        "appid": "",
        "mchid": "",
        "out_trade_no": str(order_id),
        "transaction_id": "wx-txn-1",
        "trade_state": "SUCCESS",
        "amount": {"total": 10000, "currency": "CNY"},
    }
    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(transaction))

    result = await wallet_service.handle_wechat_notify({}, b"{}")

    assert result == {"code": "SUCCESS", "message": "success"}
    assert mock_db.execute.await_count == 1


async def test_wechat_callback_amount_mismatch_does_not_credit(
    wallet_service: WalletService,
    mock_db: AsyncMock,
    wechat_client: AsyncMock,
) -> None:
    order_id = uuid.UUID("11111111-2222-3333-4444-555555555555")
    transaction = SimpleNamespace(
        order_id=str(order_id),
        status="pending",
        payment_status="pending",
        amount=Decimal("100.00"),
        bonus_amount=Decimal("0.00"),
    )
    wechat_client.verify_and_decrypt_notify.return_value = {
        "appid": "",
        "mchid": "",
        "out_trade_no": str(order_id),
        "transaction_id": "wx-txn-1",
        "trade_state": "SUCCESS",
        "amount": {"total": 1, "currency": "CNY"},
    }
    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(transaction))

    with pytest.raises(InvalidPaymentCallbackError):
        await wallet_service.handle_wechat_notify({}, b"{}")

    assert transaction.status == "pending"
    assert mock_db.execute.await_count == 1


async def test_confirm_payment_disabled_in_production(
    wallet_service: WalletService,
) -> None:
    with pytest.raises(SimulatedPaymentDisabledError):
        await wallet_service.confirm_payment(
            uuid.UUID("11111111-2222-3333-4444-555555555555"),
            _test_user_id(),
        )


async def test_redeem_promo_code_invalid(
    wallet_service: WalletService,
    mock_db: AsyncMock,
) -> None:
    mock_db.execute = AsyncMock(return_value=_mock_scalar_result(None))

    with pytest.raises(InvalidPromoCodeError) as exc_info:
        await wallet_service.redeem_promo_code("INVALID")

    assert exc_info.value.detail == "Invalid promo code"
