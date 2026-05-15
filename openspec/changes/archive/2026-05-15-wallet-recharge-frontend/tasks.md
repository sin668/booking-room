## 1. Backend Data Model

- [x] 1.1 Add `balance` field to `User` model
  - File: `br-server/app/models/user.py`
  - Add `balance: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=0, nullable=False)` after existing fields
  - Import `Numeric` and `Decimal` from sqlalchemy/decimal

- [x] 1.2 Create `WalletTransaction` model
  - File: `br-server/app/models/wallet.py` (new)
  - Follow `br-server/app/models/coupon.py` pattern: SQLAlchemy 2.0 `Mapped` types, UUID primary key, `func.now()` timestamps
  - Fields: `id` (UUID PK), `user_id` (String(36), indexed), `type` (String(20): "recharge"), `amount` (Numeric(10,2)), `bonus_amount` (Numeric(10,2), default=0), `balance_after` (Numeric(10,2)), `order_id` (String(36), unique, indexed), `status` (String(20): "pending"/"completed"/"failed"), `promo_code_id` (Integer, nullable, FK→coupons.id), `payment_method` (String(20)), `created_at` (DateTime)
  - Add composite index on `(user_id, type)` and index on `order_id`

- [x] 1.3 Register model in `br-server/app/models/__init__.py`
  - Add `from app.models.wallet import WalletTransaction` to imports

- [x] 1.4 Create Alembic migration
  - Run: `cd br-server && alembic revision --autogenerate -m "add_wallet_balance_and_transactions"`
  - Verify generated migration in `br-server/alembic/versions/` adds `balance` column to `users` and creates `wallet_transactions` table
  - Run: `cd br-server && alembic upgrade head`
  - Verify: migration applies cleanly

## 2. Backend Schemas

- [x] 2.1 Create wallet schemas
  - File: `br-server/app/schemas/wallet.py` (new)
  - Follow `br-server/app/schemas/user.py` pattern: Pydantic V2, `Field()` validation, `ConfigDict(from_attributes=True)`
  - Schemas to define:
    - `RechargeRequest(BaseModel)`: `amount: float = Field(gt=0, le=9999)`, `payment_method: str = Field(pattern="^(wechat|alipay)$")`, `promo_code: str | None = None`
    - `RechargeResponse(BaseModel)`: `order_id: UUID`, `amount: Decimal`, `bonus_amount: Decimal = 0`, `status: str`, `balance_after: Decimal | None = None`
    - `BalanceResponse(BaseModel)`: `balance: Decimal`, `total_recharged: Decimal`
    - `PromoCodeRequest(BaseModel)`: `code: str = Field(min_length=1)`
    - `PromoCodeResponse(BaseModel)`: `code: str`, `description: str`, `bonus_amount: Decimal`

## 3. Backend Service

- [x] 3.1 Create `WalletService` skeleton
  - File: `br-server/app/services/wallet_service.py` (new)
  - Follow `br-server/app/services/auth_service.py` constructor pattern:
    ```python
    class WalletService:
        def __init__(self, db: AsyncSession, redis, config: Settings) -> None:
            self._db = db
            self._redis = redis
            self._config = config
    ```

- [x] 3.2 Implement `get_balance(user_id: UUID) -> BalanceResponse`
  - Query `User` by id, return `balance` and sum of completed `WalletTransaction.amount`
  - Use: `stmt = select(User).where(User.id == user_id)`

- [x] 3.3 Implement `create_recharge_order(user_id, amount, payment_method, promo_code?) -> RechargeResponse`
  - If promo_code provided: validate against `Coupon` table (exists, `is_active=True`, not expired, scope contains "recharge")
  - Create `WalletTransaction` with status="pending"
  - Flush to DB to get the generated order_id
  - Return `RechargeResponse` with status="pending"

- [x] 3.4 Implement `confirm_payment(order_id: UUID) -> RechargeResponse`
  - Query `WalletTransaction` by `order_id`, validate status=="pending"
  - Calculate total credit: `amount + bonus_amount`
  - Atomic balance update: `await self._db.execute(text("UPDATE users SET balance = balance + :amount WHERE id = :uid"), {"amount": total, "uid": user_id})`
  - Update transaction: `status="completed"`, `balance_after = old_balance + total`
  - Commit and return updated `RechargeResponse`
  - Raise `HTTPException(409)` if order already completed

- [x] 3.5 Implement `redeem_promo_code(user_id, code) -> PromoCodeResponse`
  - Validate coupon: exists, active, not expired, type matches recharge scope
  - Return `PromoCodeResponse` with description and bonus_amount

## 4. Backend Routes

- [x] 4.1 Create wallet routes
  - File: `br-server/app/api/routes/wallet.py` (new)
  - Follow `br-server/app/api/routes/coupon.py` pattern: `APIRouter` with prefix, tags, `Depends(get_current_user_id)`
  - Endpoints:
    - `POST /recharge` → `RechargeResponse`, depends: `get_db`, `get_redis`, `get_current_user_id`
    - `POST /recharge/{order_id}/confirm` → `RechargeResponse`, same deps
    - `GET /balance` → `BalanceResponse`, same deps
    - `POST /promo-code` → `PromoCodeResponse`, same deps
  - Each handler: instantiate `WalletService(db, redis, settings)`, call service method, return response

