## ADDED Requirements

### Requirement: App register user default role
系统 SHALL 在角色种子数据中创建 `app_register_user` 角色，作为 app 注册用户的默认角色。

#### Scenario: Role created in seed_admin
- **WHEN** 执行 `seed_admin`
- **THEN** 创建角色 `app_register_user`（name="注册用户", code="app_register_user", is_default=False）
- **AND** 该角色分配基础查看权限菜单（如预约管理查看权限）

#### Scenario: Role is idempotent
- **GIVEN** `app_register_user` 角色已存在
- **WHEN** 再次执行 `seed_admin`
- **THEN** 不创建重复角色，更新已有角色的名称和状态

### Requirement: Auto-assign default role on registration
系统 SHALL 在 app 用户注册成功后，自动分配 `app_register_user` 角色。

#### Scenario: New user gets default role
- **GIVEN** `app_register_user` 角色存在于 `admin_roles` 表
- **WHEN** app 用户完成注册（手机号 + 密码）
- **THEN** 系统创建 `user_type='app'` 的用户记录
- **AND** 自动在 `admin_user_roles` 表中插入该用户与 `app_register_user` 角色的关联

#### Scenario: Default role not found
- **GIVEN** `app_register_user` 角色不存在（未执行 seed_admin）
- **WHEN** app 用户完成注册
- **THEN** 注册仍然成功，不分配角色（不阻塞注册流程）
- **AND** 记录警告日志提示默认角色缺失

#### Scenario: Existing users get role on next login
- **GIVEN** 合并前已注册的 app 用户没有分配角色
- **WHEN** 管理员通过用户管理页面查看该用户
- **THEN** 用户角色列表为空，管理员可手动分配角色

### Requirement: Admin can assign additional roles to app users
系统 SHALL 支持管理员给 app 用户分配额外角色，实现用户分级权限。

#### Scenario: Assign extra roles
- **GIVEN** 一个 app 用户已拥有 `app_register_user` 默认角色
- **WHEN** 管理员通过用户管理页面为该用户额外分配"客服"角色
- **THEN** 该用户同时拥有 `app_register_user` 和"客服"两个角色
- **AND** 用户权限为两个角色权限的并集
