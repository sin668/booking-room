## ADDED Requirements

### Requirement: Current user profile read API
系统 SHALL 提供当前登录用户资料读取接口，返回设置页所需的个人资料字段。

#### Scenario: Read current profile
- **GIVEN** 用户已登录
- **WHEN** 用户请求当前用户资料接口
- **THEN** 系统返回用户 `id`、`phone`、`username`、`username_updated_at`、`nickname`、`avatar`、`status`、`user_type`、`created_at`
- **AND** 不返回 `password_hash`、refresh token 或角色写权限等敏感数据

#### Scenario: Unauthenticated profile read
- **GIVEN** 请求未携带有效 Access Token
- **WHEN** 用户请求当前用户资料接口
- **THEN** 系统返回 HTTP 401

### Requirement: Current user profile update API
系统 SHALL 提供当前登录用户资料更新接口，允许用户更新自己的用户名、昵称和头像等安全资料字段。用户名不限制总修改次数，但每次成功修改后 SHALL 进入滚动 24 小时冷却期。

#### Scenario: Update username successfully
- **GIVEN** 用户已登录且用户名 `LunaStudy01` 未被任何用户使用
- **AND** 用户未处于用户名修改冷却期
- **WHEN** 用户提交用户名更新为 `LunaStudy01`
- **THEN** 系统更新当前用户的 `username`
- **AND** 系统记录当前时间为 `username_updated_at`
- **AND** 返回更新后的用户资料

#### Scenario: Reject username update during cooldown
- **GIVEN** 用户已登录且上次成功修改用户名发生在 24 小时内
- **WHEN** 用户提交新的用户名
- **THEN** 系统拒绝更新并返回 HTTP 429
- **AND** 响应包含剩余冷却时间
- **AND** 响应提示“用户名修改后 24 小时内不可再次修改”

#### Scenario: Reject duplicate username
- **GIVEN** 用户已登录且用户名 `LunaStudy01` 已被其他用户使用
- **WHEN** 用户提交用户名更新为 `LunaStudy01`
- **THEN** 系统拒绝更新并返回 HTTP 409
- **AND** 响应提示“该用户名已存在”

#### Scenario: Reject invalid username format
- **GIVEN** 用户已登录
- **WHEN** 用户提交包含空格或中文字符的用户名
- **THEN** 系统拒绝更新并返回 HTTP 422

#### Scenario: Cannot update protected fields
- **GIVEN** 用户已登录
- **WHEN** 用户通过当前用户资料更新接口提交 `balance`、`status`、`user_type` 或 `roles`
- **THEN** 系统 SHALL 忽略这些字段或返回 HTTP 422
- **AND** 不修改对应受保护字段
