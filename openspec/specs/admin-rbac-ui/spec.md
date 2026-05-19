## ADDED Requirements

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
br-admin 角色权限页 SHALL 调用 br-server 角色接口管理角色和授权。

#### Scenario: Load role list
- **WHEN** 管理员打开角色权限页
- **THEN** 页面调用 `GET /api/v1/admin/roles`
- **AND** 表格展示真实角色数据

#### Scenario: Assign directory menu and button permissions
- **WHEN** 管理员点击角色的菜单权限操作
- **THEN** 页面显示包含 directory/menu/button 的权限树
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
