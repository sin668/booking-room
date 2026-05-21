## 1. User 模型合并

- [x] 1.1 更新 `User` 模型（`br-server/app/models/user.py`）：
  - 新增字段：`user_type`（String(10), NOT NULL, DEFAULT 'app'）、`username`（String(50), nullable）、`email`（String(255), nullable）、`mobile`（String(20), nullable）、`avatar`（String(512), nullable）、`is_super_admin`（Boolean, DEFAULT False, NOT NULL）
  - 添加 `__table_args__`：CHECK 约束 `user_type IN ('app', 'admin')`，partial unique index `ix_users_phone`（WHERE phone IS NOT NULL），partial unique index `ix_users_username`（WHERE username IS NOT NULL）
  - 移除 `phone` 列的原 `unique=True`（由 partial unique index 接管）
- [x] 1.2 更新 `User` 模型关联关系：添加 `roles` relationship 到 `AdminRole`（secondary=`admin_user_roles`, back_populates="users", lazy="selectin"），需要 `from app.models.admin_role import AdminRole, admin_user_roles`
- [x] 1.3 更新 `AdminRole` 模型（`br-server/app/models/admin_role.py`）：
  - `admin_user_roles` 联合表的 `ForeignKey("admin_users.id")` 改为 `ForeignKey("users.id")`，列名从 `admin_user_id` 改为 `user_id`，保持 UniqueConstraint
  - `AdminRole.users` relationship 的 back_populates 保持 `"users"`（对应 User.roles）
  - 更新 TYPE_CHECKING import：`from app.models.user import User` 替换 `from app.models.admin_user import AdminUser`
- [x] 1.4 删除 `AdminUser` 模型文件（`br-server/app/models/admin_user.py`）
- [x] 1.5 更新 `br-server/app/models/__init__.py`：移除 `AdminUser` 导出

## 2. Schema 更新

- [x] 2.1 更新 `br-server/app/schemas/user.py`：`UserResponse` 新增 `user_type`、`username`、`email`、`mobile`、`avatar`、`balance`、`is_super_admin`、`roles`（list[AdminRoleSummary]）字段
- [x] 2.2 `br-server/app/schemas/admin_auth.py` 保持不变（AdminLoginRequest/AdminCurrentResponse 等仍用于 admin 端点，仅底层模型引用变更）
- [x] 2.3 新增 `br-server/app/schemas/admin_user_management.py`：用户管理 CRUD schema
  - `AdminUserListParams`（可选 user_type/keyword/status 过滤）
  - `AdminUserListItem`（基础字段 + roles + booking_count + coupon_count）
  - `AdminUserListResponse`（items + total + page + page_size）
  - `AdminUserCreate`（user_type 必选 + phone/username 二选一 + password + nickname）
  - `AdminUserUpdate`（可选 nickname/email/mobile/avatar/balance/role_ids）
  - `AdminUserDetail`（完整字段 + roles + 统计）
  - `AdminResetPassword`（new_password）
  - `AdminToggleStatus`（target_status）
  - `AdminAssignRoles`（role_ids: list[int]）
- [x] 2.4 更新 `br-server/app/schemas/__init__.py`（如存在导出列表）

## 3. Service 层更新

- [x] 3.1 更新 `br-server/app/services/auth_service.py`：
  - 注册查询添加 `User.user_type == 'app'` 过滤
  - 登录查询添加 `User.user_type == 'app'` 过滤
  - 注册成功后查询 `app_register_user` 角色，若存在则插入 `admin_user_roles` 关联（容错：角色不存在时记录 warning 日志，不阻塞注册）
- [x] 3.2 更新 `br-server/app/services/admin_auth_service.py`：
  - 所有 `from app.models.admin_user import AdminUser` → `from app.models.user import User`
  - `login()`：`AdminUser` → `User`，查询添加 `.where(User.user_type == 'admin')`
  - `get_admin_by_id()`：同上
  - `permissions_for()`/`roles_for()`/`permission_codes_for()`：参数类型 `AdminUser` → `User`（接口不变，都是通过 roles relationship 访问）
  - `update_profile()`/`update_password()`：参数类型 `AdminUser` → `User`
