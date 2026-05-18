## Context

br-admin 当前存在两套路由来源：

- `src/router/modules/*.ts` 静态路由模块
- mock `/api/menus` 返回的后端动态路由结构

`src/settings/projectSetting.ts` 中 `permissionMode` 当前为 `FIXED`，因此默认使用前端固定路由。`src/router/generator.ts` 已具备从后端菜单生成动态路由的基础能力，但数据来源仍是 mock，且没有组件白名单、真实角色权限和后端接口权限边界。

br-server 当前的管理接口通过 `get_current_admin` 校验 `X-Admin-Token`。这适合早期单管理员开发，但无法表达：

- 当前管理员身份
- 管理员角色
- 页面菜单权限
- 按钮权限
- 接口权限校验
- 个人设置和系统配置

## Goals / Non-Goals

**Goals:**

- br-server 提供真实管理员登录和权限上下文
- 菜单设置控制 br-admin 左侧导航和动态路由
- 菜单 component 使用白名单选择，后端校验
- 角色权限支持 directory/menu/button 三类节点
- 按钮级权限可在角色权限树中勾选
- 后端管理接口同步做接口级权限校验
- 个人设置和系统设置持久化到 br-server
- 默认管理员、角色、菜单、系统设置通过幂等 seed 初始化
- 保留 `X-Admin-Token` 作为 legacy 超级管理员通道

**Non-Goals:**

- 多租户权限体系
- 部门/组织架构权限
- 数据范围权限（如仅查看某城市/门店）
- 审计日志
- 密码找回、邮箱验证、MFA
- 前台用户与后台管理员账号合并

## Data Model

### AdminUser

字段建议：

- `id`: UUID primary key
- `username`: unique, indexed
- `password_hash`
- `nickname`
- `email`
- `mobile`
- `avatar`
- `status`: `active` / `disabled`
- `is_super_admin`: boolean
- `created_at`
- `updated_at`

### AdminRole

- `id`: integer primary key
- `name`: 角色名称，如"超级管理员"
- `code`: unique，如 `super_admin`
- `description`
- `status`: `active` / `disabled`
- `is_default`
- `created_at`
- `updated_at`

### AdminMenu

菜单既是动态路由源，也是权限树节点。

- `id`: integer primary key
- `parent_id`: nullable self reference
- `type`: `directory` / `menu` / `button`
- `title`: 展示标题
- `permission_code`: unique，按钮和页面权限码，如 `system:role:view`
- `path`: 路由 path，仅 directory/menu 使用
- `name`: 路由 name，仅 directory/menu 使用
- `component`: 组件白名单值，仅 directory/menu 使用
- `redirect`
- `icon`
- `sort`
- `hidden`
- `keep_alive`
- `enabled`
- `created_at`
- `updated_at`

### Relation Tables

- `admin_user_roles`: `admin_user_id`, `admin_role_id`
- `admin_role_menus`: `admin_role_id`, `admin_menu_id`

### SystemSetting

建议以 key-value 保存，但服务层提供结构化 schema：

- `key`: unique
- `value`: text / json string
- `group`: `basic` / `email`
- `is_secret`: boolean
- `created_at`
- `updated_at`

## Component Whitelist

后端维护允许配置的组件值。菜单设置页用下拉选择，后端创建/更新时校验。

首批白名单建议：

- `LAYOUT`
- `/dashboard/console/console`
- `/system/menu/menu`
- `/system/role/role`
- `/setting/account/account`
- `/setting/system/system`
- `/room/list/index`
- `/room/seats/index`
- `/activity/list/index`
- `/booking/list/index`

如果 component 不在白名单中，接口返回 HTTP 422。

## Dynamic Route Shape

`GET /api/v1/admin/menus/routes` 返回 br-admin 可直接转换的树：

```json
[
  {
    "path": "system",
    "name": "System",
    "component": "LAYOUT",
    "redirect": "/system/menu",
    "meta": {
      "title": "系统设置",
      "icon": "OptionsSharp",
      "permissions": ["system:view"],
      "hidden": false,
      "keepAlive": false
    },
    "children": []
  }
]
```

规则：

- 仅返回 `type in ["directory", "menu"]`
- 仅返回 `enabled=true`
- 普通管理员仅返回其角色授权的菜单节点
- `button` 节点不生成路由，但会进入 `/auth/me` 的 permissions
- `is_super_admin=true` 返回全部启用菜单和全部权限

