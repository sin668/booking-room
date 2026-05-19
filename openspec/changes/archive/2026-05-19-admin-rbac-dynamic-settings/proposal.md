## Why

当前 br-admin 的"系统设置 / 菜单设置"、"系统设置 / 角色权限"、"设置页面 / 个人设置"、"设置页面 / 系统设置"仍主要使用 mock 或本地静态表单数据。br-server 目前的管理接口仅通过 `X-Admin-Token` 做简单管理员校验，没有真实管理员账号、角色、菜单权限、按钮权限和系统配置模型。

随着后台功能扩展，管理端需要一套真实的权限与配置基础能力：

- 管理员登录应由 br-server 统一认证
- 菜单设置应控制左侧导航和动态路由
- 角色权限应支持页面权限和按钮级权限
- 后端管理接口应同步做接口级权限校验
- 个人设置和系统设置应持久化到 br-server

## What Changes

- 新增 admin 用户、角色、菜单、角色菜单授权、用户角色、系统设置等后台数据模型
- 新增真实管理员登录、当前管理员信息、个人资料更新、修改密码 API
- 新增后台菜单 CRUD、动态路由树、组件白名单校验能力
- 新增角色 CRUD、角色菜单/按钮权限分配能力
- 新增系统基础设置和邮件设置 API
- br-admin 登录、动态路由、菜单设置、角色权限、个人设置、系统设置改为调用 br-server
- 后端管理接口引入权限码校验，`X-Admin-Token` 暂时作为 legacy 超级管理员通道兼容
- 新增幂等 seed 脚本初始化默认管理员、超级管理员角色、默认菜单、按钮权限和系统设置

## Capabilities

### New Capabilities

- `admin-auth-api`: 管理员认证、当前管理员信息、个人资料、修改密码、权限上下文
- `admin-menu-api`: 后台菜单/按钮权限模型、CRUD、组件白名单、动态路由数据
- `admin-role-api`: 角色列表、角色 CRUD、角色授权、按钮权限分配
- `admin-settings-api`: 系统基础设置、邮件设置、邮件测试、安全读取策略
- `admin-rbac-ui`: br-admin 菜单设置、角色权限、个人设置、系统设置真实接口改造
- `admin-dynamic-routing`: br-admin 基于 br-server 菜单数据生成左侧导航和动态路由

### Modified Capabilities

- 现有 admin room/seat/activity/booking/upload/verification 管理接口增加接口级权限校验
- br-admin 登录流程从 mock `/api/login`、`/api/admin_info` 改为 br-server 管理员认证接口

## Impact

- **后端模型**: 新增 `AdminUser`、`AdminRole`、`AdminMenu`、`AdminUserRole`、`AdminRoleMenu`、`SystemSetting`
- **后端路由**: 新增 `/api/v1/admin/auth/*`、`/api/v1/admin/menus/*`、`/api/v1/admin/roles/*`、`/api/v1/admin/settings/*`
- **后端鉴权**: `get_current_admin` 升级为管理员上下文，新增 `require_admin_permission(permission_code)` 依赖
- **前端路由**: `permissionMode` 切换为后端动态路由模式，菜单来自 `/api/v1/admin/menus/routes`
- **前端页面**: 菜单设置、角色权限、个人设置、系统设置从 mock/local state 改为真实 API
- **数据迁移**: Alembic 仅建表；默认管理员/角色/菜单/设置通过独立幂等 seed 脚本创建
- **兼容策略**: `X-Admin-Token` 暂时等价超级管理员，后续可移除
- **回滚方案**: 关闭动态路由改回前端固定路由，保留 legacy token 管理接口；数据库可通过 Alembic downgrade 移除新增表
