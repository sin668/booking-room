## Context

当前 `users` 表通过 `user_type` 字段（`'app'` / `'admin'`）将用户硬隔离为两套登录入口：
- br-app（`auth_service.py`）：注册和登录均查询 `user_type='app'`，登录仅支持手机号
- br-admin（`admin_auth_service.py`）：登录和 token 校验均查询 `user_type='admin'`，登录仅支持用户名

实际上管理后台的访问控制已由 RBAC 角色权限体系承担（`admin_user_roles` + `AdminRole` + `AdminMenu`），`user_type` 不需要再充当登录屏障。

两个系统的认证方式保持不变，但支持 br-app 和 br-admin 同时可以使用手机号或者用户名进行登录。移除 user_type 过滤后，用户只要同时设置了手机号和用户名（并拥有对应角色权限），即可同时访问两个系统。

## Goals / Non-Goals

**Goals:**
- br-app 和 br-admin 的登录接口均同时支持手机号 + 密码和用户名 + 密码两种登录方式
- 移除所有登录查询中的 `user_type` 过滤条件
- `user_type` 保留为来源标识字段（注册来源追踪），不再用于登录权限控制
- 用户创建时的手机号/用户名唯一性校验改为全局（不再按 user_type 隔离）

**Non-Goals:**
- 不合并两套认证 Token 体系（br-app 的 JWTService 与 br-admin 的 admin_access token 保持独立）
- 不修改 RBAC 权限体系
- 不删除 `user_type` 字段或修改数据库 schema
- 不修改注册流程（br-app 注册仍仅通过手机号）

## Decisions

### Decision 1: 移除查询过滤而非删除字段

**选择**: 保留 `user_type` 字段，仅移除查询时的过滤条件。

**替代方案**: 删除 `user_type` 字段。
**否决原因**: `user_type` 作为用户来源标识仍有业务价值（统计、筛选、运营分析），删除需要数据库迁移且破坏现有数据。

### Decision 2: 统一登录接口支持手机号和用户名

**选择**: br-app 的 `UserLogin` schema 和 br-admin 的 `AdminLoginRequest` schema 均改为同时接受 `phone` 和 `username`（两者可选但至少提供一个），后端登录查询先按提供的字段匹配用户。

**实现方式**: 使用 `or_` 条件构建查询，当 `phone` 有值时按 `User.phone` 查找，当 `username` 有值时按 `User.username` 查找。

**替代方案 A**: 创建独立的用户名登录接口。
**否决原因**: 增加不必要的 API 端点，前端需要维护两套登录调用逻辑。

**替代方案 B**: 统一为单一 login identifier 字段（如 `account`），后端自动判断是手机号还是用户名。
**否决原因**: 字段语义模糊，不利于 API 文档和前端表单校验。

### Decision 3: 唯一性校验改为全局

**选择**: 手机号和用户名的唯一性校验不再附加 `user_type` 条件。

**影响**: 现有数据中可能存在同一手机号分别注册了 app 和 admin 用户的情况（不同 user_type）。需在部署前检查并合并重复数据。

**替代方案**: 保持按 user_type 隔离唯一性。
**否决原因**: 既然 user_type 不再是访问屏障，隔离唯一性会导致同一手机号存在两条记录，造成数据混乱和登录歧义。

### Decision 4: 管理后台访问权限完全由角色控制

**选择**: br-admin 的 `get_admin_by_id` 不再检查 `user_type='admin'`，任何拥有管理角色的用户均可访问后台。

**影响**: 需确保 `app_register_user` 默认角色不具备管理后台权限（当前已满足——该角色无菜单权限分配）。

## Risks / Trade-offs

- **[脏数据风险]** 现有数据可能存在跨 user_type 的手机号/用户名重复 → 部署前运行数据一致性检查脚本，合并或标记冲突记录
- **[权限泄露]** 移除 user_type 过滤后，app 用户若被误分配管理角色可访问后台 → RBAC 权限体系已确保只有被显式授予角色的用户才能访问管理接口，风险可控
- **[登录冲突]** 若手机号和用户名分属不同用户 → 查询逻辑按单个字段精确匹配，不会产生歧义；两个字段同时提供时优先使用 `phone`
