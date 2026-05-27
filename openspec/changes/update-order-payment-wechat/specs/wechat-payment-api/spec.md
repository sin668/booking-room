## ADDED Requirements

### Requirement: Booking WeChat payment notification API
系统 SHALL 提供 `POST /api/v1/bookings/wechat/notify` 处理微信支付 API v3 异步通知，用于订单直接支付场景。通知作为预约支付确认的唯一可信依据。

#### Scenario: Process successful booking payment notification
- **GIVEN** 存在 `payment_status="pending"`、`payment_provider="wechat"` 的预约
- **WHEN** 微信支付发送签名有效、解密成功、`trade_state="SUCCESS"` 且金额匹配的通知
- **THEN** 系统使用行级锁读取该预约
- **AND** 更新预约为 `payment_status="paid"`、`paid_at`、`transaction_id`
- **AND** 返回微信要求的成功响应

#### Scenario: Duplicate successful notification
- **GIVEN** 一笔预约已经 `payment_status="paid"`
- **WHEN** 微信支付再次发送同一订单的成功通知
- **THEN** 系统返回成功响应
- **AND** 不重复更新

#### Scenario: Invalid notification signature
- **WHEN** 通知签名校验失败
- **THEN** 系统拒绝处理通知
- **AND** 不更新预约状态

#### Scenario: Notification amount mismatch
- **GIVEN** 预约 `total_price=9.00`
- **WHEN** 解密后的微信通知金额不为 9.00
- **THEN** 系统拒绝处理
- **AND** 记录错误日志

### Requirement: Booking payment status query API
系统 SHALL 提供 `GET /api/v1/bookings/{booking_id}/payment-status`，供前端在微信支付完成后轮询预约的支付状态。

#### Scenario: Query pending booking payment
- **GIVEN** 用户已登录且拥有 `payment_status="pending"` 的预约
- **WHEN** 用户请求 `GET /api/v1/bookings/{booking_id}/payment-status`
- **THEN** 返回 HTTP 200
- **AND** 响应包含 `booking_id`、`payment_status="pending"`

#### Scenario: Query paid booking payment
- **GIVEN** 用户已登录且拥有 `payment_status="paid"` 的预约
- **WHEN** 用户请求 `GET /api/v1/bookings/{booking_id}/payment-status`
- **THEN** 返回 HTTP 200
- **AND** 响应包含 `booking_id`、`payment_status="paid"`、`paid_at`、`transaction_id`

#### Scenario: Query other user's booking payment
- **GIVEN** 用户 A 请求用户 B 的预约支付状态
- **WHEN** 用户 A 请求 `GET /api/v1/bookings/{booking_id}/payment-status`
- **THEN** 返回 HTTP 404
