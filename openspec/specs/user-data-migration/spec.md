## ADDED Requirements

### Requirement: Alembic migration for schema expansion
系统 SHALL 提供 Alembic 迁移脚本，在不破坏现有 `users` 表数据的前提下，新增 `username`、`email`、`mobile`、`avatar`、`user_type`、`is_super_admin` 等字段。

#### Scenario: Migration adds user_type column
- **GIVEN** 现有 `users` 表包含 app 用户数据
- **WHEN** 执行 schema expansion 迁移
- **THEN** `users` 表新增 `user_type VARCHAR(10) NOT NULL DEFAULT 'app'` 列，现有记录的 `user_type` 均为 `'app'`

#### Scenario: Migration adds admin-specific columns
- **GIVEN** 现有 `users` 表不包含 `username`、`email`、`mobile`、`avatar`、`is_super_admin` 列
- **WHEN** 执行 schema expansion 迁移
- **THEN** 上述列被正确添加，`username` 和 `email` 允许 NULL，`is_super_admin` 默认 FALSE

#### Scenario: Existing data preserved
- **GIVEN** `users` 表已有 app 用户记录
- **WHEN** 执行 schema expansion 迁移
- **THEN** 所有现有 app 用户记录的 id、phone、nickname、password_hash 等字段值不变

### Requirement: Alembic migration for data merge
系统 SHALL 提供数据迁移脚本，将 `admin_users` 表中的所有记录迁移到 `users` 表，`user_type` 设置为 `'admin'`。

#### Scenario: Admin users migrated to users table
- **GIVEN** `admin_users` 表中有 5 条管理员记录
- **WHEN** 执行数据迁移
- **THEN** `users` 表新增 5 条 `user_type='admin'` 的记录，id 保持不变，`username`、`password_hash`、`nickname`、`email`、`mobile`、`avatar`、`is_super_admin`、`status` 等字段值从 `admin_users` 迁移

#### Scenario: Admin user roles foreign key updated
- **GIVEN** `admin_user_roles` 表中 `user_id` 引用 `admin_users.id`
- **WHEN** 执行数据迁移
- **THEN** `admin_user_roles.user_id` 的外键引用更新为 `users.id`，关联关系保持正确

#### Scenario: Duplicate id handling
- **GIVEN** `admin_users` 表中存在 id 与 `users` 表现有 id 相同的记录（UUID 冲突）
- **WHEN** 执行数据迁移
- **THEN** 冲突的管理员记录生成新的 UUID，并在日志中记录 id 映射关系

### Requirement: Partial unique indexes creation
系统 SHALL 在迁移过程中创建 partial unique index 以支持合并后的唯一性约束。

#### Scenario: Phone partial unique index
- **WHEN** 执行迁移
- **THEN** 创建 `CREATE UNIQUE INDEX ix_users_phone_app ON users(phone) WHERE user_type = 'app' AND phone IS NOT NULL`

#### Scenario: Username partial unique index
- **WHEN** 执行迁移
- **THEN** 创建 `CREATE UNIQUE INDEX ix_users_username_admin ON users(username) WHERE user_type = 'admin' AND username IS NOT NULL`

### Requirement: Alembic migration for admin_users table removal
系统 SHALL 在数据迁移和代码更新完成后，提供迁移脚本删除 `admin_users` 表。

#### Scenario: Admin users table dropped
- **GIVEN** 所有 admin 用户数据已迁移到 `users` 表，代码已更新
- **WHEN** 执行清理迁移
- **THEN** `admin_users` 表被删除（DROP TABLE）

### Requirement: Rollback migration
系统 SHALL 提供反向迁移脚本，支持从合并后的 `users` 表恢复独立的 `admin_users` 表。

#### Scenario: Rollback recreates admin_users table
- **GIVEN** 已执行合并迁移，`users` 表包含 app 和 admin 类型用户
- **WHEN** 执行回滚迁移
- **THEN** 重新创建 `admin_users` 表，从 `users` 表中 `user_type='admin'` 的记录回填数据

#### Scenario: Rollback restores admin_user_roles foreign key
- **GIVEN** 已执行合并迁移，`admin_user_roles.user_id` 引用 `users.id`
- **WHEN** 执行回滚迁移
- **THEN** `admin_user_roles.user_id` 外键恢复为引用 `admin_users.id`

#### Scenario: Rollback removes admin records from users table
- **GIVEN** 回滚迁移执行中
- **WHEN** admin_users 表已重建并回填数据
- **THEN** 从 `users` 表中删除所有 `user_type='admin'` 的记录
