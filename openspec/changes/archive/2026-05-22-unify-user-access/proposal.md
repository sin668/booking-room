## Why

当前 `users` 表通过 `user_type` 字段（`'app'` / `'admin'`）硬隔离两个项目的登录入口：br-app 登录查询 `user_type='app'`，br-admin 登录查询 `user_type='admin'`。这导致同一用户无法同时使用两个系统，增加了管理复杂度。实际上项目的访问控制已经由 RBAC 角色权限体系承担，`user_type` 不应再充当登录屏障，仅需保留为用户来源标识。

## What Changes

- **移除登录查询中的 user_type 过滤**：br-app 手机号登录和 br-admin 用户名登录均不再按 `user_type` 筛选用户，任意用户可通过手机号登录 br-app、通过用户名登录 br-admin（前提是已设置对应字段）
- **user_type 保留为来源标识**：字段本身不删除，新注册的 app 用户仍默认为 `'app'`，管理后台创建的用户仍标记为 `'admin'`，但不再用于登录权限控制
- **用户管理接口调整**：创建用户时的唯一性校验不再按 `user_type` 隔离（手机号全局唯一、用户名全局唯一），列表筛选中 `user_type` 改为可选过滤条件（已支持，无需改动）
- **前端适配**：br-admin 用户管理表单中 `user_type` 字段仍保留，作为来源标识供管理员查看

## Capabilities

### New Capabilities

（无新增能力）

### Modified Capabilities

- `admin-auth-api`: 管理员登录和 token 校验不再按 `user_type='admin'` 过滤用户，改为通过角色权限控制管理后台访问
- `user-auth`: app 端手机号登录和注册不再按 `user_type='app'` 过滤，手机号唯一性校验改为全局
- `admin-user-management`: 用户创建时手机号和用户名唯一性校验改为全局（不再按 user_type 隔离），创建用户时 user_type 作为来源标识自动设置

## Impact

**后端模块**：
- `br-server/app/services/auth_service.py` — register / login 移除 `user_type == 'app'` 过滤
- `br-server/app/services/admin_auth_service.py` — login / get_admin_by_id 移除 `user_type == 'admin'` 过滤
- `br-server/app/services/admin_user_service.py` — create_user 唯一性校验改为全局
- `br-server/app/models/user.py` — CHECK 约束保留不变

**数据库**：
- 现有数据无需迁移，`user_type` 字段值保持原样
- 需确保无手机号/用户名跨 user_type 重复的脏数据（迁移前检查）

**回滚方案**：
- 在登录查询中恢复 `user_type` 过滤条件即可回滚，无需数据库变更
- 所有改动均为代码层过滤逻辑调整，数据库 schema 不变

**测试影响**：
- 受影响的测试需更新断言（移除 user_type 过滤相关的测试用例）