- [x] 3.3 更新 `br-server/app/services/seed_admin.py`：
  - `from app.models.admin_user import AdminUser` → `from app.models.user import User`
  - `_get_or_create_admin()`：创建 `User(user_type='admin', ...)` 替代 `AdminUser(...)`
  - `_ensure_user_role()`：`admin_user_roles.c.admin_user_id` → `admin_user_roles.c.user_id`
  - 新增 `_get_or_create_app_role()`：创建 `app_register_user` 角色（name="注册用户", code="app_register_user"）
  - MENU_SEEDS 新增 `MenuSeed("system.user", "menu", "用户管理", "system:user:view", "user", "SystemUser", "/system/user/index", None, "UserOutlined", 23, parent="system")`
  - BUTTON_SEEDS 新增用户管理按钮权限：`("system.user", "system:user:create", "用户管理-新增")`、`("system.user", "system:user:update", "用户管理-编辑")`、`("system.user", "system:user:delete", "用户管理-删除")`、`("system.user", "system:user:reset-password", "用户管理-重置密码")`、`("system.user", "system:user:status", "用户管理-状态")`

## 4. API 路由更新

- [x] 4.1 更新 `br-server/app/api/routes/admin_auth.py`：
  - `from app.models.admin_user import AdminUser` → `from app.models.user import User`
  - `/login`/`/me`/`/profile`/`/password`：`AdminUser` → `User`，service 调用不变（已通过 3.2 适配）
- [x] 4.2 更新 `br-server/app/api/dependencies.py`：
  - `get_current_admin_context`：查询 `User` 表替代 `AdminUser`，添加 `user_type='admin'` 过滤
  - legacy token 处理中的 `AdminUser(...)` 构造改为 `User(user_type='admin', ...)`
- [x] 4.3 新增 `br-server/app/api/routes/admin_user.py`：统一用户管理路由
  - `router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])`
  - `GET ""` — `list_users(user_type/keyword/status/page/page_size)`，依赖 `require_admin_permission("system:user:view")`
  - `POST ""` — `create_user(data: AdminUserCreate)`，依赖 `require_admin_permission("system:user:create")`
  - `GET "/{user_id}"` — `get_user(user_id)`，依赖 `require_admin_permission("system:user:view")`
  - `PUT "/{user_id}"` — `update_user(user_id, data)`，依赖 `require_admin_permission("system:user:update")`
  - `DELETE "/{user_id}"` — `delete_user(user_id)`，依赖 `require_admin_permission("system:user:delete")`
  - `PUT "/{user_id}/reset-password"` — `reset_password(user_id, data)`，依赖 `require_admin_permission("system:user:reset-password")`
  - `PUT "/{user_id}/status"` — `toggle_status(user_id, data)`，依赖 `require_admin_permission("system:user:status")`
- [x] 4.4 新增 `br-server/app/services/admin_user_service.py`：统一用户管理 Service
  - `list_users(db, user_type, keyword, status, page, page_size)` — 分页查询，含子查询统计 booking_count、coupon_count
  - `get_user(db, user_id)` — 查询单个用户含角色和统计
  - `create_user(db, data)` — 创建 app/admin 用户，app 用户自动分配 app_register_user 角色
  - `update_user(db, user_id, data)` — 更新基本信息和角色
  - `delete_user(db, user_id)` — 删除用户及关联角色
  - `reset_password(db, user_id, new_password)` — 重置密码
  - `toggle_status(db, user_id, target_status)` — 切换状态
  - `assign_roles(db, user_id, role_ids)` — 分配角色
- [x] 4.5 注册路由（`br-server/app/main.py`）：新增 `from app.api.routes.admin_user import router as admin_user_router`，在 admin_auth_router 旁 `app.include_router(admin_user_router)`

## 5. Alembic 数据库迁移

