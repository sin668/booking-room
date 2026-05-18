## ADDED Requirements

### Requirement: Admin menu data model
系统 SHALL 支持后台菜单权限树，节点类型包含 `directory`、`menu`、`button`。

#### Scenario: Directory node
- **WHEN** 创建 `type="directory"` 的菜单节点
- **THEN** 该节点可作为导航分组和权限树父节点

#### Scenario: Menu node
- **WHEN** 创建 `type="menu"` 的菜单节点
- **THEN** 该节点可生成动态路由

#### Scenario: Button node
- **WHEN** 创建 `type="button"` 的权限节点
- **THEN** 该节点不生成动态路由
- **AND** 可在角色权限树中勾选

### Requirement: Component whitelist
系统 SHALL 对菜单 `component` 字段执行白名单校验。

#### Scenario: Component options request
- **WHEN** 管理员请求 `GET /api/v1/admin/menus/component-options`
- **THEN** 返回可配置组件列表

#### Scenario: Valid component
- **WHEN** 管理员创建或更新菜单时提交白名单内的 `component`
- **THEN** 系统保存成功

#### Scenario: Invalid component
- **WHEN** 管理员提交不在白名单内的 `component`
- **THEN** 系统返回 HTTP 422

### Requirement: Admin menu CRUD API
系统 SHALL 提供菜单列表、创建、更新、删除接口。

#### Scenario: Menu tree list
- **WHEN** 管理员请求 `GET /api/v1/admin/menus`
- **THEN** 返回 directory/menu/button 组成的树形列表

#### Scenario: Create menu
- **WHEN** 管理员提交合法菜单数据到 `POST /api/v1/admin/menus`
- **THEN** 系统创建菜单节点并返回完整记录

#### Scenario: Update menu
- **WHEN** 管理员提交合法更新数据到 `PUT /api/v1/admin/menus/{menu_id}`
- **THEN** 系统更新菜单节点

#### Scenario: Delete menu
- **WHEN** 管理员删除无子节点且未被角色使用的菜单
- **THEN** 系统删除该菜单

#### Scenario: Delete menu with children
- **WHEN** 管理员删除仍包含子节点的菜单
- **THEN** 系统返回 HTTP 409

### Requirement: Dynamic route API
系统 SHALL 提供 `GET /api/v1/admin/menus/routes` 接口，返回当前管理员可访问的动态路由树。

#### Scenario: Route tree excludes buttons
- **WHEN** 管理员请求动态路由树
- **THEN** 返回结果仅包含 `directory` 和 `menu` 节点
- **AND** 不包含 `button` 节点

#### Scenario: Route tree filters disabled menus
- **WHEN** 某菜单 `enabled=false`
- **THEN** 动态路由树不返回该菜单

#### Scenario: Super admin route tree
- **GIVEN** 当前管理员为超级管理员
- **WHEN** 请求动态路由树
- **THEN** 返回全部启用的 directory/menu 节点

#### Scenario: Role-based route tree
- **GIVEN** 当前管理员不是超级管理员
- **WHEN** 请求动态路由树
- **THEN** 仅返回其角色授权的 directory/menu 节点

### Requirement: Menu permission enforcement
菜单管理接口 SHALL 受权限码保护。

#### Scenario: Menu view permission
- **WHEN** 管理员没有 `system:menu:view`
- **THEN** 请求菜单列表返回 HTTP 403

#### Scenario: Menu create permission
- **WHEN** 管理员没有 `system:menu:create`
- **THEN** 创建菜单返回 HTTP 403
