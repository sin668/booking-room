# Design: role-page-user-type-data-scope

## 角色编辑页（br-admin）

- 路由：`router/modules/system.ts` 增加 `role/edit/:id?`（name `system_role_edit`，`hideInMenu: true`，`activeMenu: 'system_role'`），与 `system_user_edit` 同模式；BACK 动态路由模式下由 asyncRoute store 合并 hideInMenu 静态子路由，无需后端菜单种子。
- `role/edit.vue` 仿 `user/edit.vue` 结构：顶部返回/取消/保存；基本信息卡（角色名称、角色编码、角色说明、状态）；菜单权限卡（n-tree，cascade/checkable，全部展开/全部选择按钮，复用 `getRoleMenus`/`updateRoleMenus` 与 `normalizeMenuTree`）。
- 编辑模式用新增的 `GET /v1/admin/roles/{id}` 回填基本信息；新增模式保存时先 `createRole` 再 `updateRoleMenus(新id)`；编辑模式保存时 `updateRole` + `updateRoleMenus`。
- `role.vue`：移除「菜单权限」操作、授权 n-modal 及相关状态/函数；新增/编辑改 `router.push`；删除 `CreateModal.vue`、`EditModal.vue`（改造后无引用）。

## 用户类型（前后端）

- 语义映射：「用户类型」下拉 = `is_super_admin`（超级管理员 true / 普通用户 false），仅对 `user_type='admin'` 用户适用；app 用户列表列显示 `-`，表单不显示下拉。现有「用户来源」列（后台创建/App注册）保留。
- 后端：`AdminUserListItem` 增加 `is_super_admin`；`AdminUserCreate` 增加 `is_super_admin: bool = False`（仅 admin 类型生效）；`AdminUserUpdate` 增加 `is_super_admin: bool | None`，设为 true 时清空 `admin_user_roles` 关联（超管不需要角色）。
- 前端：`user/columns.ts` 在「状态」前加「用户类型」列；`user/edit.vue` 表单在「状态」前加下拉（新增模式同样显示），保存 payload 携带 `is_super_admin`；`user/index.vue` 对超管行隐藏「分配角色」下拉操作；`api/system/user.ts` 类型补字段。

## 数据权限（br-server）

- **字段**：Course/Activity/StudyRoom/Coupon/Teacher 增加 `created_by: Mapped[uuid.UUID | None]`（nullable、index、无 FK——沿用 `Review.reviewed_by` 先例，避免 legacy-admin UUID(int=0) 外键问题）。单个 Alembic 迁移加 5 列，不回填。
- **归属规则**：
  - 内容型（上述 5 类）：按自身 `created_by` 过滤；座位随所属自习室（Seat 不加字段，按 room 归属过滤）；课时/排课子资源随课程页面入口，不在本次单独过滤。
  - 预约：课程订单（course_id 非空）随课程创建人；座位订单随自习室创建人（outerjoin courses + study_rooms 条件过滤）。
  - 评价：有 course_id 随课程；否则随订单所属自习室。
  - 认证/钱包流水/教育 listing：不过滤（用户确认）。
- **可见性**：`created_by IS NULL`（存量/legacy/测试）全员可见；非超管可见 `created_by == 自己 OR IS NULL`；超管（含 legacy token）不过滤。判定一律用 `context.is_super_admin`。
- **注入方式**：路由用参数依赖 `context: AdminContext | None = Depends(get_current_admin)`（沿用 admin_review.py 范式；测试 conftest override 为 None 时不过滤、创建人落 NULL）。创建时 `created_by = context.admin_id if context and context.admin_id.int != 0 else None`。
- **过滤实现**：service 列表/详情方法增加可选 `viewer: AdminContext | None` 参数，内部统一用一个小助手构造 `or_(created_by.is_(None), created_by == viewer.admin_id)` 条件；viewer 为 None 或超管时不加条件。
- **admin_course.py 无鉴权问题**：list/create/detail 路由补 `get_current_admin` 参数依赖（顺带补齐认证），不引入新权限码。
- **已知边界**：数据权限只约束查看（列表/详情）；更新/删除仍由功能权限码控制。认证等记录类数据对有菜单权限者全量可见。

## 测试

- 后端 pytest（内存 SQLite）：新增数据权限测试（普通管理员只见自己+存量、超管全量、创建人记录、预约/评价关联过滤、座位随教室）；用户类型测试（create/update/list 的 is_super_admin、超管清空角色）。
- 前端：`pnpm test:business-refactor` + `pnpm build`；独立 CDP Chrome 浏览器验收（角色页跳转/菜单树保存、用户类型列与下拉、超管隐藏分配角色）。