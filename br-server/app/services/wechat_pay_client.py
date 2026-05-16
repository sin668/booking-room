"""WeChat Pay API v3 client for JSAPI wallet recharges."""

from __future__ import annotations

import base64
import json
import secrets
import time
import urllib.parse
from pathlib import Path
from typing import Any

import httpx
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding
from cryptography.hazmat.primitives.ciphers.aead import AESGCM

from app.core.config import Settings
from app.schemas.wallet import WechatDecryptedNotify


class WechatPayConfigError(Exception):
    """Raised when WeChat Pay configuration is disabled or incomplete."""


class WechatPayRequestError(Exception):
    """Raised when a WeChat Pay API request fails."""


class WechatPaySignatureError(Exception):
    """Raised when a WeChat Pay request or notification signature is invalid."""


class WechatPayDecryptError(Exception):
    """Raised when a WeChat Pay notification cannot be decrypted."""


class WechatPayClient:
    """Small API v3 client that owns WeChat Pay protocol details."""

    def __init__(
        self,
        config: Settings,
        *,
        http_timeout: float = 10,
        wechatpay_public_key_pem: str | bytes | None = None,
        skip_signature_verification: bool = False,
    ) -> None:
        self._config = config
        self._http_timeout = http_timeout
        self._private_key = None
        self._wechatpay_public_key = None
        self._wechatpay_public_key_pem = wechatpay_public_key_pem
        self._skip_signature_verification = skip_signature_verification

    async def create_jsapi_prepay(
        self,
        openid: str,
        out_trade_no: str,
        amount_cents: int,
        description: str,
        notify_url: str,
    ) -> str:
        """Create a JSAPI prepay order and return its prepay_id."""
        self._require_usable_config()
        if amount_cents <= 0:
            raise WechatPayRequestError("amount_cents must be greater than zero")

        path = "/v3/pay/transactions/jsapi"
        payload = {
            "appid": self._config.WECHAT_PAY_APPID,
            "mchid": self._config.WECHAT_PAY_MCHID,
            "description": description,
            "out_trade_no": out_trade_no,
            "notify_url": notify_url,
            "amount": {"total": amount_cents, "currency": "CNY"},
            "payer": {"openid": openid},
        }
        body = _json_dumps(payload)
        headers = self._build_authorization_headers("POST", path, body)

        try:
            async with httpx.AsyncClient(
                base_url=self._config.WECHAT_PAY_API_BASE_URL,
                timeout=self._http_timeout,
            ) as client:
                response = await client.post(path, content=body, headers=headers)
        except httpx.HTTPError as exc:
            raise WechatPayRequestError(
                f"WeChat Pay prepay request failed: {exc}"
            ) from exc

        data = _parse_response(response)
        prepay_id = data.get("prepay_id")
        if not prepay_id:
            raise WechatPayRequestError("WeChat Pay prepay response missing prepay_id")
        return str(prepay_id)

    def build_jsapi_payment_params(self, prepay_id: str) -> dict[str, str]:
        """Build mini program payment params for uni.requestPayment."""
        self._require_usable_config()
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        package = f"prepay_id={prepay_id}"
        message = "\n".join(
            [self._config.WECHAT_PAY_APPID, timestamp, nonce, package, ""]
        )
        signature = self._sign(message.encode("utf-8"))
        return {
            "timeStamp": timestamp,
            "nonceStr": nonce,
            "package": package,
            "signType": "RSA",
            "paySign": signature,
        }

    async def query_order(self, out_trade_no: str) -> dict[str, Any]:
        """Query an order by merchant out_trade_no."""
        self._require_usable_config()
        path = f"/v3/pay/transactions/out-trade-no/{urllib.parse.quote(out_trade_no)}"
        query = urllib.parse.urlencode({"mchid": self._config.WECHAT_PAY_MCHID})
        signed_path = f"{path}?{query}"
        headers = self._build_authorization_headers("GET", signed_path, "")

        try:
            async with httpx.AsyncClient(
                base_url=self._config.WECHAT_PAY_API_BASE_URL,
                timeout=self._http_timeout,
            ) as client:
                response = await client.get(
                    path,
                    params={"mchid": self._config.WECHAT_PAY_MCHID},
                    headers=headers,
                )
        except httpx.HTTPError as exc:
            raise WechatPayRequestError(
                f"WeChat Pay query request failed: {exc}"
            ) from exc

        return _parse_response(response)

    async def verify_and_decrypt_notify(
        self,
        headers: dict[str, str],
        body: bytes,
    ) -> WechatDecryptedNotify:
        """Verify notification signature, decrypt resource, and validate fields."""
        self._require_usable_config()
        if not self._skip_signature_verification:
            self._verify_notify_signature(headers, body)

        try:
            payload = json.loads(body.decode("utf-8"))
            resource = payload["resource"]
            associated_data = resource.get("associated_data", "").encode("utf-8")
            nonce = resource["nonce"].encode("utf-8")
            ciphertext = base64.b64decode(resource["ciphertext"])
            api_v3_key = self._config.WECHAT_PAY_API_V3_KEY.encode("utf-8")
            plaintext = AESGCM(api_v3_key).decrypt(
                nonce,
                ciphertext,
                associated_data,
            )
        except Exception as exc:
            raise WechatPayDecryptError(
                "Failed to decrypt WeChat Pay notification"
            ) from exc

        try:
            return WechatDecryptedNotify.model_validate_json(plaintext)
        except Exception as exc:
            raise WechatPayDecryptError(
                "Invalid decrypted WeChat Pay notification"
            ) from exc

    def _require_usable_config(self) -> None:
        try:
            self._config.require_wechat_pay_usable()
        except ValueError as exc:
            raise WechatPayConfigError(str(exc)) from exc

    def _build_authorization_headers(
        self,
        method: str,
        canonical_url: str,
        body: str,
    ) -> dict[str, str]:
        timestamp = str(int(time.time()))
        nonce = secrets.token_urlsafe(16)
        message = "\n".join([method.upper(), canonical_url, timestamp, nonce, body, ""])
        signature = self._sign(message.encode("utf-8"))
        token = (
            'mchid="{mchid}",nonce_str="{nonce}",timestamp="{timestamp}",'
            'serial_no="{serial}",signature="{signature}"'
        ).format(
            mchid=self._config.WECHAT_PAY_MCHID,
            nonce=nonce,
            timestamp=timestamp,
            serial=self._config.WECHAT_PAY_CERT_SERIAL_NO,
            signature=signature,
        )
        return {
            "Accept": "application/json",
            "Content-Type": "application/json",
            "Authorization": f"WECHATPAY2-SHA256-RSA2048 {token}",
        }

    def _sign(self, message: bytes) -> str:
        signature = self._load_private_key().sign(
            message,
            padding.PKCS1v15(),
            hashes.SHA256(),
        )
        return base64.b64encode(signature).decode("utf-8")

    def _load_private_key(self):
        if self._private_key is not None:
            return self._private_key

        private_key_path = Path(self._config.WECHAT_PAY_PRIVATE_KEY_PATH)
        try:
            private_key_bytes = private_key_path.read_bytes()
            self._private_key = serialization.load_pem_private_key(
                private_key_bytes,
                password=None,
            )
        except Exception as exc:
            raise WechatPayConfigError(
                "Invalid WeChat Pay private key configuration"
            ) from exc
        return self._private_key

    def _verify_notify_signature(self, headers: dict[str, str], body: bytes) -> None:
        public_key = self._load_wechatpay_public_key()
        normalized_headers = {key.lower(): value for key, value in headers.items()}
        try:
            timestamp = normalized_headers["wechatpay-timestamp"]
            nonce = normalized_headers["wechatpay-nonce"]
            serial = normalized_headers["wechatpay-serial"]
            signature = base64.b64decode(normalized_headers["wechatpay-signature"])
        except Exception as exc:
            raise WechatPaySignatureError(
                "Missing or malformed WeChat Pay signature headers"
            ) from exc

        expected_serial = self._config.WECHAT_PAY_PLATFORM_CERT_SERIAL_NO
        if expected_serial and serial != expected_serial:
            raise WechatPaySignatureError("Unexpected WeChat Pay platform serial")

        try:
            timestamp_int = int(timestamp)
        except ValueError as exc:
            raise WechatPaySignatureError("Invalid WeChat Pay timestamp") from exc
        if abs(int(time.time()) - timestamp_int) > 300:
            raise WechatPaySignatureError("Expired WeChat Pay notification timestamp")

        message = b"\n".join(
            [timestamp.encode("utf-8"), nonce.encode("utf-8"), body, b""]
        )
        try:
            public_key.verify(
                signature,
                message,
                padding.PKCS1v15(),
                hashes.SHA256(),
            )
        except InvalidSignature as exc:
            raise WechatPaySignatureError(
                "Invalid WeChat Pay notification signature"
            ) from exc
        except Exception as exc:
            raise WechatPaySignatureError(
                "Unable to verify WeChat Pay notification signature"
            ) from exc

    def _load_wechatpay_public_key(self):
        if self._wechatpay_public_key is not None:
            return self._wechatpay_public_key

        if not self._wechatpay_public_key_pem:
            public_key_path = self._config.WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH
            if not public_key_path:
                raise WechatPaySignatureError("WeChat Pay platform public key unavailable")
            try:
                self._wechatpay_public_key_pem = Path(public_key_path).read_bytes()
            except Exception as exc:
                raise WechatPaySignatureError("WeChat Pay platform public key unavailable") from exc
        try:
            public_key_pem = self._wechatpay_public_key_pem
            if isinstance(public_key_pem, str):
                public_key_pem = public_key_pem.encode("utf-8")
            self._wechatpay_public_key = serialization.load_pem_public_key(public_key_pem)
            return self._wechatpay_public_key
        except Exception as exc:
            raise WechatPaySignatureError(
                "Invalid WeChat Pay platform public key"
            ) from exc


def _json_dumps(data: dict[str, Any]) -> str:
    return json.dumps(data, ensure_ascii=False, separators=(",", ":"))


def _parse_response(response: httpx.Response) -> dict[str, Any]:
    try:
        data = response.json()
    except Exception as exc:
        raise WechatPayRequestError("WeChat Pay returned a non-JSON response") from exc

    if 200 <= response.status_code < 300:
        if isinstance(data, dict):
            return data
        raise WechatPayRequestError("WeChat Pay returned an invalid JSON response")

    code = data.get("code", "UNKNOWN") if isinstance(data, dict) else "UNKNOWN"
    message = (
        data.get("message", response.text) if isinstance(data, dict) else response.text
    )
    raise WechatPayRequestError(f"WeChat Pay API error [{code}] {message}")
