## ADDED Requirements

### Requirement: Admin login API
系统 SHALL 提供 `POST /api/v1/admin/auth/login` 接口，允许后台管理员使用用户名和密码登录。

#### Scenario: Successful admin login
- **WHEN** 管理员提交正确的 `username` 和 `password`
- **THEN** 系统返回 HTTP 200
- **AND** 响应包含 `access_token`、`token_type="bearer"`、`expires_in`

#### Scenario: Invalid credentials
- **WHEN** 管理员提交不存在的用户名或错误密码
- **THEN** 系统返回 HTTP 401

#### Scenario: Disabled admin user
- **WHEN** 状态为 `disabled` 的管理员尝试登录
- **THEN** 系统返回 HTTP 403

### Requirement: Current admin profile API
系统 SHALL 提供 `GET /api/v1/admin/auth/me` 接口，返回当前登录管理员资料、角色和权限列表。

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

### Requirement: Admin profile update API
系统 SHALL 提供 `PUT /api/v1/admin/auth/profile` 接口，允许当前管理员更新个人资料。

#### Scenario: Successful profile update
- **WHEN** 管理员提交 `nickname`、`email`、`mobile` 或 `avatar`
- **THEN** 系统更新当前管理员资料并返回更新后的资料

#### Scenario: Username cannot be changed by profile API
- **WHEN** 请求体包含 `username`
- **THEN** 系统忽略该字段或返回 HTTP 422

### Requirement: Admin password update API
系统 SHALL 提供 `PUT /api/v1/admin/auth/password` 接口，允许当前管理员修改密码。

#### Scenario: Successful password update
- **WHEN** 管理员提交正确的 `old_password`、合法的 `new_password` 和一致的 `confirm_password`
- **THEN** 系统更新密码并返回 HTTP 200

#### Scenario: Wrong old password
- **WHEN** `old_password` 不正确
- **THEN** 系统返回 HTTP 400

#### Scenario: Password confirmation mismatch
- **WHEN** `new_password` 与 `confirm_password` 不一致
- **THEN** 系统返回 HTTP 422

### Requirement: Legacy admin token compatibility
系统 SHALL 暂时支持 `X-Admin-Token` 作为 legacy 超级管理员凭证。

#### Scenario: Legacy token accepted
- **WHEN** 请求携带正确的 `X-Admin-Token`
- **THEN** 系统将该请求视为超级管理员上下文

#### Scenario: Wrong legacy token
- **WHEN** 请求携带错误的 `X-Admin-Token`
- **THEN** 系统返回 HTTP 401

### Requirement: Admin interface permission enforcement
系统 SHALL 在管理接口上执行接口级权限校验。

#### Scenario: Super admin bypasses permission checks
- **GIVEN** 当前管理员 `is_super_admin=true`
- **WHEN** 调用任意管理接口
- **THEN** 系统允许访问

#### Scenario: Permission granted
- **GIVEN** 当前管理员拥有接口要求的权限码
- **WHEN** 调用该管理接口
- **THEN** 系统允许访问

#### Scenario: Permission denied
- **GIVEN** 当前管理员不拥有接口要求的权限码
- **WHEN** 调用该管理接口
- **THEN** 系统返回 HTTP 403
