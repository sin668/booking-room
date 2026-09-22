# admin-auth-api Specification

## Purpose

定义管理后台的认证与鉴权 HTTP 接口：管理员登录（手机号或用户名 + 密码）、当前管理员信息与权限列表查询、接口级权限校验，涵盖请求参数、响应结构、访问令牌有效期与权限验证规则。
## Requirements
### Requirement: Admin login API
系统 SHALL 提供 `POST /api/v1/admin/auth/login` 接口，允许用户使用手机号或用户名 + 密码登录管理后台。用户数据从统一的 `users` 表中查询，不再按 `user_type` 过滤。请求体中 `phone` 和 `username` 至少提供一个。

管理端访问令牌的有效期 SHALL 由独立配置项 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS` 控制（默认 7 天，最小 3 天），不复用 C 端的 `ACCESS_TOKEN_EXPIRE_MINUTES`（默认 15 分钟）。响应字段 `expires_in` SHALL 等于 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS * 86400` 秒，作为管理端会话有效期的唯一权威来源；br-admin 前端 SHALL 以登录响应的 `expires_in` 决定本地令牌存储时长，登录路径 SHALL NOT 持有与之竞争的独立硬编码有效期常量；仅当响应缺失该字段时（如 `/me` 端点返回的 `AdminUserInfo` 不含 `expires_in`），前端 MAY 退回一个防御性默认值作为兜底。

#### Scenario: Successful admin login with username
- **WHEN** 用户提交正确的 `username` 和 `password`（phone 为空）
- **THEN** 系统从 `users` 表按 `username` 匹配用户，验证密码
- **AND** 系统返回 HTTP 200
- **AND** 响应包含 `access_token`、`token_type="bearer"`、`expires_in`

#### Scenario: Successful admin login with phone
- **WHEN** 用户提交正确的 `phone` 和 `password`（username 为空）
- **THEN** 系统从 `users` 表按 `phone` 匹配用户，验证密码
- **AND** 系统返回 HTTP 200
- **AND** 响应包含 `access_token`、`token_type="bearer"`、`expires_in`

#### Scenario: Admin access token validity is at least three days
- **WHEN** 管理员成功登录并解码返回的 `access_token`
- **THEN** JWT payload 的 `exp` 与 `iat` 之差 SHALL 不小于 3 天（259200 秒）
- **AND** 响应 `expires_in` SHALL 不小于 259200

#### Scenario: Admin token expiry is independent from client app token expiry
- **GIVEN** `ACCESS_TOKEN_EXPIRE_MINUTES` 保持默认 15
- **WHEN** 分别签发管理端令牌（`admin_auth_service`）与 C 端令牌（`jwt_service`）
- **THEN** 管理端令牌有效期由 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS` 决定，C 端令牌有效期仍为 15 分钟
- **AND** 修改 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS` 不影响 C 端令牌有效期

#### Scenario: Admin session survives beyond fifteen minutes
- **GIVEN** 管理员已登录并取得访问令牌
- **WHEN** 在登录后超过 15 分钟但不超过 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS` 的时间内携带该令牌请求任意管理端接口
- **THEN** 系统 SHALL 正常鉴权通过，不返回 HTTP 401
- **AND** br-admin 不跳转登录页

#### Scenario: Invalid credentials
- **WHEN** 用户提交不存在的手机号/用户名或错误密码
- **THEN** 系统返回 HTTP 401

#### Scenario: Disabled admin user
- **WHEN** 状态为 `disabled` 的用户尝试登录
- **THEN** 系统返回 HTTP 403

#### Scenario: Missing both phone and username
- **WHEN** 请求体中 `phone` 和 `username` 均为空
- **THEN** 系统返回 HTTP 422

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

### Requirement: Admin interface permission enforcement
系统 SHALL 在管理接口上执行接口级权限校验。管理员上下文从统一的 `users` 表构建，不再检查 `user_type`。

#### Scenario: Super admin bypasses permission checks
- **GIVEN** 当前用户 `is_super_admin=true`
- **WHEN** 调用任意管理接口
- **THEN** 系统允许访问

#### Scenario: Permission granted
- **GIVEN** 当前用户拥有接口要求的权限码
- **WHEN** 调用该管理接口
- **THEN** 系统允许访问

#### Scenario: Permission denied
- **GIVEN** 当前用户不拥有接口要求的权限码
- **WHEN** 调用该管理接口
- **THEN** 系统返回 HTTP 403

