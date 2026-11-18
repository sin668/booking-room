# Delta: admin-rbac-ui

## MODIFIED Requirements

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