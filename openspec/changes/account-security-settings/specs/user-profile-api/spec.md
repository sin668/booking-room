## ADDED Requirements

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