- [x] 4.2 Register wallet router in `br-server/app/main.py`
  - Add import: `from app.api.routes.wallet import router as wallet_router`
  - Add: `app.include_router(wallet_router)` after existing `include_router` calls (~line 75)
  - Router prefix and tags defined in wallet.py itself (follow existing pattern)

## 5. Backend Tests — Unit

- [x] 5.1 Create unit test file skeleton
  - File: `br-server/tests/test_wallet_service.py` (new)
  - Follow `br-server/tests/test_auth_service.py` fixture pattern:
    - `@pytest.fixture settings()` with test JWT secret
    - `@pytest.fixture mock_db()` using `AsyncMock(spec=AsyncSession)`
    - `@pytest.fixture mock_redis()` using `AsyncMock()`
    - `@pytest.fixture wallet_service(mock_db, mock_redis, settings)` returning `WalletService(...)`

- [x] 5.2 Write `test_get_balance` test
  - Mock `self._db.execute` to return a User with balance=256.00
  - Mock wallet_transactions aggregate to return total_recharged=1200.00
  - Assert returns `BalanceResponse(balance=256.00, total_recharged=1200.00)`
  - Run: `cd br-server && pytest tests/test_wallet_service.py::test_get_balance -v`

- [x] 5.3 Write `test_create_recharge_order` test
  - Mock DB execute/flush, call `create_recharge_order(user_id, 100, "wechat")`
  - Assert returns `RechargeResponse` with amount=100, status="pending"
  - Run: `cd br-server && pytest tests/test_wallet_service.py::test_create_recharge_order -v`

- [x] 5.4 Write `test_confirm_payment` test
  - Setup: mock pending transaction in DB, mock user with balance=256.00
  - Call `confirm_payment(order_id)`, assert balance updated to 356.00, status="completed"
  - Run: `cd br-server && pytest tests/test_wallet_service.py::test_confirm_payment -v`

- [x] 5.5 Write `test_confirm_payment_already_completed` test
  - Setup: mock transaction with status="completed"
  - Assert raises `HTTPException(409)`
  - Run: `cd br-server && pytest tests/test_wallet_service.py::test_confirm_payment_already_completed -v`

- [x] 5.6 Write `test_redeem_promo_code_invalid` test
  - Mock coupon query to return None
  - Assert raises `HTTPException(422)` with "优惠码无效"
  - Run: `cd br-server && pytest tests/test_wallet_service.py::test_redeem_promo_code_invalid -v`

## 6. Backend Tests — Integration

- [x] 6.1 Create integration test file skeleton
  - File: `br-server/tests/test_api_wallet.py` (new)
  - Follow `br-server/tests/test_api_auth.py` pattern: use `httpx.AsyncClient` with test app, create auth tokens with `_create_access_token(user_id)`

- [x] 6.2 Write `test_get_balance` integration test
  - Create test user, get auth token, `GET /api/v1/wallet/balance`
  - Assert 200 with `{"balance": "0.00", "total_recharged": "0.00"}`
  - Run: `cd br-server && pytest tests/test_api_wallet.py::test_get_balance -v`

- [x] 6.3 Write `test_create_recharge_order` integration test
  - `POST /api/v1/wallet/recharge {"amount": 100, "payment_method": "wechat"}`
  - Assert 201 with order_id and status="pending"
  - Run: `cd br-server && pytest tests/test_api_wallet.py::test_create_recharge_order -v`

- [x] 6.4 Write `test_create_recharge_invalid_amount` integration test
  - `POST /api/v1/wallet/recharge {"amount": -1, "payment_method": "wechat"}`
  - Assert 422 validation error
  - Run: `cd br-server && pytest tests/test_api_wallet.py::test_create_recharge_invalid_amount -v`

- [x] 6.5 Write `test_confirm_payment` integration test
  - Create order via POST, then `POST /api/v1/wallet/recharge/{order_id}/confirm`
  - Assert 200, balance updated, status="completed"
  - Run: `cd br-server && pytest tests/test_api_wallet.py::test_confirm_payment -v`

- [x] 6.6 Write `test_unauthenticated_access` integration test
  - Call all 4 endpoints without token
  - Assert all return 401
  - Run: `cd br-server && pytest tests/test_api_wallet.py::test_unauthenticated_access -v`

- [x] 6.7 Run full test suite
  - Run: `cd br-server && pytest tests/test_wallet_service.py tests/test_api_wallet.py -v`
  - Verify all pass, check no regressions

## 7. Frontend API Layer

