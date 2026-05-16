## 1. Backend Configuration

- [x] 1.1 Update `br-server/app/core/config.py`
  - Add settings: `WECHAT_PAY_ENABLED`, `WECHAT_PAY_APPID`, `WECHAT_PAY_MCHID`, `WECHAT_PAY_API_V3_KEY`, `WECHAT_PAY_PRIVATE_KEY_PATH`, `WECHAT_PAY_CERT_SERIAL_NO`, `WECHAT_PAY_NOTIFY_URL`, `WECHAT_PAY_API_BASE_URL`
  - Default `WECHAT_PAY_ENABLED=false` for local development
  - Do not provide default values for production secrets

- [x] 1.2 Add configuration validation
  - Add a helper/property that returns whether WeChat Pay is usable
  - When `WECHAT_PAY_ENABLED=true`, require AppID, merchant ID, API v3 key, private key path, certificate serial number, and notify URL
  - Ensure validation errors never print raw key material

- [x] 1.3 Document required environment variables
  - Update deployment or environment documentation used by this repo
  - Include sample variable names only, not real secrets

## 2. Backend Data Model and Migration

- [x] 2.1 Extend `WalletTransaction` in `br-server/app/models/wallet.py`
  - Add `payment_provider: String(20), nullable=False, default="wechat"`
  - Add `payment_status: String(20), nullable=False, default="pending"`
  - Add `prepay_id: String(128), nullable=True, index=True`
  - Add `transaction_id: String(64), nullable=True, unique=True, index=True`
  - Add `paid_at: DateTime, nullable=True`
  - Add `notify_payload: JSON/Text, nullable=True` for sanitized callback data
  - Add `notify_processed_at: DateTime, nullable=True`

- [x] 2.2 Create Alembic migration under `br-server/alembic/versions/`
  - Add all new `wallet_transactions` columns
  - Add indexes for `payment_status`, `prepay_id`, and `transaction_id`
  - Preserve existing pending/completed recharge rows by backfilling `payment_provider="wechat"` and `payment_status` from existing `status`
  - Include downgrade that drops the new indexes and columns

- [x] 2.3 Verify migration locally
  - Run: `cd br-server; alembic upgrade head`
  - Run: `cd br-server; alembic downgrade -1`
  - Run: `cd br-server; alembic upgrade head`
  - Expected: all commands complete without schema errors

## 3. Backend Schemas

- [x] 3.1 Update `br-server/app/schemas/wallet.py`
  - Add `PaymentParams` schema with `timeStamp`, `nonceStr`, `package`, `signType`, `paySign`
  - Extend `RechargeResponse` with `payment_provider`, `payment_status`, `payment_params`
  - Add `RechargeOrderResponse` for `GET /api/v1/wallet/recharge/{order_id}`
  - Keep Decimal output compatible with existing wallet responses

- [x] 3.2 Add internal notification schemas
  - Add Pydantic models for decrypted WeChat notification fields used by the service
  - Include `appid`, `mchid`, `out_trade_no`, `transaction_id`, `trade_state`, `success_time`, `amount.total`, `amount.currency`
  - Keep these schemas internal to service/route handling; do not expose raw callback resources to user-facing APIs

## 4. WeChat Pay Client

- [x] 4.1 Create `br-server/app/services/wechat_pay_client.py`
  - Implement `create_jsapi_prepay(openid, out_trade_no, amount_cents, description, notify_url)`
  - Implement `build_jsapi_payment_params(prepay_id)`
  - Implement `query_order(out_trade_no)`
  - Implement `verify_and_decrypt_notify(headers, body)`
  - Use `httpx.AsyncClient` for API calls and existing cryptography dependencies for RSA/AES-GCM operations

- [x] 4.2 Add client-level exceptions
  - `WechatPayConfigError`
  - `WechatPayRequestError`
  - `WechatPaySignatureError`
  - `WechatPayDecryptError`
  - Ensure route/service layers can map them to stable HTTP responses

- [x] 4.3 Add `br-server/tests/test_wechat_pay_client.py`
  - Test JSAPI payment parameter shape
  - Test prepay failure raises `WechatPayRequestError`
  - Test invalid notification signature raises `WechatPaySignatureError`
  - Test decrypt failure raises `WechatPayDecryptError`
  - Run: `cd br-server; pytest tests/test_wechat_pay_client.py -v`

## 5. Wallet Service Integration

- [x] 5.1 Update `WalletService` dependencies in `br-server/app/services/wallet_service.py`
  - Inject a WeChat Pay client or client factory instead of constructing protocol logic inline
  - Keep wallet business decisions in `WalletService`
  - Keep WeChat API signing/decryption in `WechatPayClient`

- [x] 5.2 Update `create_recharge_order`
  - Reject `payment_method="alipay"` with a domain error until Alipay is implemented
  - Validate user exists and promo code remains valid
  - Create pending `WalletTransaction`
  - Call WeChat JSAPI prepay with order amount in cents
  - Store `prepay_id`, `payment_provider="wechat"`, `payment_status="pending"`
  - Return `RechargeResponse` with `payment_params`

- [x] 5.3 Add `get_recharge_order`
  - Query by `order_id` and current `user_id`
  - Return 404-style domain error when missing or owned by another user
  - Return wallet `status`, `payment_status`, amount, bonus, and `balance_after`

