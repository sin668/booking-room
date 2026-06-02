## Purpose
Define current-user profile read and update APIs for app settings.
## Requirements
### Requirement: Current user profile read API
系统 SHALL 提供当前登录用户资料读取接口，返回设置页所需的个人资料字段，并允许微信快速登录用户在绑定手机号前 `phone` 为 null。

#### Scenario: Read current profile
- **GIVEN** 用户已登录
- **WHEN** 用户请求当前用户资料接口
- **THEN** 系统返回用户 `id`、`phone`、`username`、`username_updated_at`、`nickname`、`avatar`、`status`、`user_type`、`created_at`
- **AND** 不返回 `password_hash`、refresh token 或角色写权限等敏感数据

#### Scenario: Unauthenticated profile read
- **GIVEN** 请求未携带有效 Access Token
- **WHEN** 用户请求当前用户资料接口
- **THEN** 系统返回 HTTP 401

#### Scenario: Read WeChat user without bound phone
- **GIVEN** 用户通过微信快速登录创建账号
- **AND** 用户尚未绑定手机号
- **WHEN** 用户请求当前用户资料接口
- **THEN** 响应中的 `phone` SHALL 为 null
- **AND** 响应 SHALL 包含可用于前端展示的 `username`、`nickname`、`avatar`、`status` 和 `user_type`

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

### Requirement: Current user security summary API
系统 SHALL 提供当前登录用户账号安全摘要接口，返回设置页账号与安全分组所需状态。

#### Scenario: Read security summary
- **GIVEN** 用户已登录
- **WHEN** 用户请求账号安全摘要接口
- **THEN** 系统 SHALL 返回用户手机号绑定状态、微信绑定状态、实名认证状态和账号状态
- **AND** 响应 SHALL 返回脱敏手机号和脱敏身份证号（如存在）
- **AND** 响应 SHALL NOT 返回 password_hash、完整身份证号、完整 OpenID 或 refresh token

#### Scenario: Unauthenticated security summary read
- **GIVEN** 请求未携带有效 Access Token
- **WHEN** 用户请求账号安全摘要接口
- **THEN** 系统 SHALL 返回 HTTP 401

### Requirement: Identity verification submission API
系统 SHALL 支持当前登录用户提交实名认证资料，并安全存储实名状态。

#### Scenario: Submit valid identity verification
- **GIVEN** 用户已登录且尚未实名认证
- **WHEN** 用户提交真实姓名和合法身份证号
- **THEN** 系统 SHALL 保存实名记录
- **AND** 系统 SHALL 保存身份证号哈希和脱敏身份证号
- **AND** 系统 SHALL NOT 保存或返回完整身份证号
- **AND** 系统 SHALL 返回实名状态和脱敏信息

#### Scenario: Reject invalid identity verification
- **GIVEN** 用户已登录
- **WHEN** 用户提交空姓名或非法身份证号
- **THEN** 系统 SHALL 返回 HTTP 422
- **AND** 系统 SHALL NOT 创建实名记录

#### Scenario: Prevent overwriting verified identity
- **GIVEN** 用户已完成实名认证
- **WHEN** 用户再次提交不同实名资料
- **THEN** 系统 SHALL 返回 HTTP 409
- **AND** 系统 SHALL NOT 覆盖已有实名记录

### Requirement: Account deletion API
系统 SHALL 支持当前登录用户注销账号，并在提交前强制检查资产和业务风险；校验通过后系统 SHALL 设置 `users.status='deleted'`，不新增注销申请表，不物理删除用户记录。

#### Scenario: Delete account without risks
- **GIVEN** 用户已登录
- **AND** 用户余额为 0
- **AND** 用户没有未完成预约、待处理支付、未用卡券或其他资产风险
- **WHEN** 用户提交注销账号请求
- **THEN** 系统 SHALL 将用户状态设置为 `deleted`
- **AND** 系统 SHALL 撤销该用户 refresh token
- **AND** 系统 SHALL NOT 删除用户记录
- **AND** 系统 SHALL 返回账号已注销状态

#### Scenario: Reject deactivation with balance
- **GIVEN** 用户已登录且钱包余额大于 0
- **WHEN** 用户提交注销账号请求
- **THEN** 系统 SHALL 返回 HTTP 409
- **AND** 响应 SHALL 包含余额未处理的阻断原因
- **AND** 系统 SHALL NOT 修改用户状态

#### Scenario: Reject deactivation with active booking
- **GIVEN** 用户已登录且存在未完成预约
- **WHEN** 用户提交注销账号请求
- **THEN** 系统 SHALL 返回 HTTP 409
- **AND** 响应 SHALL 包含未完成预约的阻断原因
- **AND** 系统 SHALL NOT 修改用户状态

#### Scenario: Reject already deleted account operation
- **GIVEN** 用户账号状态已经为 `deleted`
- **WHEN** 用户尝试再次调用当前用户资料或注销账号接口
- **THEN** 系统 SHALL 拒绝请求
- **AND** 系统 SHALL NOT 创建任何注销记录或物理删除用户
