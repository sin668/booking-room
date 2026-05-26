## ADDED Requirements

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