- [x] 5.1 创建 Phase 1 迁移脚本：扩展 `users` 表结构
  - `ALTER TABLE users ADD COLUMN user_type VARCHAR(10) DEFAULT 'app' NOT NULL`
  - `ALTER TABLE users ADD COLUMN username VARCHAR(50)`
  - `ALTER TABLE users ADD COLUMN email VARCHAR(255)`
  - `ALTER TABLE users ADD COLUMN mobile VARCHAR(20)`
  - `ALTER TABLE users ADD COLUMN avatar VARCHAR(512)`
  - `ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE NOT NULL`
  - `ALTER TABLE users ADD CONSTRAINT ck_users_user_type CHECK (user_type IN ('app', 'admin'))`
  - 创建 partial unique index `ix_users_phone`：`CREATE UNIQUE INDEX ix_users_phone ON users(phone) WHERE phone IS NOT NULL`
  - 创建 partial unique index `ix_users_username`：`CREATE UNIQUE INDEX ix_users_username ON users(username) WHERE username IS NOT NULL`
  - 更新 `admin_user_roles` 外键：重命名列 `admin_user_id` → `user_id`，更新 FK 引用为 `users.id`
- [x] 5.2 创建 Phase 2 迁移脚本：数据迁移
  - `INSERT INTO users (id, user_type, username, password_hash, nickname, email, mobile, avatar, status, is_super_admin, created_at, updated_at) SELECT id, 'admin', username, password_hash, COALESCE(nickname, ''), email, mobile, avatar, status, is_super_admin, created_at, updated_at FROM admin_users ON CONFLICT (id) DO NOTHING`
  - 处理 UUID 冲突：对已存在的 id 生成新 UUID 并记录映射
- [x] 5.3 创建 Phase 3 迁移脚本：`DROP TABLE admin_users`
- [x] 5.4 创建回滚迁移脚本：
  - 从 users 表按 `user_type='admin'` 筛选 → 重建 `admin_users` 表 → 回填数据 → 恢复 `admin_user_roles` 外键 → 删除 admin 用户行 → 移除新增列和索引

## 6. 测试 — 模型合并

- [x] 6.1 更新 `br-server/tests/test_admin_models.py`：所有 `AdminUser` → `User`，创建时指定 `user_type='admin'`
- [x] 6.2 更新 `br-server/tests/test_admin_auth_api.py`：所有 `AdminUser` → `User`，路由导入路径更新
- [x] 6.3 更新 `br-server/tests/test_admin_permissions.py`：`AdminUser` → `User`，查询添加 `user_type='admin'`
- [x] 6.4 更新 `br-server/tests/test_admin_role_api.py`：如有 `AdminUser` 引用则替换
- [x] 6.5 新增 `br-server/tests/test_unified_user_model.py`：
  - 测试创建 app 用户时 `user_type` 默认为 `'app'`
  - 测试创建 admin 用户时 `user_type='admin'`
  - 测试 phone partial unique index（同 phone 不能创建两个用户）
  - 测试 username partial unique index
  - 测试 CHECK 约束拒绝非法 user_type
  - 测试 User.roles relationship 返回关联的 AdminRole

## 7. 代码审查 — AdminUser 清除

- [x] 7.1 `grep -rn "AdminUser" br-server/app/ --include="*.py"`：确认无残留引用
- [x] 7.2 `grep -rn "admin_users" br-server/app/ --include="*.py"`：确认无残留表名引用（仅迁移脚本和 admin_user_roles 关联表名除外）
- [x] 7.3 运行现有测试 `pytest tests/ -q`：确保模型合并不破坏现有功能

## 8. 默认角色

- [x] 8.1 新增 `br-server/tests/test_app_default_role.py`：
  - 测试 `seed_admin()` 创建 `app_register_user` 角色
  - 测试重复执行 seed 幂等性
  - 测试 app 用户注册后自动获得 `app_register_user` 角色
  - 测试角色不存在时注册不阻塞（mock 场景）

## 9. 用户管理 API 测试

