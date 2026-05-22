## MODIFIED Requirements

### Requirement: Admin login API
系统 SHALL 提供 `POST /api/v1/admin/auth/login` 接口，允许用户使用手机号或用户名 + 密码登录管理后台。用户数据从统一的 `users` 表中查询，不再按 `user_type` 过滤。请求体中 `phone` 和 `username` 至少提供一个。

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
系统 SHALL 提供 `GET /api/v1/admin/auth/me` 接口，返回当前登录管理员资料、角色和权限列表。管理员数据从统一的 `users` 表中查询，不再按 `user_type` 过滤。

#### Scenario: Current admin info
- **WHEN** 已登录管理员请求 `/api/v1/admin/auth/me`
- **THEN** 返回 HTTP 200
- **AND** 响应包含 `id`、`username`、`nickname`、`email`、`mobile`、`avatar`、`is_super_admin`、`roles`、`permissions`

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
