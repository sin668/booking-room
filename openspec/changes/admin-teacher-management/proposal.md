# Proposal: admin-teacher-management

## Why

老师管理目前仅有极简的 teachers 表（name/avatar/title/rating/bio/student_count），后台没有老师管理界面，只能作为排课下拉数据源；br-app 教师简介页的资质认证、教学特色等为静态占位数据。需要按高保真原型 `prototype/admin-teachers.html` 与 `prototype/teacher-profile.html` 完善老师数据模型与管理能力。

## What Changes

1. **br-server 数据模型扩展**
   - teachers 表新增字段：`specialty`（专业方向）、`teaching_years`（教龄）、`education`（学历）、`school`（毕业院校）、`status`（在职 active/停用 inactive）、`teaching_tags`（教学特色标签，逗号分隔）、`qualifications`（资质认证，JSON）
   - 新增 `teacher_rooms` 关联表，支持老师多选所属培训室/综合室（room_type ∈ training|comprehensive）
   - 生成 Alembic 迁移
2. **br-server 管理端 API**
   - 扩展 `/api/v1/admin/teachers` 为完整 CRUD（列表分页/详情/新增/编辑/删除/停用启用），带 `require_admin_permission` 权限
   - 保持列表接口响应结构向后兼容（现有排课老师下拉依赖 items 中的 id/name/avatar/title）
   - C 端 `GET /api/v1/teachers/{teacher_id}` 扩展返回新字段与所属房间
3. **br-admin 老师管理**
   - 新增培训管理 > 老师管理列表页（参考原型：搜索、统计卡片可选做、表格列：老师/专业方向/教龄/学员数/评分/状态/操作），复用 BasicTable/BasicForm 等现有组件
   - 新增/编辑老师采用页面跳转模式（参考培训课程 courses/edit.vue 布局）：基本信息、头像上传、个人简介、资质认证、教学特色标签、多选所属培训室/综合室
   - 后端 seed 菜单与按钮权限、前端静态路由（hideInMenu 编辑页）
4. **br-app 教师简介页**
   - `pages/teacher/profile.vue` 移除静态占位，资质认证/教学特色/副标题（专业方向·教龄·学历）全部读取 br-server 库表数据

## Impact

- Affected specs: 新增 `admin-teacher-management`（ADDED Requirements）
- br-server: models/teacher.py、models/teacher_room.py（新）、schemas、services、routes/admin_teacher.py、routes/teacher.py、seed_admin.py、alembic 迁移、tests
- br-admin: views/training/teachers/（新）、api/teacher（新）、router/modules/training.ts、router/icons.ts（如需新图标）
- br-app: pages/teacher/profile.vue

## 约束（来自用户与 bug-fixed.md）

- 不创建 git 分支/worktree，直接在 main 实现验证，最后提交 GitHub
- 规避历史 BUG：菜单 path 用基路径（BUG-19/24）、Naive UI 组件须在 naive.ts 注册（BUG-23）、隐藏编辑页用 hideInMenu（记忆）、路由无尾部斜杠（BUG-22）、Alova GET 加 force（BUG-25）、关联查询用 outerjoin、删除防重复（幂等）
