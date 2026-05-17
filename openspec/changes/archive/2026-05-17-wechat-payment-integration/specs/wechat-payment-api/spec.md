## ADDED Requirements

### Requirement: Create WeChat recharge order API
系统 SHALL 在 `POST /api/v1/wallet/recharge` 中支持 `payment_method="wechat"`，创建钱包充值订单并返回微信小程序 JSAPI 支付参数。

#### Scenario: Create WeChat recharge order successfully
- **GIVEN** 用户已登录且微信支付配置可用
- **WHEN** 用户发送 `POST /api/v1/wallet/recharge`，body 为 `{"amount": 100, "payment_method": "wechat"}`
- **THEN** 系统创建 `wallet_transactions` pending 记录
- **AND** 系统调用微信支付 JSAPI 下单获取 `prepay_id`
- **AND** 返回 HTTP 201，响应包含 `order_id`、`amount`、`payment_provider="wechat"`、`payment_status="pending"` 和 `payment_params`

#### Scenario: WeChat Pay is disabled
- **GIVEN** `WECHAT_PAY_ENABLED=false`
- **WHEN** 用户创建微信充值订单
- **THEN** 返回 HTTP 503 或 422
- **AND** 错误信息说明微信支付暂不可用
- **AND** 不应创建可支付的微信预支付订单

#### Scenario: Unsupported payment method
- **GIVEN** 用户已登录
- **WHEN** 用户发送 `payment_method="alipay"` 创建充值订单
- **THEN** 返回 HTTP 422
- **AND** 错误信息说明当前仅支持微信支付

### Requirement: Query recharge order API
系统 SHALL 提供 `GET /api/v1/wallet/recharge/{order_id}`，返回当前用户充值订单的支付状态和入账状态。

#### Scenario: Query own order
- **GIVEN** 用户已登录且拥有一笔充值订单
- **WHEN** 用户请求 `GET /api/v1/wallet/recharge/{order_id}`
- **THEN** 返回 HTTP 200
- **AND** 响应包含 `order_id`、`amount`、`bonus_amount`、`status`、`payment_status`、`balance_after`

#### Scenario: Query another user's order
- **GIVEN** 用户 A 已登录，订单属于用户 B
- **WHEN** 用户 A 请求该 `order_id`
- **THEN** 返回 HTTP 404

### Requirement: WeChat payment notification API
系统 SHALL 提供 `POST /api/v1/wallet/wechat/notify` 处理微信支付 API v3 异步通知，并以通知作为钱包入账的唯一可信依据。

#### Scenario: Process successful payment notification
- **GIVEN** 存在 `payment_status="pending"` 的充值订单
- **WHEN** 微信支付发送签名有效、解密成功、`trade_state="SUCCESS"` 且金额匹配的通知
- **THEN** 系统使用行级锁读取该充值订单
- **AND** 原子增加 `users.balance`
- **AND** 将交易更新为 `status="completed"`、`payment_status="paid"`
- **AND** 保存 `transaction_id`、`paid_at`、`notify_processed_at`
- **AND** 返回微信要求的成功响应

#### Scenario: Duplicate successful notification
- **GIVEN** 一笔充值订单已经 `status="completed"` 且 `payment_status="paid"`
- **WHEN** 微信支付再次发送同一订单的成功通知
- **THEN** 系统返回成功响应
- **AND** 不再次增加用户余额
- **AND** 不创建重复交易流水

#### Scenario: Invalid notification signature
- **WHEN** 通知签名校验失败
- **THEN** 系统拒绝处理通知
- **AND** 不更新订单状态
- **AND** 不增加用户余额

#### Scenario: Notification amount mismatch
- **GIVEN** 本地订单金额为 100.00
- **WHEN** 解密后的微信通知金额不是 100.00
- **THEN** 系统拒绝入账
- **AND** 记录错误日志
- **AND** 订单保持未完成状态

#### Scenario: Payment result comes from client only
- **GIVEN** 小程序 `uni.requestPayment` 返回 success
- **WHEN** 后端尚未收到并验证微信支付成功通知
- **THEN** 系统 SHALL NOT 增加用户余额
- **AND** 订单保持 `pending` 或支付处理中状态

### Requirement: WeChat payment configuration security
系统 SHALL 从环境变量或安全文件路径读取微信支付敏感配置，禁止将商户私钥、API v3 密钥或平台证书内容提交到仓库。

#### Scenario: Missing production secret
- **GIVEN** 运行环境启用微信支付
- **WHEN** 必需的微信支付密钥配置缺失
- **THEN** 应用启动或支付创建时失败并给出明确错误
- **AND** 错误日志不得输出密钥内容
