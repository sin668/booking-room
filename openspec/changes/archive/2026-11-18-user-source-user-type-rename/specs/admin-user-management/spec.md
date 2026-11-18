# Delta: admin-user-management

## MODIFIED Requirements

### Requirement: Create user API
系统 SHALL 提供 `POST /api/v1/admin/users` 接口，支持创建 `user_source` 为 app 或 admin 的用户（用户来源）。手机号和用户名唯一性校验为全局校验（不按来源隔离）。admin 来源用户 SHALL 支持 `user_type` 枚举字段（`super-admin` 超级管理员 / `normal-user` 普通用户）；app 来源用户 `user_type` 固定为 `normal-user`。

#### Scenario: Create app user
- **GIVEN** 管理员提交 `user_source='app'`、`phone`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建用户（`user_source` 默认 `'app'`，`user_type='normal-user'`），密码使用 bcrypt 加密，自动分配 `app_register_user` 角色，返回 HTTP 201

#### Scenario: Create admin user
- **GIVEN** 管理员提交 `user_source='admin'`、`username`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建用户（`user_source='admin'`，`user_type` 默认 `'normal-user'`），返回 HTTP 201

#### Scenario: Create super admin user
- **GIVEN** 管理员提交 `user_source='admin'`、`username`、`password` 且 `user_type='super-admin'`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建 `user_type='super-admin'` 的用户，不分配任何角色

#### Scenario: Duplicate phone
- **GIVEN** 手机号已存在于 users 表（任意 user_source）
- **WHEN** 创建用户使用相同手机号
- **THEN** 返回 HTTP 409

#### Scenario: Duplicate username
- **GIVEN** 用户名已存在于 users 表（任意 user_source）
- **WHEN** 创建用户使用相同用户名
- **THEN** 返回 HTTP 409

### Requirement: Admin user type management
系统 SHALL 在用户管理列表与新增/编辑表单中暴露用户来源（`user_source`：app/admin）与管理员用户类型（`user_type`：`super-admin` 超级管理员 / `normal-user` 普通用户）。超级管理员拥有全部菜单与数据权限，不需要分配角色；普通用户按角色分配菜单，数据权限按创建人归属。

#### Scenario: User type column in list
- **WHEN** 管理员打开用户管理列表
- **THEN** 列表展示「用户来源」列（按 `user_source` 显示）与「用户类型」列
- **AND** admin 用户按 `user_type` 显示「超级管理员」或「普通用户」
- **AND** app 用户「用户类型」列显示不适用（`-`）

#### Scenario: User type dropdown in form
- **WHEN** 管理员打开新增/编辑用户页（admin 来源用户）
- **THEN** 表单在「状态」字段前展示「用户类型」下拉（超级管理员/普通用户）
- **AND** 保存时 payload 携带 `user_type`（`'super-admin'` 或 `'normal-user'`）

#### Scenario: Super admin skips role assignment
- **GIVEN** 某 admin 用户 `user_type='super-admin'`
- **WHEN** 管理员查看该用户列表行操作
- **THEN** 「分配角色」操作不显示

#### Scenario: Promote to super admin clears roles
- **GIVEN** 某 admin 用户已分配角色
- **WHEN** 通过 `PUT /api/v1/admin/users/{id}` 设置 `user_type='super-admin'`
- **THEN** 该用户的角色关联被清空

#### Scenario: List API exposes is_super_admin
- **WHEN** 请求 `GET /api/v1/admin/users`
- **THEN** 列表项包含 `user_source` 与 `user_type` 字段，不再包含 `is_super_admin`（原 `is_super_admin` 暴露场景随字段重命名更新）