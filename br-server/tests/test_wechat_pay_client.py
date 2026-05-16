"""Offline tests for the WeChat Pay API v3 client."""

from __future__ import annotations

import base64
import json
import time
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding, rsa

from app.core.config import Settings
from app.services.wechat_pay_client import (
    WechatPayClient,
    WechatPayDecryptError,
    WechatPayRequestError,
    WechatPaySignatureError,
)


@pytest.fixture
def private_key_path(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    path = tmp_path / "apiclient_key.pem"
    path.write_bytes(
        key.private_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PrivateFormat.PKCS8,
            encryption_algorithm=serialization.NoEncryption(),
        )
    )
    return path


@pytest.fixture
def platform_key_pair(tmp_path):
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    public_key_path = tmp_path / "wechatpay_public_key.pem"
    public_key_path.write_bytes(
        key.public_key().public_bytes(
            encoding=serialization.Encoding.PEM,
            format=serialization.PublicFormat.SubjectPublicKeyInfo,
        )
    )
    return key, public_key_path


@pytest.fixture
def settings(private_key_path, platform_key_pair) -> Settings:
    _, public_key_path = platform_key_pair
    return Settings(
        WECHAT_PAY_ENABLED=True,
        WECHAT_PAY_APPID="wx-test-appid",
        WECHAT_PAY_MCHID="1900000001",
        WECHAT_PAY_API_V3_KEY="a" * 32,
        WECHAT_PAY_PRIVATE_KEY_PATH=str(private_key_path),
        WECHAT_PAY_CERT_SERIAL_NO="serial-no",
        WECHAT_PAY_PLATFORM_CERT_SERIAL_NO="platform-serial",
        WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH=str(public_key_path),
        WECHAT_PAY_NOTIFY_URL="https://example.com/api/v1/wallet/wechat/notify",
    )


def test_build_jsapi_payment_params_shape(settings: Settings) -> None:
    client = WechatPayClient(settings)

    params = client.build_jsapi_payment_params("wx-prepay-id")

    assert params["timeStamp"].isdigit()
    assert params["nonceStr"]
    assert params["package"] == "prepay_id=wx-prepay-id"
    assert params["signType"] == "RSA"
    assert isinstance(params["paySign"], str)
    assert len(params["paySign"]) > 0


@pytest.mark.asyncio
async def test_create_jsapi_prepay_failure_raises_request_error(
    settings: Settings,
) -> None:
    client = WechatPayClient(settings)
    response = MagicMock()
    response.status_code = 400
    response.text = '{"code":"INVALID_REQUEST"}'
    response.json.return_value = {"code": "INVALID_REQUEST", "message": "bad request"}

    with patch("app.services.wechat_pay_client.httpx.AsyncClient") as mock_client_cls:
        mock_client = AsyncMock()
        mock_client.__aenter__ = AsyncMock(return_value=mock_client)
        mock_client.__aexit__ = AsyncMock(return_value=False)
        mock_client.post = AsyncMock(return_value=response)
        mock_client_cls.return_value = mock_client

        with pytest.raises(WechatPayRequestError) as exc_info:
            await client.create_jsapi_prepay(
                openid="openid-1",
                out_trade_no="order-1",
                amount_cents=100,
                description="Wallet recharge",
                notify_url="https://example.com/notify",
            )

    assert "INVALID_REQUEST" in str(exc_info.value)
    assert "a" * 32 not in str(exc_info.value)


@pytest.mark.asyncio
async def test_invalid_notification_signature_raises_signature_error(
    settings: Settings,
) -> None:
    client = WechatPayClient(settings)
    headers = {
        "Wechatpay-Timestamp": str(int(time.time())),
        "Wechatpay-Nonce": "nonce",
        "Wechatpay-Signature": base64.b64encode(b"invalid").decode("utf-8"),
        "Wechatpay-Serial": "platform-serial",
    }

    with pytest.raises(WechatPaySignatureError):
        await client.verify_and_decrypt_notify(headers, b'{"resource":{}}')


@pytest.mark.asyncio
async def test_expired_notification_timestamp_raises_signature_error(
    settings: Settings,
    platform_key_pair,
) -> None:
    private_key, _ = platform_key_pair
    client = WechatPayClient(settings)
    body = b'{"resource":{}}'
    timestamp = str(int(time.time()) - 301)
    nonce = "nonce"
    message = b"\n".join([timestamp.encode("utf-8"), nonce.encode("utf-8"), body, b""])
    signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    headers = {
        "Wechatpay-Timestamp": timestamp,
        "Wechatpay-Nonce": nonce,
        "Wechatpay-Signature": base64.b64encode(signature).decode("utf-8"),
        "Wechatpay-Serial": "platform-serial",
    }

    with pytest.raises(WechatPaySignatureError):
        await client.verify_and_decrypt_notify(headers, body)


@pytest.mark.asyncio
async def test_unexpected_platform_serial_raises_signature_error(
    settings: Settings,
    platform_key_pair,
) -> None:
    private_key, _ = platform_key_pair
    client = WechatPayClient(settings)
    body = b'{"resource":{}}'
    timestamp = str(int(time.time()))
    nonce = "nonce"
    message = b"\n".join([timestamp.encode("utf-8"), nonce.encode("utf-8"), body, b""])
    signature = private_key.sign(message, padding.PKCS1v15(), hashes.SHA256())
    headers = {
        "Wechatpay-Timestamp": timestamp,
        "Wechatpay-Nonce": nonce,
        "Wechatpay-Signature": base64.b64encode(signature).decode("utf-8"),
        "Wechatpay-Serial": "other-serial",
    }

    with pytest.raises(WechatPaySignatureError):
        await client.verify_and_decrypt_notify(headers, body)


@pytest.mark.asyncio
async def test_decrypt_failure_raises_decrypt_error(settings: Settings) -> None:
    client = WechatPayClient(settings, skip_signature_verification=True)
    body = {
        "resource": {
            "associated_data": "transaction",
            "nonce": "nonce-value",
            "ciphertext": "not-valid-base64",
        }
    }

    with pytest.raises(WechatPayDecryptError):
        await client.verify_and_decrypt_notify({}, json.dumps(body).encode("utf-8"))
