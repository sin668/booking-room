## MODIFIED Requirements

### Requirement: Cancel booking API
系统 SHALL 提供 `POST /api/v1/bookings/{booking_id}/cancel/` 接口，允许用户取消自己的预约。仅 `confirmed` 且 `payment_status='paid'` 的预约可取消。系统 MUST 使用服务端当前时间与预约开始时间（`date + start_time`）计算取消规则：超过 2 天取消不扣款并全额退款；1 天到 2 天之间扣 10% 订单金额；2 小时到 24 小时之间扣 20% 订单金额；2 小时内扣 50% 订单金额；到达预约开始时间点及之后不可取消。取消成功后预约状态变为 `cancelled`，记录取消时间、扣款金额和退款金额，剩余金额退回用户钱包，并生成一条钱包入账流水。若该预约使用了卡券，系统 SHALL 在取消成功后恢复对应用户卡券为可使用状态。

#### Scenario: Successful cancellation more than two days before start
- **GIVEN** 已登录用户拥有状态为 "confirmed"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端时间距离预约开始时间超过 48 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** 预约状态变为 "cancelled"
- **AND** `penalty_amount` 为 0.00
- **AND** `refund_amount` 为 100.00
- **AND** 用户钱包余额增加 100.00
- **AND** 系统创建一条 `type='booking_refund'`、标题为“取消退款”的钱包流水

#### Scenario: Cancellation one to two days before start
- **GIVEN** 已登录用户拥有状态为 "confirmed"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端时间距离预约开始时间大于 24 小时且小于等于 48 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** `penalty_amount` 为 10.00
- **AND** `refund_amount` 为 90.00
- **AND** 用户钱包余额增加 90.00

#### Scenario: Cancellation two to twenty four hours before start
- **GIVEN** 已登录用户拥有状态为 "confirmed"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端时间距离预约开始时间大于 2 小时且小于等于 24 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** `penalty_amount` 为 20.00
- **AND** `refund_amount` 为 80.00
- **AND** 用户钱包余额增加 80.00

#### Scenario: Cancellation within two hours before start
- **GIVEN** 已登录用户拥有状态为 "confirmed"、`payment_status='paid'`、实付金额为 100.00 的预约
- **AND** 当前服务端时间距离预约开始时间大于 0 且小于等于 2 小时
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** `penalty_amount` 为 50.00
- **AND** `refund_amount` 为 50.00
- **AND** 用户钱包余额增加 50.00

#### Scenario: Cancel booking at or after start time
- **GIVEN** 已登录用户拥有状态为 "confirmed" 的预约
- **AND** 当前服务端时间已到达或晚于预约开始时间
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400 或 HTTP 409
- **AND** 错误信息说明预约已开始不可取消
- **AND** 预约状态变为 "completed"
- **AND** 不增加用户钱包余额
- **AND** 不创建退款流水

#### Scenario: Cancel booking restores used coupon
- **GIVEN** 已登录用户拥有一笔使用卡券的 "confirmed" 预约
- **AND** 预约尚未到开始时间且支付状态为 "paid"
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 200
- **AND** 预约状态变为 "cancelled"
- **AND** 对应用户卡券恢复为 `available`

#### Scenario: Cancel already cancelled booking
- **GIVEN** 已登录用户拥有状态为 "cancelled" 的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400，错误信息为"该预约已取消"
- **AND** 不增加用户钱包余额
- **AND** 不创建退款流水

#### Scenario: Cancel unpaid booking
- **GIVEN** 已登录用户拥有 `payment_status='pending'` 的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400
- **AND** 错误信息说明未支付预约不可按退款规则取消
- **AND** 不增加用户钱包余额

#### Scenario: Cancel other user's booking
- **GIVEN** 已登录用户请求其他用户的预约
- **WHEN** 用户发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 404

#### Scenario: Duplicate cancellation does not refund twice
- **GIVEN** 已登录用户拥有一笔已成功取消且已退款的预约
- **WHEN** 用户再次发送 `POST /api/v1/bookings/1/cancel/`
- **THEN** 返回 HTTP 400
- **AND** 用户钱包余额不再变化
- **AND** 不创建第二条退款流水

