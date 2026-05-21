## ADDED Requirements

### Requirement: User list API
系统 SHALL 提供 `GET /api/v1/admin/users` 接口，支持分页查询所有类型用户，支持 `user_type`、`keyword`、`status` 过滤。

#### Scenario: List all users with pagination
- **GIVEN** 系统中存在 app 和 admin 类型用户
- **WHEN** 管理员请求 `GET /api/v1/admin/users?page=1&page_size=10`
- **THEN** 系统返回 HTTP 200，响应包含 `items`（用户列表）、`total`、`page`、`page_size`
- **AND** 每个用户项包含 `id`、`user_type`、`phone`、`username`、`nickname`、`email`、`status`、`balance`、`is_super_admin`、`roles`、`booking_count`、`coupon_count`、`created_at`

#### Scenario: Filter by user_type
- **WHEN** 管理员请求 `GET /api/v1/admin/users?user_type=app`
- **THEN** 仅返回 `user_type='app'` 的用户

#### Scenario: Filter by keyword
- **WHEN** 管理员请求 `GET /api/v1/admin/users?keyword=138`
- **THEN** 返回手机号或昵称包含 "138" 的用户

#### Scenario: Filter by status
- **WHEN** 管理员请求 `GET /api/v1/admin/users?status=banned`
- **THEN** 仅返回状态为 `banned` 的用户

### Requirement: User detail API
系统 SHALL 提供 `GET /api/v1/admin/users/{id}` 接口，返回单个用户的详细信息含统计数据。

#### Scenario: Get user detail
- **GIVEN** 用户 ID 存在
- **WHEN** 管理员请求 `GET /api/v1/admin/users/{id}`
- **THEN** 返回 HTTP 200，响应包含用户完整信息、关联角色列表、预约数量、卡券数量

#### Scenario: User not found
- **GIVEN** 用户 ID 不存在
- **WHEN** 管理员请求 `GET /api/v1/admin/users/{id}`
- **THEN** 返回 HTTP 404

### Requirement: Create user API
系统 SHALL 提供 `POST /api/v1/admin/users` 接口，支持创建 app 或 admin 类型用户。

#### Scenario: Create app user
- **GIVEN** 管理员提交 `user_type='app'`、`phone`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建用户，密码使用 bcrypt 加密，自动分配 `app_register_user` 角色，返回 HTTP 201

#### Scenario: Create admin user
- **GIVEN** 管理员提交 `user_type='admin'`、`username`、`password`、`nickname`
- **WHEN** 请求 `POST /api/v1/admin/users`
- **THEN** 系统创建管理员用户，返回 HTTP 201

#### Scenario: Duplicate phone
- **GIVEN** 手机号已存在于 users 表
- **WHEN** 创建 app 用户使用相同手机号
- **THEN** 返回 HTTP 409

#### Scenario: Duplicate username
- **GIVEN** 用户名已存在于 users 表
- **WHEN** 创建 admin 用户使用相同用户名
- **THEN** 返回 HTTP 409

### Requirement: Update user API
系统 SHALL 提供 `PUT /api/v1/admin/users/{id}` 接口，支持更新用户基本信息和分配角色。

#### Scenario: Update basic info
- **WHEN** 管理员提交 `nickname`、`email` 等字段
- **THEN** 系统更新用户信息并返回更新后的用户详情

#### Scenario: Assign roles
- **WHEN** 管理员提交 `role_ids` 字段（角色 ID 列表）
- **THEN** 系统更新 `admin_user_roles` 关联，返回更新后的用户详情含新角色列表

### Requirement: Delete user API
系统 SHALL 提供 `DELETE /api/v1/admin/users/{id}` 接口，支持删除用户。

#### Scenario: Delete app user
- **GIVEN** 目标用户 `user_type='app'`
- **WHEN** 管理员请求删除
- **THEN** 系统删除用户及其关联的 `admin_user_roles` 记录，返回 HTTP 204

#### Scenario: Cannot delete self
- **GIVEN** 管理员尝试删除自己的账户
- **WHEN** 请求删除
- **THEN** 返回 HTTP 400

### Requirement: Reset password API
系统 SHALL 提供 `PUT /api/v1/admin/users/{id}/reset-password` 接口，支持管理员重置用户密码。

#### Scenario: Reset password
- **WHEN** 管理员提交 `new_password`
- **THEN** 系统更新用户的 `password_hash`，返回 HTTP 200

### Requirement: Toggle user status API
系统 SHALL 提供 `PUT /api/v1/admin/users/{id}/status` 接口，支持切换用户状态。

#### Scenario: Ban app user
- **GIVEN** app 用户当前 `status='active'`
- **WHEN** 管理员请求切换状态
- **THEN** 系统将状态改为 `banned`，返回 HTTP 200

#### Scenario: Disable admin user
- **GIVEN** admin 用户当前 `status='active'`
- **WHEN** 管理员请求切换状态
- **THEN** 系统将状态改为 `disabled`，返回 HTTP 200

#### Scenario: Activate user
- **GIVEN** 用户当前 `status='banned'` 或 `status='disabled'`
- **WHEN** 管理员请求切换状态
- **THEN** 系统将状态改为 `active`，返回 HTTP 200

### Requirement: User management menu and permissions
系统 SHALL 在菜单种子数据中新增"用户管理"菜单及按钮权限。

#### Scenario: Menu seed data
- **WHEN** 执行 `seed_admin`
- **THEN** 创建 `system.user` 菜单（"用户管理"，path: `/system/user/index`）
- **AND** 创建按钮权限: `system:user:view`、`system:user:create`、`system:user:update`、`system:user:delete`、`system:user:reset-password`、`system:user:status`

### Requirement: User management frontend page
系统 SHALL 在 br-admin 中提供用户管理页面，位于系统设置目录下。

#### Scenario: User list page
- **WHEN** 管理员访问用户管理页面
- **THEN** 页面展示 BasicTable 列表，包含用户类型、手机号、昵称、余额、状态、角色、预约数、卡券数、注册时间列
- **AND** 提供用户类型、关键词、状态过滤
- **AND** 操作列包含编辑、分配角色、重置密码、切换状态、删除按钮

#### Scenario: Create user modal
- **WHEN** 管理员点击"新增用户"按钮
- **THEN** 弹出创建弹窗，支持选择用户类型（app/admin），填写对应字段

#### Scenario: Role assignment modal
- **WHEN** 管理员点击"分配角色"按钮
- **THEN** 弹出角色选择弹窗，展示所有角色，支持多选，保存后更新 `admin_user_roles`
