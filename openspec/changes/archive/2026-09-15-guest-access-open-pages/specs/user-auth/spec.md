# user-auth delta

## MODIFIED Requirements

### Requirement: Deleted account authentication guard
系统 SHALL 阻止 `status='deleted'` 的账号继续登录或刷新会话。小程序端在刷新会话失败（含 401 且刷新失败）时 SHALL 仅清理本地登录态并将错误上抛给调用方，SHALL NOT 由请求层直接强制跳转登录页；登录门槛由页面与操作层决定。

#### Scenario: Reject login for deleted account
- **GIVEN** 用户账号状态为 `deleted`
- **WHEN** 用户使用手机号、用户名或微信快速登录
- **THEN** 系统 SHALL 返回 HTTP 403
- **AND** 系统 SHALL NOT 签发新的 access token 或 refresh token

#### Scenario: Reject refresh for deleted account
- **GIVEN** 用户账号状态为 `deleted`
- **WHEN** 用户使用 refresh token 请求刷新会话
- **THEN** 系统 SHALL 返回 HTTP 401 或 HTTP 403
- **AND** 系统 SHALL NOT 签发新的 token

#### Scenario: Token refresh failure does not force global redirect
- **GIVEN** 小程序端任意请求返回 401 且 refresh token 刷新失败
- **WHEN** 请求层处理该失败
- **THEN** 小程序 SHALL 清理本地 token 并抛出「登录已过期」错误
- **AND** 小程序 SHALL NOT 在请求层强制 reLaunch 到登录页
- **AND** 后续导航行为 SHALL 由调用方页面自行决定
