# Tasks: role-page-user-type-data-scope

- [x] 1. 后端用户类型：AdminUserListItem/Create/Update 暴露 is_super_admin，create/update 生效，设超管清空角色关联
- [x] 2. 后端角色详情：GET /api/v1/admin/roles/{role_id}（system:role:view 权限）
- [x] 3. 后端数据权限基础：5 张内容表模型加 created_by + Alembic 迁移；内容创建接口记录创建人
- [x] 4. 后端数据权限过滤：内容型列表/详情按创建人过滤（座位随教室）；预约/评价随关联内容归属；admin_course 补鉴权上下文
- [x] 5. 前端角色页：新增 role/edit.vue（基本信息+菜单权限树）与路由；role.vue 去菜单权限按钮改跳转；删除废弃弹窗组件
- [x] 6. 前端用户类型：列表用户类型列、编辑页用户类型下拉（状态前）、超管隐藏分配角色、API 类型补字段
- [x] 7. 后端测试：数据权限与用户类型 pytest 用例通过，既有测试不回归
- [x] 8. 前端验证：test:business-refactor + build 通过；CDP 浏览器验收角色页/用户类型/数据权限核心场景