### Requirement: Booking database model
系统 SHALL 更新 `bookings` 表，包含字段：`id`（主键，自增）、`seat_id`（外键关联 seats.id，非空）、`user_id`（外键关联 users.id，非空）、`room_id`（外键关联 study_rooms.id，非空）、`date`（DATE，非空）、`start_time`（TIME，非空）、`end_time`（TIME，非空）、`status`（VARCHAR(20)，默认 "confirmed"，枚举值 "confirmed"/"cancelled"/"completed"）、`original_price`（DECIMAL(10,2)，非空）、`discount_amount`（DECIMAL(10,2)，默认 0，非空）、`total_price`（DECIMAL(10,2)，非空，表示抵扣后实付金额）、`coupon_id`（外键关联 user_coupons.id，可空）、`payment_method`（VARCHAR(20)，默认 "balance"，枚举值 "balance"/"wechat"）、`payment_status`（VARCHAR(20)，默认 "paid"，枚举值 "pending"/"paid"/"failed"）、`payment_provider`（VARCHAR(20)，可空）、`prepay_id`（VARCHAR(64)，可空）、`transaction_id`（VARCHAR(64)，可空）、`paid_at`（TIMESTAMP，可空）、`cancelled_at`（TIMESTAMP，可空）、`penalty_amount`（DECIMAL(10,2)，默认 0，非空）、`refund_amount`（DECIMAL(10,2)，默认 0，非空）、`cancel_policy`（VARCHAR(32)，可空，用于记录扣费档位）、`created_at`、`updated_at`。

#### Scenario: Create booking record with balance payment
- **GIVEN** 用户使用余额支付创建预约
- **WHEN** 向 `bookings` 表插入一条记录
- **THEN** 记录成功创建
- **AND** `payment_method='balance'`、`payment_status='paid'`
- **AND** `penalty_amount=0`、`refund_amount=0`、`cancelled_at` 为空

#### Scenario: Create booking record with WeChat payment
- **GIVEN** 用户使用微信支付创建预约
- **WHEN** 向 `bookings` 表插入一条记录
- **THEN** 记录成功创建
- **AND** `payment_method='wechat'`、`payment_status='pending'`、`prepay_id` 不为空
- **AND** `penalty_amount=0`、`refund_amount=0`、`cancelled_at` 为空

#### Scenario: Persist cancellation audit fields
- **GIVEN** 用户成功取消预约
- **WHEN** 系统更新 `bookings` 表
- **THEN** `status='cancelled'`
- **AND** `cancelled_at` 不为空
- **AND** `penalty_amount` 和 `refund_amount` 为本次取消计算结果
- **AND** `cancel_policy` 记录对应扣费档位

### Requirement: Booking response schema
预约列表/详情响应 SHALL 包含以下字段：`id`（整数）、`seat_id`（整数）、`user_id`（整数）、`room_id`（整数）、`date`（日期字符串 YYYY-MM-DD）、`start_time`（时间字符串 HH:MM）、`end_time`（时间字符串 HH:MM）、`status`（枚举字符串）、`original_price`（数字）、`discount_amount`（数字）、`total_price`（数字）、`coupon_id`（整数或 null）、`payment_method`（字符串，枚举值 "balance"/"wechat"）、`payment_status`（字符串，枚举值 "pending"/"paid"/"failed"）、`paid_at`（ISO 时间字符串或 null）、`cancelled_at`（ISO 时间字符串或 null）、`penalty_amount`（数字）、`refund_amount`（数字）、`can_cancel`（布尔值）、`created_at`（ISO 时间字符串）、`seat`（对象，包含 id、seat_number、zone、position、price_per_hour）、`room`（对象，包含 id、name、address）。

#### Scenario: Response field validation
- **GIVEN** 客户端请求预约详情
- **WHEN** 后端返回预约详情
- **THEN** 响应包含 `id`、`seat_id`、`room_id`、`date`、`start_time`、`end_time`、`status`、`original_price`、`discount_amount`、`total_price`、`coupon_id`、`payment_method`、`payment_status`、`paid_at`、`cancelled_at`、`penalty_amount`、`refund_amount`、`can_cancel`、`created_at`、`seat`、`room` 字段

#### Scenario: Confirmed future booking can cancel
- **GIVEN** 客户端请求尚未开始且已支付的 confirmed 预约
- **WHEN** 后端返回预约详情或列表项
- **THEN** `can_cancel` 为 true

#### Scenario: Started booking cannot cancel
- **GIVEN** 客户端请求已到达开始时间的预约
- **WHEN** 后端返回预约详情或列表项
- **THEN** `can_cancel` 为 false
- **AND** 订单状态为 "completed" 或在本次响应前被同步为 "completed"

## ADDED Requirements

### Requirement: Auto-complete started bookings
系统 SHALL 在预约开始时间点及之后将仍为 `confirmed` 的已支付预约变为 `completed`，确保已开始预约不可取消。

#### Scenario: Sync completed booking during list query
- **GIVEN** 当前用户存在一笔已到开始时间且状态为 "confirmed" 的已支付预约
- **WHEN** 用户请求 `GET /api/v1/bookings/`
- **THEN** 系统将该预约状态同步为 "completed"
- **AND** 列表响应中该预约不可取消

#### Scenario: Sync completed booking during cancellation attempt
- **GIVEN** 当前用户存在一笔已到开始时间且状态为 "confirmed" 的已支付预约
- **WHEN** 用户请求取消该预约
- **THEN** 系统将该预约状态同步为 "completed"
- **AND** 拒绝取消
