"""Integration tests for wallet API routes."""

from __future__ import annotations

import uuid
from decimal import Decimal
from unittest.mock import AsyncMock

import pytest
from httpx import AsyncClient

from app.api.dependencies import get_current_user_id
from app.main import app
from app.services.wallet_service import (
    OrderNotFoundError,
    PaymentSignatureError,
    UnsupportedPaymentMethodError,
)


USER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")
OTHER_USER_ID = uuid.UUID("22222222-3333-4444-5555-666666666666")
ORDER_ID = uuid.UUID("aaaaaaaa-bbbb-cccc-dddd-eeeeeeeeeeee")


@pytest.fixture
async def auth_client(client: AsyncClient):
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def other_auth_client(client: AsyncClient):
    app.dependency_overrides[get_current_user_id] = lambda: OTHER_USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
def wallet_service(monkeypatch):
    service = AsyncMock()
    monkeypatch.setattr("app.api.routes.wallet._service", lambda db, redis: service)
    return service


async def test_authenticated_create_recharge_order(
    auth_client: AsyncClient,
    wallet_service: AsyncMock,
) -> None:
    wallet_service.create_recharge_order.return_value = {
        "order_id": ORDER_ID,
        "amount": Decimal("100.00"),
        "bonus_amount": Decimal("0.00"),
        "status": "pending",
        "payment_provider": "wechat",
        "payment_status": "pending",
        "payment_params": {
            "timeStamp": "1710000000",
            "nonceStr": "nonce",
            "package": "prepay_id=wx-prepay-id",
            "signType": "RSA",
            "paySign": "signature",
        },
    }

    response = await auth_client.post(
        "/api/v1/wallet/recharge",
        json={"amount": 100, "payment_method": "wechat"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["order_id"] == str(ORDER_ID)
    assert data["payment_status"] == "pending"
    assert data["payment_params"]["package"] == "prepay_id=wx-prepay-id"
    wallet_service.create_recharge_order.assert_awaited_once_with(
        user_id=USER_ID,
        amount=100.0,
        payment_method="wechat",
        promo_code=None,
    )


async def test_unauthenticated_create_recharge_order_returns_401(
    client: AsyncClient,
) -> None:
    app.dependency_overrides.pop(get_current_user_id, None)

    response = await client.post(
        "/api/v1/wallet/recharge",
        json={"amount": 100, "payment_method": "wechat"},
    )

    assert response.status_code == 401


async def test_recharge_order_detail_for_owner(
    auth_client: AsyncClient,
    wallet_service: AsyncMock,
) -> None:
    wallet_service.get_recharge_order.return_value = {
        "order_id": ORDER_ID,
        "amount": Decimal("100.00"),
        "bonus_amount": Decimal("0.00"),
        "status": "completed",
        "payment_provider": "wechat",
        "payment_status": "paid",
        "balance_after": Decimal("300.00"),
    }

    response = await auth_client.get(f"/api/v1/wallet/recharge/{ORDER_ID}")

    assert response.status_code == 200
    assert response.json()["payment_status"] == "paid"
    wallet_service.get_recharge_order.assert_awaited_once_with(
        order_id=ORDER_ID,
        user_id=USER_ID,
    )


async def test_recharge_order_detail_for_another_user_returns_404(
    other_auth_client: AsyncClient,
    wallet_service: AsyncMock,
) -> None:
    wallet_service.get_recharge_order.side_effect = OrderNotFoundError("Order not found")

    response = await other_auth_client.get(f"/api/v1/wallet/recharge/{ORDER_ID}")

    assert response.status_code == 404


async def test_wechat_notify_success(
    client: AsyncClient,
    wallet_service: AsyncMock,
) -> None:
    wallet_service.handle_wechat_notify.return_value = {
        "code": "SUCCESS",
        "message": "success",
    }

    response = await client.post(
        "/api/v1/wallet/wechat/notify",
        content=b"{}",
        headers={"Wechatpay-Signature": "valid"},
    )

    assert response.status_code == 200
    assert response.json() == {"code": "SUCCESS", "message": "success"}
    wallet_service.handle_wechat_notify.assert_awaited_once()


async def test_wechat_notify_invalid_signature(
    client: AsyncClient,
    wallet_service: AsyncMock,
) -> None:
    wallet_service.handle_wechat_notify.side_effect = PaymentSignatureError(
        "WeChat Pay callback verification failed"
    )

    response = await client.post(
        "/api/v1/wallet/wechat/notify",
        content=b"{}",
        headers={"Wechatpay-Signature": "invalid"},
    )

    assert response.status_code == 401
    assert response.json() == {
        "code": "FAIL",
        "message": "WeChat Pay callback verification failed",
    }


async def test_unsupported_payment_method_returns_422(
    auth_client: AsyncClient,
    wallet_service: AsyncMock,
) -> None:
    wallet_service.create_recharge_order.side_effect = UnsupportedPaymentMethodError(
        "Alipay is not implemented"
    )

    response = await auth_client.post(
        "/api/v1/wallet/recharge",
        json={"amount": 100, "payment_method": "alipay"},
    )

    assert response.status_code == 422
