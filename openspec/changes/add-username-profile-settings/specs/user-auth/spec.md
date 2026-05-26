## MODIFIED Requirements

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

## ADDED Requirements

### Requirement: Current user response includes username
系统 SHALL 在当前用户资料响应中返回 username，供小程序设置页展示。

#### Scenario: Current user contains username
- **GIVEN** 用户已登录且 username 为 `Luna48392`
- **WHEN** 小程序请求当前用户资料
- **THEN** 响应体包含 `username: "Luna48392"`