- [x] 5.4 Add `handle_wechat_notify`
  - Verify and decrypt the callback through `WechatPayClient`
  - Locate transaction by `out_trade_no` using `SELECT ... FOR UPDATE`
  - Validate `trade_state="SUCCESS"`
  - Validate `appid`, `mchid`, currency, and amount
  - If already completed/paid, return idempotent success without changing balance
  - If pending, atomically update `users.balance`, mark transaction `completed/paid`, save `transaction_id`, `paid_at`, sanitized notify payload, and `notify_processed_at`

- [x] 5.5 Restrict simulated payment confirmation
  - Keep `confirm_payment` only for tests/development when explicitly enabled
  - Production route must not allow client-triggered wallet crediting
  - Update tests that previously used `confirm_payment` to cover callback-driven completion

## 6. Backend Routes

- [x] 6.1 Update `br-server/app/api/routes/wallet.py`
  - `POST /api/v1/wallet/recharge` returns WeChat payment params
  - Add `GET /api/v1/wallet/recharge/{order_id}` with current-user authorization
  - Add `POST /api/v1/wallet/wechat/notify` without user auth, using WeChat signature verification instead

- [x] 6.2 Map domain and payment errors
  - 400 for malformed callback or amount mismatch
  - 401 or 403 for invalid WeChat signature
  - 404 for missing user-facing order
  - 422 for unsupported payment method or invalid promo code
  - 503 for WeChat Pay disabled or misconfigured

- [x] 6.3 Return WeChat-compatible notify responses
  - Success response must match WeChat Pay expected JSON shape
  - Failure response must include a clear failure code/message without leaking secrets

## 7. Backend Tests

- [x] 7.1 Update `br-server/tests/test_wallet_service.py`
  - Test creating a WeChat recharge order returns `payment_params`
  - Test unsupported Alipay raises the expected domain error
  - Test querying own recharge order succeeds
  - Test querying another user's recharge order fails
  - Test successful WeChat callback credits balance once
  - Test duplicate callback does not double credit
  - Test callback amount mismatch does not credit balance
  - Run: `cd br-server; pytest tests/test_wallet_service.py -v`

- [x] 7.2 Add or update wallet API integration tests
  - If no wallet API test file exists, create `br-server/tests/test_api_wallet.py`
  - Test authenticated create recharge order
  - Test unauthenticated create recharge order returns 401
  - Test recharge order detail for owner
  - Test recharge order detail for another user returns 404
  - Test WeChat notify success
  - Test WeChat notify invalid signature
  - Test unsupported payment method returns 422
  - Run: `cd br-server; pytest tests/test_api_wallet.py -v`

- [x] 7.3 Run regression tests
  - Run: `cd br-server; pytest tests/test_wallet_service.py tests/test_api_wallet.py tests/test_api_booking.py -v`
  - Expected: all tests pass

## 8. Frontend API Layer

- [x] 8.1 Update `br-app/src/api/wallet.js`
  - Add `getRechargeOrder(orderId)` using `GET /api/v1/wallet/recharge/{orderId}`
  - Keep `createRechargeOrder(data)` unchanged at call site
  - Stop using `confirmPayment(orderId)` in production recharge flow

## 9. Frontend Recharge Page

- [x] 9.1 Update `br-app/src/pages/recharge/index.vue` submit flow
  - If selected payment method is Alipay, show `暂未开通` and do not call backend
  - Call `createRechargeOrder`
  - Validate response includes `payment_params`
  - Call `uni.requestPayment` with returned params

- [x] 9.2 Add backend status confirmation after payment
  - After `uni.requestPayment` success, poll `getRechargeOrder(orderId)`
  - Stop polling when `status="completed"`
  - Refresh balance only after backend reports completed
  - If polling times out, show `支付处理中，请稍后查看余额`

- [x] 9.3 Improve frontend state handling
  - Separate states for creating order, waiting for WeChat payment, and confirming backend result
  - Prevent repeated taps while any payment state is active
  - On user cancel, show `支付已取消` and keep current balance
  - On payment failure, show `支付失败，请重试` and keep current balance

## 10. API Documentation

- [x] 10.1 Update `docs/api.md`
  - Document changed `POST /api/v1/wallet/recharge` request/response
  - Document `GET /api/v1/wallet/recharge/{order_id}`
  - Document `POST /api/v1/wallet/wechat/notify`
  - Document that wallet crediting only happens after verified WeChat callback

- [x] 10.2 Document operational requirements
  - List required WeChat Pay environment variables
  - Describe callback URL deployment requirement
  - Describe how to disable WeChat Pay safely

## 11. Review and Acceptance

- [x] 11.1 Clean Architecture review
  - Routes only parse inputs and map errors
  - `WechatPayClient` owns vendor protocol details
  - `WalletService` owns wallet state transitions
  - Models remain persistence-only

- [x] 11.2 Security review
  - No secrets committed or logged
  - Callback signature and decrypt failures do not mutate database state
  - Amount, currency, appid, mchid, order ownership, and duplicate callback checks are covered by tests

- [x] 11.3 Manual acceptance
  - In test mode, create a recharge order and verify payment params are returned
  - Simulate a valid WeChat callback and verify balance increases once
  - Simulate duplicate callback and verify balance does not increase again
  - In the mini program, verify payment cancel/failure/processing/success messages