## Auth and Permission Flow

```text
POST /api/v1/admin/auth/login
        ↓
access_token
        ↓
GET /api/v1/admin/auth/me
        ↓
admin profile + roles + permissions
        ↓
GET /api/v1/admin/menus/routes
        ↓
br-admin addRoute + render sidebar
```

`/auth/me` 返回权限列表格式兼容 br-admin 当前 `usePermission()`：

```json
{
  "permissions": [
    { "label": "角色权限-新增", "value": "system:role:create" }
  ]
}
```

## Interface Permission Enforcement

新增依赖：

```text
get_current_admin_context()
require_admin_permission("room:create")
```

规则：

- Bearer admin token 解析为 `AdminContext`
- `is_super_admin=true` 跳过权限码校验
- 普通管理员必须拥有对应 `permission_code`
- `X-Admin-Token` 命中 `ADMIN_TOKEN` 时返回 legacy super admin context
- 未认证返回 HTTP 401
- 已认证但无权限返回 HTTP 403

首批权限码：

- `system:menu:view/create/update/delete`
- `system:role:view/create/update/delete/assign`
- `system:settings:view/update/email`
- `admin:profile:view/update/password`
- `room:view/create/update/delete/status`
- `seat:view/create/update/delete/status/bulk_create`
- `activity:view/create/update/delete/status`
- `booking:view/cancel`
- `upload:create`

## Settings Scope

### Personal Settings

个人设置对应当前管理员资料：

- `nickname`
- `email`
- `mobile`
- `avatar`
- 修改密码：`old_password`、`new_password`、`confirm_password`

不保留模板中的"联系地址"。

### System Settings

基础设置：

- `site_name`
- `icp_code`
- `contact_phone`
- `contact_address`
- `login_captcha`
- `system_open`
- `close_text`
- `login_desc`

邮件设置：

- `smtp_host`
- `smtp_port`
- `smtp_username`
- `smtp_password`
- `smtp_sender`
- `smtp_tls`

读取邮件设置时不返回 `smtp_password` 明文，仅返回 `smtp_password_set`。

不实现模板中电商残留的显示设置、商品图片、水印、市场价、价格精度。

## Seed Strategy

Alembic migration 只负责建表，不写默认业务数据。

新增幂等脚本：

```text
python -m app.services.seed_admin
```

创建：

- 默认管理员 `admin`
- 超级管理员角色 `super_admin`
- 默认菜单和按钮权限
- 默认系统设置

默认密码策略：

- 开发环境可使用 `admin / 123456`
- 支持 `ADMIN_DEFAULT_USERNAME`、`ADMIN_DEFAULT_PASSWORD`、`ADMIN_DEFAULT_EMAIL`
- 生产环境未设置 `ADMIN_DEFAULT_PASSWORD` 时拒绝创建默认管理员，避免硬编码弱密码

## API Response Style

新 admin API 使用 br-server 原生 REST 格式，不包 `{ code, message, result }`。

分页响应：

```json
{
  "items": [],
  "total": 0,
  "page": 1,
  "page_size": 10
}
```

br-admin API 层负责适配 BasicTable 需要的：

```ts
{
  list,
  page,
  pageSize,
  pageCount,
  itemCount
}
```

## Migration Plan

1. 新增后端模型、schema、service、route、权限依赖
2. 新增 Alembic migration 建表
3. 新增 `seed_admin` 幂等脚本
4. 后端新增 admin auth/menu/role/settings API 测试
5. 现有 admin routes 增加 `require_admin_permission`
6. br-admin 登录和 API auth header 改为 Bearer token，保留 legacy token 兼容
7. br-admin 菜单设置、角色权限、个人设置、系统设置接真实接口
8. 切换 `permissionMode` 为 `BACK`
9. 验证动态路由、按钮权限、接口权限、legacy token 兼容

## Risks / Trade-offs

- **动态菜单配错导致页面不可达**：通过 component 白名单和后端校验降低风险
- **空库无菜单**：通过幂等 seed 脚本初始化默认菜单和超级管理员
- **权限码漏配**：super admin 和 legacy token 可恢复访问；测试覆盖关键接口
- **现有页面仍用 X-Admin-Token**：依赖层保留 legacy super admin 兼容，前端逐步迁移到 Bearer
- **按钮权限 UI 复杂**：使用同一棵权限树表达 directory/menu/button，避免单独按钮授权界面
