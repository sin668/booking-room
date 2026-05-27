## MODIFIED Requirements

### Requirement: Current user profile read API
系统 SHALL 提供当前登录用户资料读取接口，返回设置页所需的个人资料字段，并允许微信快速登录用户在绑定手机号前 `phone` 为 null。

#### Scenario: Read current profile
- **GIVEN** 用户已登录
- **WHEN** 用户请求当前用户资料接口
- **THEN** 系统返回用户 `id`、`phone`、`username`、`username_updated_at`、`nickname`、`avatar`、`status`、`user_type`、`created_at`
- **AND** 不返回 `password_hash`、refresh token 或角色写权限等敏感数据

#### Scenario: Read WeChat user without bound phone
- **GIVEN** 用户通过微信快速登录创建账号
- **AND** 用户尚未绑定手机号
- **WHEN** 用户请求当前用户资料接口
- **THEN** 响应中的 `phone` SHALL 为 null
- **AND** 响应 SHALL 包含可用于前端展示的 `username`、`nickname`、`avatar`、`status` 和 `user_type`

#### Scenario: Unauthenticated profile read
- **GIVEN** 请求未携带有效 Access Token
- **WHEN** 用户请求当前用户资料接口
- **THEN** 系统返回 HTTP 401
