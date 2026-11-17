# Proposal: role-page-user-type-data-scope

## Why

1. 角色权限管理页目前用弹窗编辑角色、用独立「菜单权限」弹窗授权，操作割裂；用户管理页已是页面跳转编辑模式，角色管理需要对齐：列表去掉「菜单权限」按钮，新增/编辑跳转到角色编辑页（上方基本信息、下方菜单权限树）。
2. 后台缺少「超级管理员 / 普通用户」的显式区分：后端已有 `User.is_super_admin` 与完整菜单权限体系（超管全菜单、普通管理员按角色菜单），但用户管理列表/表单未暴露该字段，无法在界面上区分和管理。
3. 数据权限缺失：所有业务表没有创建人字段，任何有菜单权限的管理员都能看到全部业务数据。需要实现「普通管理员只能查看自己创建的数据」，超管查看全量。

## What Changes

- **角色管理（br-admin）**：列表移除「菜单权限」操作与授权弹窗；新增/编辑改为路由跳转到新角色编辑页 `role/edit.vue`（基本信息 + 菜单权限树，一屏保存）；删除废弃的 CreateModal/EditModal。
- **角色 API（br-server）**：新增 `GET /api/v1/admin/roles/{role_id}` 详情接口，支撑编辑页回填。
- **用户类型（前后端）**：用户列表新增「用户类型」列（超级管理员/普通用户，app 用户不适用）；新增/编辑用户页在「状态」前增加用户类型下拉；`AdminUserCreate/Update/ListItem` 暴露 `is_super_admin`；设为超管时清空角色关联，列表对超管隐藏「分配角色」操作。
- **数据权限（br-server）**：courses/activities/study_rooms/coupons/teachers 五张内容表新增 `created_by`（可空 UUID，无 FK，沿用 reviewed_by 先例）+ Alembic 迁移；创建接口记录当前管理员；非超管的列表/详情按创建人过滤；座位随所属自习室归属；预约/评价随关联课程/自习室归属；认证/钱包流水/教育 listing 不做数据过滤（用户已确认）；存量数据（created_by 为空）全员可见（用户已确认）。

## 范围与决策

- 用户已确认：完整实现数据权限 + 继续 tweak 流程（记录于 `.comet/rulings.md`）；记录类数据随关联内容归属；历史数据全员可见。
- 数据权限只约束「查看」（列表/详情）；写操作仍由功能权限码控制（已知边界，记录于 design）。
- 超管判定一律用 `is_super_admin`，不用 admin_id 是否存在（legacy X-Admin-Token 的 admin_id 为 UUID(int=0)）。