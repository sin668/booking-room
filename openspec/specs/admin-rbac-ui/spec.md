## Purpose

br-admin 后台 RBAC 界面能力：管理员登录、菜单设置、角色权限与用户管理页面均调用 br-server 真实接口，角色新增/编辑通过页面跳转完成并在编辑页内授权菜单。
## Requirements
### Requirement: br-admin real admin login
br-admin SHALL 使用 br-server 管理员认证接口完成登录，不再依赖 mock 登录接口。

#### Scenario: Successful login
- **WHEN** 管理员在 br-admin 登录页提交正确用户名和密码
- **THEN** 前端调用 `POST /api/v1/admin/auth/login`
- **AND** 保存返回的 access token
- **AND** 进入后台首页

#### Scenario: Login failure
- **WHEN** 登录接口返回 401 或 403
- **THEN** br-admin 显示失败提示并停留在登录页

### Requirement: Menu settings page uses real API
br-admin 菜单设置页 SHALL 调用 br-server 菜单接口管理动态菜单和按钮权限。

#### Scenario: Load menu tree
- **WHEN** 管理员打开菜单设置页
- **THEN** 页面调用 `GET /api/v1/admin/menus`
- **AND** 显示真实菜单权限树

#### Scenario: Create menu with component dropdown
- **WHEN** 管理员新增 directory 或 menu 节点
- **THEN** component 字段通过后端组件白名单下拉选择

#### Scenario: Create button permission
- **WHEN** 管理员新增 button 节点
- **THEN** 页面允许填写按钮权限名称和权限码
- **AND** 该节点不会要求选择页面组件

#### Scenario: Remove mock warning
- **WHEN** 菜单设置页加载
- **THEN** 页面不再展示"页面数据为 Mock 示例数据，非真实数据"

### Requirement: Role permissions page uses real API
br-admin 角色权限页 SHALL 调用 br-server 角色接口管理角色和授权；新增/编辑角色 SHALL 通过页面跳转完成，菜单授权在角色编辑页内完成，列表不再提供独立的「菜单权限」操作。

#### Scenario: Load role list
- **WHEN** 管理员打开角色权限页
- **THEN** 页面调用 `GET /api/v1/admin/roles`
- **AND** 表格展示真实角色数据
- **AND** 操作列不包含「菜单权限」按钮

#### Scenario: Create role via page navigation
- **WHEN** 管理员点击「新增角色」
- **THEN** 页面跳转到角色编辑页（路由 `system_role_edit`，无 id 参数）
- **AND** 页面上方展示角色基本信息表单（名称、编码、说明、状态）
- **AND** 页面下方展示菜单权限树
- **AND** 保存时先调用 `POST /api/v1/admin/roles`，再调用 `PUT /api/v1/admin/roles/{role_id}/menus`

#### Scenario: Edit role via page navigation
- **WHEN** 管理员点击角色的「编辑」操作
- **THEN** 页面跳转到角色编辑页（携带角色 id）
- **AND** 基本信息通过 `GET /api/v1/admin/roles/{role_id}` 回填
- **AND** 菜单权限树通过 `GET /api/v1/admin/roles/{role_id}/menus` 回填勾选状态

#### Scenario: Assign directory menu and button permissions
- **WHEN** 管理员在角色编辑页勾选菜单权限树
- **THEN** 权限树包含 directory/menu/button 节点
- **AND** 管理员可勾选按钮级权限
- **AND** 保存时调用 `PUT /api/v1/admin/roles/{role_id}/menus`

### Requirement: Personal settings page uses real API
br-admin 个人设置页 SHALL 显示并更新当前管理员资料。

#### Scenario: Load current admin profile
- **WHEN** 管理员打开个人设置页
- **THEN** 页面从 `/api/v1/admin/auth/me` 加载 `nickname`、`email`、`mobile`、`avatar`

#### Scenario: Update profile
- **WHEN** 管理员提交个人资料
- **THEN** 页面调用 `PUT /api/v1/admin/auth/profile`

#### Scenario: Change password
- **WHEN** 管理员提交旧密码和新密码
- **THEN** 页面调用 `PUT /api/v1/admin/auth/password`

#### Scenario: Address field removed
- **WHEN** 管理员打开个人设置页
- **THEN** 页面不展示联系地址字段

### Requirement: System settings page uses real API
br-admin 系统设置页 SHALL 使用 br-server 系统设置接口。

#### Scenario: Basic settings tab
- **WHEN** 管理员打开系统设置页
- **THEN** 页面展示基础设置表单并从 `/api/v1/admin/settings` 加载数据

#### Scenario: Email settings tab
- **WHEN** 管理员打开邮件设置
- **THEN** 页面展示邮件设置表单
- **AND** SMTP 密码显示为已设置/未设置状态，不展示明文

#### Scenario: Removed commerce display settings
- **WHEN** 管理员打开系统设置页
- **THEN** 页面不展示商品图片、水印、市场价、价格精度等电商模板设置

### Requirement: Button permission UI enforcement
br-admin SHALL 使用后端返回的权限列表控制按钮显示。

#### Scenario: Unauthorized action hidden
- **GIVEN** 当前管理员没有某按钮权限码
- **WHEN** 页面渲染该操作按钮
- **THEN** 按钮不显示或被禁用

