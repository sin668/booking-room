## Purpose
Define app user authentication behavior, token issuance, and current-user identity fields.

## Requirements

### Requirement: JWT token issuance
系统 SHALL 在用户注册或登录成功后签发 JWT Access Token（15 分钟有效期）和 Refresh Token（7 天有效期）。用户数据从统一的 `users` 表中查询，不再按 `user_type` 过滤。注册成功后自动分配 `app_register_user` 默认角色，并保证用户具有全局唯一 username。

#### Scenario: Issue token pair on registration
- **GIVEN** 用户完成注册流程
- **WHEN** 注册成功
- **THEN** 系统返回 Access Token（15min）和 Refresh Token（7d），Access Token 存放于响应体，Refresh Token 存放于 HttpOnly Cookie
- **AND** 系统自动为该用户分配 `app_register_user` 角色
- **AND** 用户记录包含全局唯一 username

#### Scenario: Issue token pair on login
- **GIVEN** 用户使用手机号或用户名 + 密码登录成功
- **WHEN** 登录验证通过
- **THEN** 系统返回新的 Access Token 和 Refresh Token，旧 Refresh Token 失效

### Requirement: Phone + password login
系统 SHALL 支持使用手机号或用户名 + 密码登录。用户查询从统一的 `users` 表中按 `phone` 或 `username` 查询，不再按 `user_type` 过滤。请求体中 `phone` 和 `username` 至少提供一个。

#### Scenario: Successful login with phone
- **GIVEN** 用户已注册，手机号 13800138000，密码 "Abc123456"
- **WHEN** 用户提交手机号和密码登录（username 为空）
- **THEN** 系统从 `users` 表按 `phone` 匹配用户，验证密码通过后返回 JWT Token 对

#### Scenario: Successful login with username
- **GIVEN** 用户已注册，用户名 "Luna48392"，密码 "Abc123456"
- **WHEN** 用户提交用户名和密码登录（phone 为空）
- **THEN** 系统从 `users` 表按 `username` 匹配用户，验证密码通过后返回 JWT Token 对

#### Scenario: Wrong password
- **GIVEN** 用户已注册，手机号 13800138000
- **WHEN** 用户提交错误密码
- **THEN** 系统拒绝登录，返回 HTTP 401，提示"手机号或密码错误"

#### Scenario: Login with unregistered phone
- **GIVEN** 手机号 13900139000 未注册
- **WHEN** 用户使用该手机号尝试登录
- **THEN** 系统拒绝登录，返回 HTTP 401，提示"手机号或密码错误"（不暴露未注册信息）

#### Scenario: Account banned
- **GIVEN** 用户账号状态为 "banned"
- **WHEN** 用户尝试登录
- **THEN** 系统拒绝登录，返回 HTTP 403，提示"账号已被禁用，请联系客服"

#### Scenario: Missing both phone and username
- **GIVEN** 请求体中 `phone` 和 `username` 均为空
- **WHEN** 用户尝试登录
- **THEN** 系统返回 HTTP 422，提示至少提供手机号或用户名

### Requirement: Current user response includes username
系统 SHALL 在当前用户资料响应中返回 username，供小程序设置页展示。

#### Scenario: Current user contains username
- **GIVEN** 用户已登录且 username 为 `Luna48392`
- **WHEN** 小程序请求当前用户资料
- **THEN** 响应体包含 `username: "Luna48392"`

### Requirement: WeChat code exchange login
系统 SHALL 提供微信快速登录接口，通过微信登录 code 换取 OpenID，并签发与现有小程序登录一致的认证会话。

#### Scenario: Login with bound WeChat OpenID
- **GIVEN** 微信登录 code 有效且换取到的 OpenID 已绑定到某个 app 用户
- **WHEN** 小程序调用微信快速登录接口
- **THEN** 系统 SHALL 为该用户签发 `access_token`
- **AND** 系统 SHALL 在签发 refresh session 时返回 `refresh_token` 并设置 refresh token cookie

#### Scenario: Login with new WeChat OpenID
- **GIVEN** 微信登录 code 有效且换取到的 OpenID 未绑定任何用户
- **WHEN** 小程序调用微信快速登录接口
- **THEN** 系统 SHALL 创建 `phone = null` 的 app 用户
- **AND** 系统 SHALL 将 OpenID 写入 `users.wechat_openid`
- **AND** 系统 SHALL 为新用户生成全局唯一 username 和默认昵称
- **AND** 系统 SHALL 签发与现有登录一致的 token 响应

#### Scenario: Reject invalid WeChat login code
- **GIVEN** 微信登录 code 无效、过期或被微信接口拒绝
- **WHEN** 小程序调用微信快速登录接口
- **THEN** 系统 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 提示“微信登录已过期，请重试”

#### Scenario: WeChat login service unavailable
- **GIVEN** 微信登录配置缺失或微信服务不可用
- **WHEN** 小程序调用微信快速登录接口
- **THEN** 系统 SHALL 返回 HTTP 503
- **AND** 响应 SHALL 提示“微信登录暂不可用”

#### Scenario: Reject banned WeChat user
- **GIVEN** OpenID 已绑定的用户状态为 `banned`
- **WHEN** 小程序调用微信快速登录接口
- **THEN** 系统 SHALL 返回 HTTP 403
- **AND** 系统 SHALL NOT 签发新 token

### Requirement: WeChat session key handling
系统 SHALL 保护微信 `session_key`，不得将其返回给前端。

#### Scenario: Store session key server side
- **GIVEN** 微信 code 换取成功并返回 `session_key`
- **WHEN** 系统需要短期保存该值
- **THEN** 系统 SHALL 将 `session_key` 存入服务端 Redis
- **AND** 缓存 SHALL 设置 10 到 30 分钟的过期时间
- **AND** API 响应 SHALL NOT 包含 `session_key`
