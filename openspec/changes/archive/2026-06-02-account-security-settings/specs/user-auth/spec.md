## ADDED Requirements

### Requirement: Current user password change
系统 SHALL 支持已登录用户修改自己的登录密码，并要求校验旧密码。

#### Scenario: Change password successfully
- **GIVEN** 用户已登录且旧密码正确
- **WHEN** 用户提交旧密码、新密码和确认新密码
- **THEN** 系统 SHALL 更新当前用户 password_hash
- **AND** 系统 SHALL 撤销该用户现有 refresh token
- **AND** 系统 SHALL 返回密码修改成功响应

#### Scenario: Reject wrong old password
- **GIVEN** 用户已登录
- **WHEN** 用户提交错误旧密码
- **THEN** 系统 SHALL 返回 HTTP 400 或 HTTP 401
- **AND** 系统 SHALL NOT 修改 password_hash
- **AND** 响应 SHALL 提示“原密码错误”

#### Scenario: Reject weak new password
- **GIVEN** 用户已登录且旧密码正确
- **WHEN** 用户提交不符合密码强度规则的新密码
- **THEN** 系统 SHALL 返回 HTTP 422
- **AND** 系统 SHALL NOT 修改 password_hash

#### Scenario: Reject mismatched password confirmation
- **GIVEN** 用户已登录且旧密码正确
- **WHEN** 用户提交的新密码和确认新密码不一致
- **THEN** 系统 SHALL 返回 HTTP 422
- **AND** 系统 SHALL NOT 修改 password_hash

### Requirement: Deleted account authentication guard
系统 SHALL 阻止 `status='deleted'` 的账号继续登录或刷新会话。

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
