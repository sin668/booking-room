## Why

当前系统维护两张独立的用户表 `users`（小程序端）和 `admin_users`（管理后台），导致：用户管理分散、数据模型重复、无法统一查询用户、后续扩展（如管理员也想使用小程序、或给普通用户分配管理权限）受阻。合并为统一用户表可以简化数据模型、统一认证体系、为未来功能扩展打下基础。

## What Changes

- 将 `users` 和 `admin_users` 合并为一张统一的 `users` 表，通过 `user_type` 字段区分小程序用户（`app`）和管理员（`admin`）
- 统一字段覆盖两表的差异字段：`phone`（app 登录）、`username`（admin 登录）、`password_hash`、`nickname`、`email`、`mobile`、`avatar`、`balance`、`status`、`is_super_admin` 等
- 保留现有两套认证流程不变：br-app 继续使用手机号+密码，br-admin 继续使用用户名+密码
- 保留两套 JWT Token 机制不变：app 端 access+refresh token，admin 端 admin_access token
- RBAC 权限体系复用现有 `admin_roles`/`admin_user_roles` 表，app 用户也可被分配角色
- **新增**: br-admin 统一用户管理页面和 API，支持对所有类型用户的 CRUD 操作（查看列表、创建、编辑、删除、重置密码、切换状态、分配角色）
- **新增**: `app_register_user` 默认角色，app 用户注册时自动分配，包含基础查看权限
- Alembic 迁移脚本：数据迁移（合并现有数据）、表结构变更、外键更新
- **BREAKING**: `admin_users` 表删除，所有引用 `admin_users` 的外键和查询改为 `users`
- 提供回滚迁移脚本，支持从合并后的 `users` 表恢复出独立的 `admin_users` 表

## Capabilities

### New Capabilities
- `unified-user-model`: 统一用户数据模型，包含 user_type 字段区分用户类型，合并两表的字段定义
- `user-data-migration`: Alembic 迁移脚本，将现有 users 和 admin_users 数据合并到统一 users 表
- `admin-user-management`: br-admin 统一用户管理 API 和前端页面，支持对所有类型用户的 CRUD（列表、创建、编辑、删除、重置密码、切换状态、分配角色）
- `app-default-role`: app 注册用户默认角色（app_register_user），注册时自动分配基础权限

### Modified Capabilities
- `admin-auth-api`: 管理员登录、个人资料、权限校验改为从统一 users 表查询 admin 类型用户
- `user-auth`: 小程序登录从统一 users 表查询 app 类型用户（逻辑不变，底层查询统一）；注册时自动分配 app_register_user 角色

## Impact

**后端 (br-server)**:
- `app/models/user.py` — 统一 User 模型，合并 AdminUser 字段
- `app/models/admin_user.py` — 删除（或标记废弃）
- `app/services/auth_service.py` — 用户查询逻辑适配
- `app/services/admin_auth_service.py` — 管理员查询改为从 users 表按 user_type=admin 查询
- `app/services/seed_admin.py` — 种子数据适配统一 users 表
- `app/api/routes/admin_auth.py` — 登录/me/profile 路由适配
- `app/api/routes/admin_user.py` — 用户管理 CRUD 适配
- `app/api/dependencies.py` — admin 认证依赖适配
- `app/schemas/admin_user.py` — Schema 适配
- `alembic/versions/` — 新增数据迁移和表结构变更迁移
- 所有引用 AdminUser 模型的文件

**回滚方案**:
- 迁移脚本中保留 `old_admin_users_id` 映射字段
- 提供反向迁移脚本：按 user_type=admin 筛选 → 重建 admin_users 表 → 回填数据 → 恢复外键
- 迁移前自动备份数据（可选，通过环境变量控制）
