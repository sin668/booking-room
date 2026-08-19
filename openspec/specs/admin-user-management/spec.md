## Requirements

### Requirement: Create user API
系统 SHALL 提供 `POST /api/v1/admin/users` 接口，支持创建 app 或 admin 类型用户。手机号和用户名唯一性校验为全局校验（不再按 `user_type` 隔离）。

#### Scenario: Create app user
- **GIVEN** 管理员提交 `user_type='app'`、`phone`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建用户（`user_type` 默认 `'app'`），密码使用 bcrypt 加密，自动分配 `app_register_user` 角色，返回 HTTP 201

#### Scenario: Create admin user
- **GIVEN** 管理员提交 `user_type='admin'`、`username`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建用户（`user_type='admin'`），返回 HTTP 201

#### Scenario: Duplicate phone
- **GIVEN** 手机号已存在于 users 表（任意 user_type）
- **WHEN** 创建用户使用相同手机号
- **THEN** 返回 HTTP 409

#### Scenario: Duplicate username
- **GIVEN** 用户名已存在于 users 表（任意 user_type）
- **WHEN** 创建用户使用相同用户名
- **THEN** 返回 HTTP 409
