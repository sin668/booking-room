## ADDED Requirements

### Requirement: JWT token issuance
系统 SHALL 在用户注册或登录成功后签发 JWT Access Token（15 分钟有效期）和 Refresh Token（7 天有效期）。

#### Scenario: Issue token pair on registration
- **GIVEN** 用户完成注册流程
- **WHEN** 注册成功
- **THEN** 系统返回 Access Token（15min）和 Refresh Token（7d），Access Token 存放于响应体，Refresh Token 存放于 HttpOnly Cookie

#### Scenario: Issue token pair on login
- **GIVEN** 用户使用手机号 + 密码登录成功
- **WHEN** 登录验证通过
- **THEN** 系统返回新的 Access Token 和 Refresh Token，旧 Refresh Token 失效

### Requirement: JWT token refresh
系统 SHALL 支持 Access Token 过期后通过 Refresh Token 获取新的 Token 对。

#### Scenario: Refresh with valid refresh token
- **GIVEN** 用户持有有效的 Refresh Token
- **WHEN** Access Token 过期，前端使用 Refresh Token 请求刷新
- **THEN** 系统签发新的 Access Token（15min）和新的 Refresh Token（7d），旧 Refresh Token 失效（Rotation）

#### Scenario: Refresh with expired refresh token
- **GIVEN** 用户的 Refresh Token 已超过 7 天有效期
- **WHEN** 前端使用该 Refresh Token 请求刷新
- **THEN** 系统拒绝刷新，返回 HTTP 401，提示"登录已过期，请重新登录"

#### Scenario: Refresh token reuse detection
- **GIVEN** 一个 Refresh Token 已被使用过（Rotation 后旧 Token 失效）
- **WHEN** 攻击者使用该已失效的 Refresh Token 请求刷新
- **THEN** 系统拒绝请求，将该用户所有 Token 加入黑名单，强制重新登录（安全策略）

### Requirement: Token blacklist for logout
系统 SHALL 支持用户退出登录时将当前 Token 加入黑名单，实现主动失效。

#### Scenario: User logout
- **GIVEN** 用户已登录，持有有效 Access Token
- **WHEN** 用户点击退出登录
- **THEN** 系统将 Access Token 加入 Redis 黑名单（TTL = Token 剩余有效期），清除 Refresh Token Cookie，返回成功

#### Scenario: Request with blacklisted token
- **GIVEN** 用户退出登录后，Access Token 已在黑名单中
- **WHEN** 使用该 Token 请求受保护接口
- **THEN** 系统拒绝请求，返回 HTTP 401，提示"Token 已失效"

### Requirement: Phone + password login
系统 SHALL 支持使用手机号 + 密码登录。

#### Scenario: Successful login
- **GIVEN** 用户已注册，手机号 13800138000，密码 "Abc123456"
- **WHEN** 用户提交手机号和密码登录
- **THEN** 系统验证密码（bcrypt 比对），验证通过后返回 JWT Token 对

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

### Requirement: Protected route middleware
系统 SHALL 提供 JWT 验证中间件，保护需要认证的 API 路由。

#### Scenario: Access protected route with valid token
- **GIVEN** 用户持有有效的 Access Token
- **WHEN** 请求受保护的 API（如 GET /api/v1/users/me）
- **THEN** 系统验证 Token 有效性，通过后将用户信息注入请求上下文

#### Scenario: Access protected route without token
- **GIVEN** 请求未携带 Authorization Header
- **WHEN** 请求受保护的 API
- **THEN** 系统拒绝请求，返回 HTTP 401，提示"未提供认证信息"

#### Scenario: Access protected route with expired token
- **GIVEN** Access Token 已过期
- **WHEN** 请求受保护的 API
- **THEN** 系统拒绝请求，返回 HTTP 401，提示"Token 已过期"
