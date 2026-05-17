## ADDED Requirements

### Requirement: Query wallet transactions API
系统 SHALL 提供 `GET /api/v1/wallet/transactions` 端点，返回当前认证用户的钱包流水分页列表，并且 MUST 在后端按当前用户身份过滤数据。

#### Scenario: Query first page of all transactions
- **GIVEN** 已认证用户存在钱包流水
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions?page=1&page_size=20&type=all`
- **THEN** 返回 200
- **AND** 响应包含 `items`、`total`、`page`、`page_size` 和 `has_more`
- **AND** `items` 中每条记录只属于当前认证用户

#### Scenario: Query recharge transactions
- **GIVEN** 已认证用户同时存在充值流水和其他类型流水
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions?type=recharge`
- **THEN** 返回 200
- **AND** `items` 中所有记录的 `type` 均为 `recharge`

#### Scenario: Query transactions with invalid type
- **GIVEN** 用户已认证
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions?type=unknown`
- **THEN** 返回 422
- **AND** 错误信息说明流水类型不受支持

#### Scenario: Unauthenticated transaction query
- **GIVEN** 请求未携带有效 token
- **WHEN** 请求访问 `GET /api/v1/wallet/transactions`
- **THEN** 返回 401

### Requirement: Wallet transaction response fields
流水查询 API SHALL 为每条流水返回稳定展示字段，至少包含 `id`、`type`、`title`、`amount`、`bonus_amount`、`direction`、`status`、`payment_method`、`balance_after`、`created_at`、`completed_at` 和 `order_id`。

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

### Requirement: Wallet transactions pagination constraints
流水查询 API SHALL 对分页参数进行约束，`page` 最小为 1，`page_size` 最小为 1 且最大为 50，默认 `page=1`、`page_size=20`。

#### Scenario: Default pagination
- **GIVEN** 用户已认证
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions` 且未传分页参数
- **THEN** 系统按 `page=1` 和 `page_size=20` 返回结果

#### Scenario: Reserved transaction type returns empty page
- **GIVEN** 用户已认证且暂无消费流水
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions?type=consume`
- **THEN** 返回 200
- **AND** `items` 为空数组
- **AND** `total` 为 0

#### Scenario: Page size exceeds limit
- **GIVEN** 用户已认证
- **WHEN** 用户请求 `GET /api/v1/wallet/transactions?page_size=100`
- **THEN** 返回 422
- **AND** 错误信息说明 `page_size` 超出允许范围

### Requirement: Wallet transaction ordering
流水查询 API SHALL 按交易创建时间倒序返回记录；当创建时间相同时，SHALL 使用记录 ID 或稳定字段保证排序结果确定。

#### Scenario: Newest transaction first
- **GIVEN** 当前用户存在多条不同创建时间的钱包流水
- **WHEN** 用户请求第一页流水
- **THEN** 最新创建的流水排在更早创建的流水之前