- [x] 7.1 Create wallet API module
  - File: `br-app/src/api/wallet.js` (new)
  - Follow `br-app/src/api/auth.js` pattern:
    ```javascript
    import { get, post } from '@/utils/request'

    export function getBalance() {
      return get('/api/v1/wallet/balance')
    }

    export function createRechargeOrder(data) {
      return post('/api/v1/wallet/recharge', data)
    }

    export function confirmPayment(orderId) {
      return post(`/api/v1/wallet/recharge/${orderId}/confirm`)
    }

    export function redeemPromoCode(code) {
      return post('/api/v1/wallet/promo-code', { code })
    }
    ```

## 8. Frontend Recharge Page

- [x] 8.1 Create recharge page shell
  - File: `br-app/src/pages/recharge/index.vue` (new)
  - Follow existing page pattern (Options API, `<template>`/`<script>`/`<style lang="scss">`)
  - Navigation bar: 使用 `uni.navigateTo` 的默认导航栏（pages.json 配置 `navigationBarTitleText: "钱包充值"`）
  - `<script>` data(): `balance`, `totalRecharged`, `selectedAmount(50)`, `paymentMethod('wechat')`, `promoCode('')`, `promoInfo(null)`, `loading(false)`, `submitting(false)`
  - `onLoad()` 调用 `loadBalance()`

- [x] 8.2 Implement balance card section
  - Match `prototype/recharge.html` lines 44-49: gradient card (`bg-gradient-to-r from-primary to-purple-600 rounded-2xl p-5 text-white`)
  - Display `balance` 和 `totalRecharged`，loading 时显示 skeleton
  - Call `getBalance()` API in `loadBalance()`

- [x] 8.3 Implement amount selection grid
  - Match `prototype/recharge.html` lines 51-74: `grid grid-cols-3 gap-3`
  - Data: `amounts: [30, 50, 100, 200, 500]` + 自定义选项
  - `selectAmount(amount)`: 重置所有按钮样式，高亮选中项，同步底部按钮文字
  - 默认选中 ¥50

- [x] 8.4 Implement custom amount input
  - 点击"自定义"时: `uni.showModal` 或 inline input 弹出
  - 输入验证: `1 ≤ amount ≤ 9999`，非整数/超范围提示错误
  - 确认后设置 `selectedAmount` 为自定义值

- [x] 8.5 Implement payment method selector
  - Match `prototype/recharge.html` lines 77-101: 白色圆角卡片内两个选项
  - 微信支付: green icon (`fab fa-weixin`)，默认选中（蓝色圆点）
  - 支付宝: blue icon (`fab fa-alipay`)，未选中
  - 点击切换: `togglePayment(method)`

- [x] 8.6 Implement promo code input
  - Match `prototype/recharge.html` lines 104-111: 白色圆角卡片，icon + input + 兑换按钮
  - `redeemPromoCode()` 调用 API，成功时 `promoInfo` 存储优惠信息，页面显示"充X送Y"
  - 失败时 `uni.showToast({ title: '优惠码无效', icon: 'none' })`

- [x] 8.7 Implement recharge submit
  - Match `prototype/recharge.html` lines 113-118: fixed bottom button (`position: fixed`)
  - `handleRecharge()`:
    1. `submitting = true`，按钮 disabled
    2. 调用 `createRechargeOrder({ amount: selectedAmount, payment_method: paymentMethod, promo_code: promoCode || undefined })`
    3. 成功后立即调用 `confirmPayment(order_id)`
    4. 成功: `uni.showToast({ title: '充值成功' })`, 重新 `loadBalance()`
    5. 失败: `uni.showToast({ title: '充值失败，请重试', icon: 'none' })`
    6. finally: `submitting = false`

- [x] 8.8 Add SCSS styles
  - 使用 `uni.scss` 变量: `$primary`, `$primary-light`, `$bg-color`, `$text-primary`, `$text-secondary`, `$text-muted`
  - 关键样式: `.balance-card` 渐变背景, `.amount-grid` 3列布局, `.amount-btn` 选中态边框, `.payment-item` flex 布局, `.recharge-btn` fixed bottom
  - 参考 `prototype/recharge.html` 的 Tailwind 类名转换为 SCSS

## 9. Frontend Routing

- [x] 9.1 Register recharge route in `br-app/src/pages.json`
  - Add to `pages` array:
    ```json
    {
      "path": "pages/recharge/index",
      "style": {
        "navigationBarTitleText": "钱包充值"
      }
    }
    ```
  - Profile 页面已有导航到此路径的代码，无需修改

## 10. Code Review & Documentation

- [x] 10.1 Review all new code for Clean Architecture compliance
  - Service layer 无 HTTP 依赖（不导入 Request/Response）
  - Routes 层薄：只做参数校验和调用 service
  - Models 纯数据，无业务逻辑
  - Frontend API 层只做请求封装，无业务逻辑

- [x] 10.2 Update API documentation
  - File: `docs/api.md`
  - Add 4 new endpoints under Wallet section:
    - `POST /api/v1/wallet/recharge` — request/response schemas
    - `POST /api/v1/wallet/recharge/{order_id}/confirm` — request/response
    - `GET /api/v1/wallet/balance` — response schema
    - `POST /api/v1/wallet/promo-code` — request/response
  - Follow existing docs/api.md format
