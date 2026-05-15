## ADDED Requirements

### Requirement: Create recharge order API
系统 SHALL 提供 `POST /api/wallet/recharge` 端点，接收金额、支付方式、优惠码（可选），创建充值订单并返回订单信息。

#### Scenario: Create order with preset amount
- **WHEN** 已认证用户发送 `POST /api/wallet/recharge`，body 为 `{"amount": 100, "payment_method": "wechat"}`
- **THEN** 返回 201，包含 `{"order_id": "uuid", "amount": 100, "status": "pending", "balance_after": null}`

#### Scenario: Create order with promo code
- **WHEN** 用户发送充值请求携带有效 `promo_code`
- **THEN** 返回 201，`bonus_amount` 字段反映优惠金额（如充100送30则 bonus_amount=30）

#### Scenario: Create order with invalid promo code
- **WHEN** 用户发送充值请求携带无效 `promo_code`
- **THEN** 返回 422，错误信息为"优惠码无效或已使用"

#### Scenario: Unauthenticated request
- **WHEN** 未携带有效 token 的请求访问该端点
- **THEN** 返回 401

### Requirement: Confirm payment API
系统 SHALL 提供 `POST /api/wallet/recharge/{order_id}/confirm` 端点，模拟支付确认，更新余额。

#### Scenario: Confirm payment successfully
- **WHEN** 用户发送确认支付请求，订单状态为 pending
- **THEN** 返回 200，`users.balance` 原子增加订单金额+优惠金额，订单状态变为 completed，创建 wallet_transaction 记录

#### Scenario: Confirm already completed order
- **WHEN** 用户对已完成的订单发送确认请求
- **THEN** 返回 409，错误信息为"订单已处理"

### Requirement: Query balance API
系统 SHALL 提供 `GET /api/wallet/balance` 端点，返回当前用户余额和累计充值信息。

#### Scenario: Query existing balance
- **WHEN** 已认证用户请求 `GET /api/wallet/balance`
- **THEN** 返回 200，包含 `{"balance": "256.00", "total_recharged": "1200.00"}`

### Requirement: Redeem promo code API
系统 SHALL 提供 `POST /api/wallet/promo-code` 端点，校验并兑换优惠码。

#### Scenario: Redeem valid promo code
- **WHEN** 用户发送 `POST /api/wallet/promo-code`，body 为 `{"code": "SAVE30"}`
- **THEN** 返回 200，包含优惠码信息 `{"code": "SAVE30", "description": "充值100送30", "bonus_amount": 30}`

#### Scenario: Redeem expired or used promo code
- **WHEN** 用户发送已使用或已过期的优惠码
- **THEN** 返回 422

### Requirement: Wallet data model
系统 SHALL 在 `users` 表新增 `balance` 字段，新建 `wallet_transactions` 表记录交易流水。

#### Scenario: Balance atomic update
- **WHEN** 支付确认时更新余额
- **THEN** 使用 SQL 原子操作 `UPDATE users SET balance = balance + :amount`，避免并发问题

#### Scenario: Transaction record creation
- **WHEN** 充值完成
- **THEN** `wallet_transactions` 表新增一条记录，包含 user_id、type(recharge)、amount、bonus_amount、balance_after、promo_code_id、created_at
