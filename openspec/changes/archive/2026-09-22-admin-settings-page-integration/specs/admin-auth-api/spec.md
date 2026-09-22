# Delta: admin-auth-api

## MODIFIED Requirements

### Requirement: Current admin profile API
系统 SHALL 提供 `GET /api/v1/admin/auth/me` 接口，返回当前登录管理员资料、角色和权限列表。管理员数据从统一的 `users` 表中查询，不再按 `user_type` 过滤。联系电话 SHALL 以 `users.phone` 列为唯一权威来源，响应字段名为 `phone`（不再使用已废弃的 `mobile` 字段名）；响应 SHALL 包含 `username_updated_at`、`phone_updated_at` 时间戳字段（未记录时为 `null`）。

系统 SHALL 提供 `PUT /api/v1/admin/auth/profile` 接口，允许当前管理员更新个人资料字段 `username`、`nickname`、`email`、`phone`、`avatar`、`gender`、`birthday`、`signature`；字段均为可选，未提供或值与当前一致的字段不触发变更校验；更新成功后 SHALL 返回与 `GET /me` 一致的最新资料。请求体中出现的未声明字段 SHALL 被拒绝（HTTP 422）。

用户名与手机号的变更 SHALL 复用 C 端个人资料（`/api/v1/users/me`）的既有规则：
- 用户名仅支持 6-32 位字母、数字或下划线，非法格式返回 HTTP 422；
- 用户名、手机号均须全局唯一（含 C 端用户），冲突返回 HTTP 409 且不落库；
- 修改成功后分别记录 `username_updated_at` / `phone_updated_at`，30 天（一个月）冻结期内再次修改该类字段时 SHALL 返回 HTTP 429，响应体含 `detail` 提示文案与 `retry_after_seconds` 剩余秒数。

#### Scenario: Current admin info
- **WHEN** 已登录管理员请求 `/api/v1/admin/auth/me`
- **THEN** 返回 HTTP 200
- **AND** 响应包含 `id`、`username`、`nickname`、`email`、`phone`、`avatar`、`username_updated_at`、`phone_updated_at`、`is_super_admin`、`roles`、`permissions`

#### Scenario: Update profile persists fields
- **GIVEN** 已登录管理员且未处于任何冻结期
- **WHEN** 以 `{username, nickname, email, avatar, phone}` 请求 `PUT /api/v1/admin/auth/profile`，且用户名/手机号未被其他用户占用
- **THEN** 返回 HTTP 200，响应字段与更新后的用户记录一致
- **AND** 变更已持久化到 `users` 表，且 `username_updated_at` / `phone_updated_at` 已刷新

#### Scenario: Update profile rejects unknown fields
- **WHEN** `PUT /api/v1/admin/auth/profile` 请求体包含 `mobile` 等未声明字段
- **THEN** 返回 HTTP 422

#### Scenario: Update profile ignores unchanged fields
- **GIVEN** 管理员的手机号上次修改未满 30 天
- **WHEN** 提交的 `phone` 与当前值完全相同
- **THEN** 返回 HTTP 200 且正常保存其他字段，不触发冻结期限制

#### Scenario: Update phone conflicts with existing user
- **GIVEN** 系统中已存在另一用户（任意 `user_type`）持有目标手机号
- **WHEN** 管理员将资料中的 `phone` 更新为该号码
- **THEN** 返回 HTTP 409
- **AND** 管理员资料保持原值

#### Scenario: Username duplicate rejected
- **GIVEN** 系统中已存在其他用户持有目标用户名
- **WHEN** 管理员更新 `username` 为该名称
- **THEN** 返回 HTTP 409 且资料保持原值

#### Scenario: Username invalid format rejected
- **WHEN** 管理员提交的 `username` 不满足 6-32 位字母、数字或下划线
- **THEN** 返回 HTTP 422

#### Scenario: Cooldown blocks second change within 30 days
- **GIVEN** 管理员修改用户名（或手机号）后未满 30 天
- **WHEN** 再次提交不同的用户名（或不同的手机号）
- **THEN** 返回 HTTP 429
- **AND** 响应含提示文案与 `retry_after_seconds`

#### Scenario: Permission list format
- **WHEN** 当前管理员拥有权限
- **THEN** `permissions` 数组中的每一项包含 `label` 和 `value`
- **AND** `value` 为权限码，如 `system:role:create`

#### Scenario: Missing admin token
- **WHEN** 请求未携带 Bearer token 或 legacy admin token
- **THEN** 返回 HTTP 401
