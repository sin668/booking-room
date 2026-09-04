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

