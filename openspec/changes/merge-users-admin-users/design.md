## Context

当前 booking-room 系统有两张独立的用户表：
- `users` — 小程序端用户，通过手机号+密码登录，关联 bookings、user_coupons、wallet_transactions 等业务数据
- `admin_users` — 管理后台用户，通过用户名+密码登录，关联 admin_roles（RBAC 权限体系）

两表结构高度重叠（id、password_hash、nickname、status、created_at、updated_at），维护两套用户模型增加了代码复杂度。合并为统一表可简化模型、统一认证、为未来扩展（如管理员使用小程序、用户分级权限）铺路。

## Goals / Non-Goals

**Goals:**
- 合并 `users` 和 `admin_users` 为一张统一的 `users` 表
- 通过 `user_type` 枚举字段（`app` / `admin`）区分用户类型
- br-app 和 br-admin 现有认证流程、Token 机制、前端代码完全不变
- RBAC 权限体系保持不变，admin 类型用户继续关联角色和菜单
- 提供安全的 Alembic 迁移脚本，支持数据合并和回滚

**Non-Goals:**
- 不修改 br-app 前端代码（小程序端保持原样）
- 不改变现有 br-admin 认证 API 接口契约（路径、请求/响应格式不变）
- 不引入统一登录（SSO）或跨端认证
- 不改变 JWT Token 的 payload 结构和过期策略
- 不为 app 用户创建独立的角色体系（复用现有 admin_roles 表）

## Decisions

### D1: 使用 `user_type` 枚举字段区分用户类型

**选择**: 在 `users` 表新增 `user_type` 字段，枚举值 `app`（小程序用户）和 `admin`（管理员）。

**备选方案**:
- (A) 两张表保持不变，通过视图统一查询 → 无法解决模型重复问题，外键仍分散
- (B) 统一表 + 多态关联 → 增加复杂度，PostgreSQL 多态外键支持差
- (C) **`user_type` 枚举字段（选用）** → 简单直观，查询清晰 `WHERE user_type = 'admin'`

**影响**: 所有查询 admin 用户的代码需加 `user_type` 过滤条件。

### D2: 合并字段策略 — 扩展 users 表

**选择**: 在现有 `users` 表基础上新增 `admin_users` 特有字段，所有字段对 app 用户可为空。

合并后 `users` 表字段：
| 字段 | 类型 | 说明 | app | admin |
|------|------|------|-----|-------|
| id | UUID | 主键 | required | required |
| user_type | String(10) | app / admin | 'app' | 'admin' |
| phone | String(11) | 手机号（app 登录） | unique | nullable |
| username | String(50) | 用户名（admin 登录） | nullable | unique |
| password_hash | String(512) | bcrypt 密码 | required | required |
| nickname | String(50) | 昵称 | required | required |
| email | String(255) | 邮箱 | nullable | nullable |
| avatar | String(512) | 头像 | nullable | nullable |
| invite_code | String(20) | 邀请码 | nullable | null |
| wechat_openid | String(128) | 微信 OpenID | nullable | null |
| balance | Numeric(10,2) | 钱包余额 | 0 | 0 |
| is_super_admin | Boolean | 超级管理员 | False | False |
| status | String(20) | 状态 | active/banned | active/disabled |
| created_at / updated_at | DateTime | 时间戳 | auto | auto |

**唯一约束处理**:
- `phone`: 对所有用户都要求唯一（partial unique index）
- `username`: 对所有用户都要求唯一（partial unique index）

### D3: 迁移策略 — 三阶段迁移

```
Phase 1: 扩展 users 表结构（新增字段），不破坏现有功能
Phase 2: 数据迁移（admin_users 数据写入 users 表，user_type='admin'）
Phase 3: 更新代码引用，删除 admin_users 表
```

**备选方案**:
- (A) 一次性迁移 → 风险高，出错难以回滚
- (B) **分阶段迁移（选用）** → 每阶段可独立验证和回滚

### D4: AdminUser 模型处理 — 删除模型，保留别名导入

**选择**: 删除 `admin_user.py` 模型文件，在 `user.py` 中通过 `user_type` 过滤提供查询方法。

不保留 AdminUser 别名类，避免混淆。所有引用 AdminUser 的 service/schema/route 直接改为使用 User 模型 + `user_type='admin'` 条件。

### D5: RBAC 关联表更新

**选择**: `admin_user_roles` 表的 `user_id` 外键从 `admin_users.id` 改为 `users.id`，并在应用层通过 `user_type='admin'` 过滤。

不重命名关联表（`admin_user_roles`），仅更新外键引用，减少改动范围。

### D6: br-admin 统一用户管理 API

**选择**: 新增 `/api/v1/admin/users/` 统一用户管理 API，通过 `user_type` 参数过滤用户类型。

**端点设计**:
| 端点 | 方法 | 权限码 | 说明 |
|------|------|--------|------|
| `/api/v1/admin/users` | GET | `system:user:view` | 用户列表（支持 `user_type`、`keyword`、`status` 过滤，分页） |
| `/api/v1/admin/users` | POST | `system:user:create` | 创建用户（支持 app/admin 类型） |
| `/api/v1/admin/users/{id}` | GET | `system:user:view` | 用户详情（含统计数据） |
| `/api/v1/admin/users/{id}` | PUT | `system:user:update` | 更新用户信息、分配角色 |
| `/api/v1/admin/users/{id}` | DELETE | `system:user:delete` | 删除用户 |
| `/api/v1/admin/users/{id}/reset-password` | PUT | `system:user:reset-password` | 重置密码 |
| `/api/v1/admin/users/{id}/status` | PUT | `system:user:status` | 切换用户状态 |

