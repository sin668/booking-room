## ADDED Requirements

### Requirement: Admin role list API
系统 SHALL 提供 `GET /api/v1/admin/roles` 接口，返回分页角色列表。

#### Scenario: Successful role list request
- **WHEN** 管理员请求 `GET /api/v1/admin/roles?page=1&page_size=10`
- **THEN** 返回 HTTP 200
- **AND** 响应包含 `items`、`total`、`page`、`page_size`

#### Scenario: Search roles
- **WHEN** 管理员提交角色名称关键词
- **THEN** 系统返回匹配名称或编码的角色

### Requirement: Admin role CRUD API
系统 SHALL 提供角色创建、更新、删除接口。

#### Scenario: Create role
- **WHEN** 管理员提交 `name`、`code`、`description`、`status`
- **THEN** 系统创建角色并返回完整角色记录

#### Scenario: Duplicate role code
- **WHEN** 管理员提交已存在的 `code`
- **THEN** 系统返回 HTTP 409

#### Scenario: Update role
- **WHEN** 管理员更新角色名称、说明或状态
- **THEN** 系统保存更新并返回更新后的角色

#### Scenario: Delete unused role
- **WHEN** 管理员删除未分配给管理员用户的角色
- **THEN** 系统删除该角色

#### Scenario: Delete assigned role
- **WHEN** 管理员删除已分配给管理员用户的角色
- **THEN** 系统返回 HTTP 409

### Requirement: Role menu assignment API
系统 SHALL 提供角色菜单和按钮权限授权接口。

#### Scenario: Read role permissions
- **WHEN** 管理员请求 `GET /api/v1/admin/roles/{role_id}/menus`
- **THEN** 返回完整权限树和该角色已勾选的 menu ids

#### Scenario: Assign menu and button permissions
- **WHEN** 管理员提交 directory/menu/button 节点 id 列表到 `PUT /api/v1/admin/roles/{role_id}/menus`
- **THEN** 系统保存角色授权

#### Scenario: Assigned button appears in permissions
- **GIVEN** 角色被授权某 button 节点
- **WHEN** 使用该角色的管理员请求 `/api/v1/admin/auth/me`
- **THEN** `permissions` 包含该 button 的 `permission_code`

### Requirement: Role API permission enforcement
角色管理接口 SHALL 受权限码保护。

#### Scenario: Role assign permission required
- **WHEN** 管理员没有 `system:role:assign`
- **THEN** 保存角色授权返回 HTTP 403
