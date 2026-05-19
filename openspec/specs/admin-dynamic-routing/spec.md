## ADDED Requirements

### Requirement: Backend-driven dynamic routing
br-admin SHALL 使用 br-server 返回的动态路由树生成左侧导航和可访问路由。

#### Scenario: Dynamic route mode enabled
- **WHEN** br-admin 启动并完成登录
- **THEN** 权限模式使用后端动态路由
- **AND** 前端调用 `/api/v1/admin/menus/routes`

#### Scenario: Sidebar generated from route tree
- **WHEN** `/api/v1/admin/menus/routes` 返回菜单树
- **THEN** br-admin 根据该树生成左侧导航
- **AND** 调用 `router.addRoute` 添加可访问路由

### Requirement: Dynamic route schema compatibility
后端动态路由响应 SHALL 与 br-admin 现有 `generateRoutes` 转换逻辑兼容。

#### Scenario: Route item fields
- **WHEN** 后端返回 route item
- **THEN** 每项包含 `path`、`name`、`component`、`meta`
- **AND** `meta` 包含 `title`、`icon`、`permissions`、`hidden`

#### Scenario: Layout route
- **WHEN** 路由节点为布局容器
- **THEN** `component` 为 `LAYOUT`

#### Scenario: Page component route
- **WHEN** 路由节点为具体页面
- **THEN** `component` 为组件白名单中的页面路径

### Requirement: Route authorization
动态路由 SHALL 按当前管理员角色权限过滤。

#### Scenario: Unauthorized menu hidden
- **GIVEN** 当前管理员没有某 menu 节点权限
- **WHEN** 请求动态路由树
- **THEN** 该 menu 节点不返回

#### Scenario: Parent directory retained for authorized child
- **GIVEN** 当前管理员拥有某子菜单权限
- **WHEN** 该子菜单父级 directory 本身没有独立页面
- **THEN** 动态路由树包含必要的父级 directory

#### Scenario: Empty route set
- **GIVEN** 当前管理员没有任何菜单权限且不是超级管理员
- **WHEN** 请求动态路由树
- **THEN** 返回空数组或仅返回允许的基础路由

### Requirement: Safe route configuration
系统 SHALL 防止错误菜单配置导致前端动态导入失败。

#### Scenario: Invalid component rejected before routing
- **WHEN** 管理员尝试保存不存在的组件路径
- **THEN** 后端拒绝保存

#### Scenario: Disabled route excluded
- **WHEN** 菜单节点 `enabled=false`
- **THEN** 动态路由响应不包含该节点

#### Scenario: Hidden route metadata
- **WHEN** 菜单节点 `hidden=true`
- **THEN** 动态路由响应保留该路由但设置 `meta.hidden=true`