- [x] 9.1 新增 `br-server/tests/test_admin_user_management.py`：
  - 测试 GET 列表（分页、user_type 过滤、keyword 过滤、status 过滤）
  - 测试 GET 详情（含 booking_count、coupon_count 统计）
  - 测试 POST 创建 app 用户（验证 user_type='app'、自动分配角色、phone 唯一）
  - 测试 POST 创建 admin 用户（验证 user_type='admin'、username 唯一）
  - 测试 PUT 更新用户信息
  - 测试 PUT 分配角色
  - 测试 PUT 重置密码
  - 测试 PUT 切换状态（active↔banned, active↔disabled）
  - 测试 DELETE 删除用户
  - 测试权限码校验（无权限时返回 403）
- [x] 9.2 运行全部测试 `pytest tests/ -q`

## 10. 用户管理前端页面

- [x] 10.1 新增 `br-admin/src/api/system/user.ts`：统一用户管理 API（替换现有仅 auth 的内容）
  - 保留 `getUserInfo`/`login`/`updateProfile`/`updatePassword`/`logout`（admin 自身认证）
  - 新增 `getUserList(params)` → GET /v1/admin/users
  - 新增 `getUserDetail(id)` → GET /v1/admin/users/{id}
  - 新增 `createUser(data)` → POST /v1/admin/users
  - 新增 `updateUser(id, data)` → PUT /v1/admin/users/{id}
  - 新增 `deleteUser(id)` → DELETE /v1/admin/users/{id}
  - 新增 `resetPassword(id, data)` → PUT /v1/admin/users/{id}/reset-password
  - 新增 `toggleUserStatus(id, data)` → PUT /v1/admin/users/{id}/status
  - 新增接口类型：`UserListParams`/`UserListItem`/`UserCreateParams`/`UserUpdateParams`/`UserDetail`
- [x] 10.2 新增 `br-admin/src/views/system/user/columns.ts`：列表列定义
  - ID、手机号、昵称、用户类型（NTag: app=primary/admin=success）、余额、状态（NTag）、角色（NTag 列表）、预约数、卡券数、注册时间
- [x] 10.3 新增 `br-admin/src/views/system/user/index.vue`：用户列表页
  - BasicTable + request=loadDataTable + actionColumn（编辑、分配角色、重置密码、切换状态、删除）
  - 顶部过滤：n-select 用户类型（全部/app/admin）、n-input 关键词搜索、n-select 状态筛选
  - 新增按钮：`v-permission="{ action: ['system:user:create'] }"`
  - 操作按钮权限控制：`system:user:update/delete/reset-password/status`
  - 参考模式：`br-admin/src/views/system/role/role.vue`
- [x] 10.4 新增 `br-admin/src/views/system/user/CreateModal.vue`：创建用户弹窗
  - n-radio-group 选择用户类型（app/admin）
  - app：手机号 + 密码 + 昵称（必填）
  - admin：用户名 + 密码 + 昵称（必填）
  - 参考模式：`br-admin/src/views/system/role/CreateModal.vue`
- [x] 10.5 新增 `br-admin/src/views/system/user/EditModal.vue`：编辑用户弹窗
  - 表单字段：昵称、邮箱、手机号、余额（仅显示/编辑非敏感信息）
  - 参考模式：`br-admin/src/views/system/role/EditModal.vue`
- [x] 10.6 新增 `br-admin/src/views/system/user/RoleModal.vue`：角色分配弹窗
  - 获取所有角色列表（调用 getRoleList API）
  - n-checkbox-group 多选已分配角色
  - 保存调用 assignRoles API
- [x] 10.7 验证前端：`cd br-admin && npm run build`，确认构建无错误

## 11. 文档与最终验证

- [x] 11.1 更新 `docs/api.md`：补充统一用户管理 API 文档（7 个端点的请求/响应格式）
- [x] 11.2 前端构建验证：`cd br-app && npm run build`，确认 br-app 不受影响
- [x] 11.3 运行全部后端测试：`cd br-server && pytest tests/ -q`
- [x] 11.4 最终 `grep -rn "AdminUser" br-server/`：确认零残留
