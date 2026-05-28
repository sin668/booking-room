## MODIFIED Requirements

### Requirement: Wallet transaction response fields
流水查询 API SHALL 为每条流水返回稳定展示字段，至少包含 `id`、`type`、`title`、`amount`、`bonus_amount`、`direction`、`status`、`payment_method`、`balance_after`、`created_at`、`completed_at` 和 `order_id`。当流水来自预约取消退款时，响应 SHALL 返回 `type='booking_refund'`、标题“取消退款”和关联预约标识，以便前端在钱包流水中展示。

#### Scenario: Completed recharge response mapping
- **GIVEN** 当前用户存在一条已完成充值流水
- **WHEN** 用户请求钱包流水列表
- **THEN** 该流水的 `title` 为“充值到账”
- **AND** `direction` 为 `income`
- **AND** `amount`、`bonus_amount` 和 `balance_after` 以十进制金额字符串返回
- **AND** `completed_at` 使用支付完成时间或等价完成时间

#### Scenario: Pending recharge response mapping
- **GIVEN** 当前用户存在一条待支付充值流水
- **WHEN** 用户请求钱包流水列表
- **THEN** 该流水的 `title` 为“充值待支付”
- **AND** `status` 为 `pending`
- **AND** `balance_after` 可以为 null

#### Scenario: Failed recharge response mapping
- **GIVEN** 当前用户存在一条失败充值流水
- **WHEN** 用户请求钱包流水列表
- **THEN** 该流水的 `title` 为“充值失败”
- **AND** `status` 为 `failed`
- **AND** `direction` 为 `income`

#### Scenario: Booking cancellation refund response mapping
- **GIVEN** 当前用户存在一条预约取消退款流水
- **WHEN** 用户请求钱包流水列表
- **THEN** 该流水的 `type` 为 `booking_refund`
- **AND** 该流水的 `title` 为“取消退款”
- **AND** `direction` 为 `income`
- **AND** `status` 为 `completed`
- **AND** `amount` 等于实际退回钱包金额
- **AND** 响应包含可追踪到预约单的 `order_id` 或等价关联字段

## ADDED Requirements

### Requirement: Wallet transaction type supports booking_refund
钱包流水查询 API SHALL 支持 `booking_refund` 预约取消退款流水。若接口支持按 `type` 过滤，系统 MUST 支持 `type=booking_refund` 查询该退款类型，且 `type=all` 时 MUST 返回该类流水。

#### Scenario: Query all includes booking refund
- **GIVEN** 当前用户存在预约取消退款流水
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions?type=all`
- **THEN** 响应 `items` 包含该退款流水

#### Scenario: Query booking_refund type
- **GIVEN** 当前用户存在预约取消退款流水和充值流水
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions?type=booking_refund`
- **THEN** 响应仅包含预约取消退款流水
- **AND** 每条流水的 `type` 均为 `booking_refund`
- **AND** 每条流水只属于当前认证用户
