## MODIFIED Requirements

### Requirement: Booking payment with balance
系统 SHALL 在用户选择"账户余额"时，使用现有余额扣款逻辑创建预约，行为与改造前一致。此逻辑同时适用于自习室座位预约和课程预约订单。

#### Scenario: Pay with sufficient balance
- **GIVEN** 用户选择"账户余额"且余额充足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建预约并扣除余额
- **AND** 预约 `payment_method='balance'`、`payment_status='paid'`
- **AND** 显示预约成功弹窗

#### Scenario: Pay with insufficient balance
- **GIVEN** 用户选择"账户余额"且余额不足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统返回余额不足错误
- **AND** 显示"余额不足，请切换微信支付或先充值"提示

#### Scenario: Pay course booking with balance
- **GIVEN** 用户在课程预约页面选择"账户余额"且余额充足
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建课程预约 booking 记录并扣除余额
- **AND** 预约 `booking_type='course'`、`payment_method='balance'`、`payment_status='paid'`
- **AND** 显示课程预约成功弹窗

### Requirement: Booking payment with WeChat Pay
系统 SHALL 在用户选择"微信支付"时，创建 pending 状态的预约并返回微信 JSAPI 支付参数。此逻辑同时适用于自习室座位预约和课程预约订单。

#### Scenario: Create booking with WeChat payment
- **GIVEN** 用户选择"微信支付"且微信支付配置可用
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建预约，`payment_method='wechat'`、`payment_status='pending'`
- **AND** 系统调用微信支付 JSAPI 下单获取 `prepay_id`
- **AND** 返回 201，响应包含 `payment_params`（timeStamp、nonceStr、package、signType、paySign）
- **AND** 前端使用 `payment_params` 调用 `uni.requestPayment`

#### Scenario: Create course booking with WeChat payment
- **GIVEN** 用户在课程预约页面选择"微信支付"
- **WHEN** 用户点击"立即支付"
- **THEN** 系统创建课程预约 booking，`booking_type='course'`、`payment_status='pending'`
- **AND** 调用微信支付 JSAPI 下单
- **AND** 返回 `payment_params` 供前端唤起微信支付

#### Scenario: WeChat Pay disabled
- **GIVEN** 用户选择"微信支付"
- **AND** `WECHAT_PAY_ENABLED=false`
- **WHEN** 用户点击"立即支付"
- **THEN** 显示"微信支付暂不可用"提示

#### Scenario: WeChat Pay creation failure
- **GIVEN** 用户选择"微信支付"
- **WHEN** 后端调用微信支付下单失败
- **THEN** 显示"支付创建失败，请重试"提示
- **AND** 不创建预约记录

### Requirement: Booking WeChat payment callback
系统 SHALL 提供 `POST /api/v1/bookings/wechat/notify` 处理微信支付订单的异步通知，支付成功后确认预约。回调处理 MUST 同时支持自习室预约和课程预约订单。

#### Scenario: Process successful course booking payment notification
- **GIVEN** 存在 `booking_type='course'` 且 `payment_status='pending'` 的课程预约
- **WHEN** 微信支付发送签名有效、金额匹配、`trade_state='SUCCESS'` 的通知
- **THEN** 系统更新预约 `payment_status='paid'`、`paid_at`、`transaction_id`
- **AND** 返回微信要求的成功响应

#### Scenario: Process successful booking payment notification
- **GIVEN** 存在 `payment_status='pending'` 的预约
- **WHEN** 微信支付发送签名有效、金额匹配、`trade_state='SUCCESS'` 的通知
- **THEN** 系统更新预约 `payment_status='paid'`、`paid_at`、`transaction_id`
- **AND** 返回微信要求的成功响应

#### Scenario: Duplicate booking payment notification
- **GIVEN** 预约已经 `payment_status='paid'`
- **WHEN** 微信支付再次发送同一订单的成功通知
- **THEN** 系统返回成功响应，不重复更新

#### Scenario: Booking payment notification amount mismatch
- **GIVEN** 预约 `total_price=9.00`
- **WHEN** 微信通知金额不为 9.00
- **THEN** 系统拒绝处理，记录错误日志，预约保持 pending

### Requirement: Booking cancellation refund settlement
系统 SHALL 在已支付预约取消成功时，将可退金额退回用户钱包，并记录扣款金额、退款金额和退款流水。退款金额 SHALL 基于预约 `total_price` 计算。余额支付和微信支付预约取消后均退回钱包余额。课程预约取消时，已使用的优惠券 MUST 恢复为可用状态。

#### Scenario: Refund based on paid amount
- **GIVEN** 预约 `original_price=120.00`、`discount_amount=20.00`、`total_price=100.00`
- **AND** 当前取消规则扣 10%
- **WHEN** 用户取消预约
- **THEN** 系统按 `total_price=100.00` 计算扣款
- **AND** `penalty_amount=10.00`
- **AND** `refund_amount=90.00`

#### Scenario: Balance payment refund to wallet
- **GIVEN** 用户使用余额支付了一笔预约
- **WHEN** 用户成功取消该预约
- **THEN** 系统将可退金额加回用户钱包余额
- **AND** 创建 `type='booking_refund'` 的预约取消退款钱包流水
- **AND** 钱包流水展示标题为"取消退款"

#### Scenario: WeChat payment refund to wallet
- **GIVEN** 用户使用微信支付且预约 `payment_status='paid'`
- **WHEN** 用户成功取消该预约
- **THEN** 系统将可退金额加到用户钱包余额
- **AND** 不调用微信原路退款
- **AND** 创建 `type='booking_refund'` 的预约取消退款钱包流水
- **AND** 钱包流水展示标题为"取消退款"

#### Scenario: Course booking cancellation restores coupon
- **GIVEN** 用户使用优惠券支付了课程预约
- **WHEN** 用户成功取消该课程预约
- **THEN** 系统退还优惠券为可用状态
- **AND** 退款金额按 `total_price` 计算

#### Scenario: Atomic settlement
- **GIVEN** 用户取消一笔可取消预约
- **WHEN** 系统执行取消结算
- **THEN** 订单状态更新、余额增加、钱包流水创建在同一数据库事务内完成
- **AND** 任一步失败时所有变更回滚

#### Scenario: No refund for invalid cancellation
- **GIVEN** 预约已取消、未支付、属于其他用户或已到开始时间
- **WHEN** 用户请求取消预约
- **THEN** 系统不增加用户钱包余额
- **AND** 不创建退款流水

#### Scenario: Decimal rounding
- **GIVEN** 预约实付金额无法按扣款比例整除到分
- **WHEN** 系统计算扣款金额和退款金额
- **THEN** 金额按人民币两位小数稳定取值
- **AND** `penalty_amount + refund_amount = total_price`
