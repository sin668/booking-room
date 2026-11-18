## Purpose

后台用户管理能力：管理员通过 br-server 用户接口创建、查询、编辑 app 与 admin 类型用户，并管理管理员用户类型（超级管理员/普通用户）与角色分配。
## Requirements
### Requirement: Create user API
系统 SHALL 提供 `POST /api/v1/admin/users` 接口，支持创建 app 或 admin 类型用户。手机号和用户名唯一性校验为全局校验（不再按 `user_type` 隔离）。admin 类型用户 SHALL 支持 `is_super_admin` 字段区分超级管理员与普通用户。

#### Scenario: Create app user
- **GIVEN** 管理员提交 `user_type='app'`、`phone`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建用户（`user_type` 默认 `'app'`），密码使用 bcrypt 加密，自动分配 `app_register_user` 角色，返回 HTTP 201

#### Scenario: Create admin user
- **GIVEN** 管理员提交 `user_type='admin'`、`username`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建用户（`user_type='admin'`），返回 HTTP 201

#### Scenario: Create super admin user
- **GIVEN** 管理员提交 `user_type='admin'`、`username`、`password` 且 `is_super_admin=true`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建 `is_super_admin=true` 的用户，不分配任何角色

#### Scenario: Duplicate phone
- **GIVEN** 手机号已存在于 users 表（任意 user_type）
- **WHEN** 创建用户使用相同手机号
- **THEN** 返回 HTTP 409

#### Scenario: Duplicate username
- **GIVEN** 用户名已存在于 users 表（任意 user_type）
- **WHEN** 创建用户使用相同用户名
- **THEN** 返回 HTTP 409

### Requirement: Admin user type management
系统 SHALL 在用户管理列表与新增/编辑表单中暴露管理员用户类型（超级管理员/普通用户，映射 `is_super_admin`）。超级管理员拥有全部菜单与数据权限，不需要分配角色；普通用户按角色分配菜单，数据权限按创建人归属。

#### Scenario: User type column in list
- **WHEN** 管理员打开用户管理列表
- **THEN** 列表展示「用户类型」列
- **AND** admin 用户按 `is_super_admin` 显示「超级管理员」或「普通用户」
- **AND** app 用户该列显示不适用（`-`）

#### Scenario: User type dropdown in form
- **WHEN** 管理员打开新增/编辑用户页（admin 类型用户）
- **THEN** 表单在「状态」字段前展示「用户类型」下拉（超级管理员/普通用户）
- **AND** 保存时 payload 携带 `is_super_admin`

#### Scenario: Super admin skips role assignment
- **GIVEN** 某 admin 用户 `is_super_admin=true`
- **WHEN** 管理员查看该用户列表行操作
- **THEN** 「分配角色」操作不显示

#### Scenario: Promote to super admin clears roles
- **GIVEN** 某 admin 用户已分配角色
- **WHEN** 通过 `PUT /api/v1/admin/users/{id}` 设置 `is_super_admin=true`
- **THEN** 该用户的角色关联被清空

#### Scenario: List API exposes is_super_admin
- **WHEN** 请求 `GET /api/v1/admin/users`
- **THEN** 列表项包含 `is_super_admin` 字段

