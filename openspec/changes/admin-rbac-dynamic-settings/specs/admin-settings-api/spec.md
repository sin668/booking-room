## ADDED Requirements

### Requirement: System settings read API
系统 SHALL 提供 `GET /api/v1/admin/settings` 接口，返回系统基础设置和邮件设置。

#### Scenario: Read settings
- **WHEN** 管理员请求系统设置
- **THEN** 返回 HTTP 200
- **AND** 响应包含 `basic` 和 `email` 两组设置

#### Scenario: SMTP password is not exposed
- **WHEN** 管理员读取邮件设置
- **THEN** 响应不包含 `smtp_password` 明文
- **AND** 响应包含 `smtp_password_set` 表示是否已配置密码

### Requirement: Basic system settings update API
系统 SHALL 提供 `PUT /api/v1/admin/settings/basic` 接口，更新系统基础设置。

#### Scenario: Update basic settings
- **WHEN** 管理员提交 `site_name`、`icp_code`、`contact_phone`、`contact_address`、`login_captcha`、`system_open`、`close_text`、`login_desc`
- **THEN** 系统保存设置并返回更新后的基础设置

#### Scenario: Close system access
- **WHEN** 管理员将 `system_open` 设置为 false
- **THEN** 系统保存关闭状态和关闭提示文案

### Requirement: Email settings update API
系统 SHALL 提供 `PUT /api/v1/admin/settings/email` 接口，更新邮件设置。

#### Scenario: Update email settings without password
- **GIVEN** 系统已经配置 SMTP 密码
- **WHEN** 管理员更新邮件设置但不提交 `smtp_password`
- **THEN** 系统保留原 SMTP 密码

#### Scenario: Update email settings with password
- **WHEN** 管理员提交新的 `smtp_password`
- **THEN** 系统更新 SMTP 密码
- **AND** 后续读取仍不返回明文

### Requirement: Email test API
系统 SHALL 提供 `POST /api/v1/admin/settings/email/test` 接口，用当前邮件设置发送测试邮件。

#### Scenario: Successful email test
- **WHEN** 邮件配置有效且管理员提交测试收件地址
- **THEN** 系统尝试发送测试邮件并返回 HTTP 200

#### Scenario: Incomplete email config
- **WHEN** 邮件配置缺少必要字段
- **THEN** 系统返回 HTTP 400

### Requirement: Settings API permission enforcement
系统设置接口 SHALL 受权限码保护。

#### Scenario: View settings permission required
- **WHEN** 管理员没有 `system:settings:view`
- **THEN** 读取系统设置返回 HTTP 403

#### Scenario: Update settings permission required
- **WHEN** 管理员没有 `system:settings:update`
- **THEN** 更新基础设置返回 HTTP 403