**列表响应包含**: 基础字段 + 关联角色列表 + 统计数据（booking_count, coupon_count）。

**备选方案**:
- (A) 独立 `/api/v1/admin/app-users/` → 路径隔离但无法复用管理员管理逻辑
- (B) **统一 `/api/v1/admin/users/`（选用）** → 一套 API 管理所有用户，灵活过滤，复用性强

### D7: br-admin 用户管理前端页面

**选择**: 在 br-admin 新增 `system/user/` 页面，沿用角色管理的 BasicTable + Modal 模式。

**页面结构**:
- **列表页** (`index.vue`): 列（ID、手机号、昵称、用户类型、余额、状态、角色、预约数、卡券数、注册时间），过滤（用户类型、关键词、状态），操作（编辑、分配角色、重置密码、切换状态、删除）
- **编辑弹窗** (`EditModal.vue`): 昵称、邮箱、手机号、余额等基本信息
- **角色分配弹窗** (`RoleModal.vue`): 多选角色列表，保存到 `admin_user_roles`
- **创建弹窗** (`CreateModal.vue`): app 用户（手机号+密码+昵称）、管理员用户（用户名+密码+昵称）

**菜单种子数据**: `system.user` → "用户管理"，按钮权限码 `system:user:create`、`system:user:update`、`system:user:delete`、`system:user:reset-password`、`system:user:status`。

### D8: App 注册用户默认角色

**选择**: 在 `seed_admin.py` 中新增 `app_register_user` 角色，app 用户注册时自动分配。

- 角色: name="注册用户", code=`app_register_user`, is_default=False
- 默认权限: 预约管理（查看预约列表）等基础查看权限
- 自动分配时机: `auth_service.py` 注册逻辑中，创建用户后查询 `app_register_user` 角色，插入 `admin_user_roles`
- 管理员可在用户管理页面为 app 用户分配更多角色，实现用户分级权限

**复用现有 RBAC**: app 用户和管理员共用 `admin_roles` 和 `admin_user_roles` 表，不创建独立角色体系。

## Risks / Trade-offs

**[Risk] 数据迁移期间服务不可用** → 使用分阶段迁移，Phase 1 纯 DDL 变更（加列），不锁表。Phase 2 数据迁移在低峰期执行，提供回滚脚本。

**[Risk] 唯一约束冲突** → phone 和 username 在所有用户间唯一（partial unique index WHERE NOT NULL），不跨类型冲突。注册时需处理已存在相同手机号的 admin 用户场景。

**[Risk] 现有 admin 用户的 JWT token 失效** → Token payload 中 `sub` 存储 user UUID，合并后 UUID 不变（直接迁移），现有 token 自然兼容。

**[Risk] status 枚举值不一致** → app 用 `active/banned`，admin 用 `active/disabled`。统一为 `active/banned/disabled`，admin 用户状态从 `disabled` 映射为 `banned`，代码中统一判断。

**[Trade-off] 统一表增加了部分 nullable 字段** → app 用户会有 username/email 等空字段，admin 用户会有 phone/balance 等空字段。这是可接受的，单表灵活性带来的收益远大于字段空置的存储开销。

**[Trade-off] 删除 AdminUser 模型导致改动面较大** → 但这是必要的，保留双模型会增加长期维护负担，一次性清理优于长期共存。

## Migration Plan

### 部署步骤

1. **Phase 1 — Schema 变更**（可在线执行）:
   - `ALTER TABLE users ADD COLUMN user_type VARCHAR(10) DEFAULT 'app' NOT NULL`
   - `ALTER TABLE users ADD COLUMN username VARCHAR(50)`
   - `ALTER TABLE users ADD COLUMN email VARCHAR(255)`
   - `ALTER TABLE users ADD COLUMN mobile VARCHAR(20)`
   - `ALTER TABLE users ADD COLUMN avatar VARCHAR(512)`
   - `ALTER TABLE users ADD COLUMN is_super_admin BOOLEAN DEFAULT FALSE NOT NULL`
   - 创建 partial unique indexes

2. **Phase 2 — 数据迁移**:
   - INSERT INTO users ... SELECT ... FROM admin_users（设置 user_type='admin'）
   - UPDATE admin_user_roles SET user_id = migrated_user_id

3. **Phase 3 — 代码部署**:
   - 更新所有 AdminUser 引用为 User + user_type 过滤
   - 删除 AdminUser 模型
   - DROP TABLE admin_users（通过新迁移）

### 回滚方案

- 提供反向迁移脚本：
  - 从 users 表按 `user_type='admin'` 筛选 → 重建 `admin_users` 表
  - 回填数据到 `admin_users`
  - 恢复 `admin_user_roles` 外键指向
  - 从 `users` 表删除 admin 用户行
  - DROP 合并时新增的列
- 迁移脚本保留 `user_type` 字段，回滚前通过 `user_type` 精确定位

## Open Questions

无 — 合并方案和用户管理功能方案均已确认。
