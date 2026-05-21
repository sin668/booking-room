## ADDED Requirements

### Requirement: Unified users table schema
系统 SHALL 维护一张统一的 `users` 表存储所有类型用户，通过 `user_type` 字段区分小程序用户（`app`）和管理员（`admin`）。

#### Scenario: App user record
- **GIVEN** 系统创建一个小程序用户
- **WHEN** 用户注册完成
- **THEN** `users` 表插入一条记录，`user_type` 为 `'app'`，`phone` 字段有值，`username` 字段为 NULL

#### Scenario: Admin user record
- **GIVEN** 系统创建一个管理员用户
- **WHEN** 管理员创建完成
- **THEN** `users` 表插入一条记录，`user_type` 为 `'admin'`，`username` 字段有值，`phone` 字段可为 NULL

#### Scenario: user_type column constraint
- **GIVEN** `users` 表的 `user_type` 字段
- **WHEN** 插入或更新记录
- **THEN** `user_type` 值只能是 `'app'` 或 `'admin'`，其他值应被数据库 CHECK 约束拒绝

### Requirement: Partial unique index on phone
系统 SHALL 对 `users.phone` 字段创建 partial unique index，确保仅在 `user_type='app'` 的记录中手机号唯一。

#### Scenario: App user phone uniqueness
- **GIVEN** 已存在一个 `user_type='app'`、`phone='13800138000'` 的用户
- **WHEN** 尝试创建另一个 `user_type='app'`、`phone='13800138000'` 的用户
- **THEN** 数据库拒绝插入，抛出唯一约束违反错误

#### Scenario: Admin user can have same phone as app user
- **GIVEN** 已存在一个 `user_type='app'`、`phone='13800138000'` 的用户
- **WHEN** 创建一个 `user_type='admin'`、`phone='13800138000'` 的管理员
- **THEN** 创建成功，不受 phone 唯一约束影响

#### Scenario: Admin user with null phone
- **GIVEN** 创建一个 `user_type='admin'` 的管理员
- **WHEN** 不提供 phone 字段
- **THEN** 创建成功，`phone` 为 NULL

### Requirement: Partial unique index on username
系统 SHALL 对 `users.username` 字段创建 partial unique index，确保仅在 `user_type='admin'` 的记录中用户名唯一。

#### Scenario: Admin username uniqueness
- **GIVEN** 已存在一个 `user_type='admin'`、`username='admin'` 的用户
- **WHEN** 尝试创建另一个 `user_type='admin'`、`username='admin'` 的用户
- **THEN** 数据库拒绝插入，抛出唯一约束违反错误

#### Scenario: App user username can be null
- **GIVEN** 创建一个 `user_type='app'` 的用户
- **WHEN** 不提供 username 字段
- **THEN** 创建成功，`username` 为 NULL

### Requirement: Unified status field
系统 SHALL 统一 `status` 字段枚举值为 `active`、`banned`、`disabled`。App 用户使用 `active`/`banned`，Admin 用户使用 `active`/`disabled`。

#### Scenario: App user banned
- **GIVEN** 一个 `user_type='app'` 的用户，`status='banned'`
- **WHEN** 该用户尝试登录
- **THEN** 系统拒绝登录，返回 HTTP 403

#### Scenario: Admin user disabled
- **GIVEN** 一个 `user_type='admin'` 的用户，`status='disabled'`
- **WHEN** 该管理员尝试登录
- **THEN** 系统拒绝登录，返回 HTTP 403

### Requirement: AdminUser model removal
系统 SHALL 删除独立的 `AdminUser` 模型，所有管理员操作通过 `User` 模型 + `user_type='admin'` 查询条件完成。

#### Scenario: Admin CRUD uses User model
- **GIVEN** 管理端需要查询管理员列表
- **WHEN** 调用管理员查询接口
- **THEN** 后端通过 `User` 模型查询，过滤条件为 `user_type='admin'`

#### Scenario: Admin role association uses User model
- **GIVEN** 管理员与角色的多对多关系通过 `admin_user_roles` 表维护
- **WHEN** 查询管理员的角色
- **THEN** 通过 `admin_user_roles.user_id` 关联到 `users.id`，并验证对应用户的 `user_type='admin'`

### Requirement: RBAC association table foreign key update
系统 SHALL 更新 `admin_user_roles` 表的 `user_id` 外键，从引用 `admin_users.id` 改为引用 `users.id`。

#### Scenario: Admin role assignment
- **GIVEN** 一个 `user_type='admin'` 的用户
- **WHEN** 为该用户分配角色
- **THEN** `admin_user_roles` 表的 `user_id` 引用 `users.id`，`role_id` 引用 `admin_roles.id`

#### Scenario: Role query returns admin users
- **GIVEN** 某角色通过 `admin_user_roles` 关联了多个用户
- **WHEN** 查询该角色的用户列表
- **THEN** 返回的用户均来自 `users` 表且 `user_type='admin'`
