# Design: admin-teacher-management

## 数据模型

### teachers 表扩展（全部可空/带默认值，兼容存量数据）

| 字段 | 类型 | 说明 |
|------|------|------|
| specialty | String(50) NULL | 专业方向，如"考研政治" |
| teaching_years | Integer default 0 | 教龄（年） |
| education | String(20) NULL | 学历：本科/硕士/博士 |
| school | String(100) NULL | 毕业院校 |
| status | String(20) default 'active' | active 在职 / inactive 停用 |
| teaching_tags | String(500) NULL | 教学特色标签，逗号分隔（沿用 courses.tags 模式） |
| qualifications | JSON NULL | 资质认证列表 `[{"name","sub"}]`（沿用 study_rooms.environment_images JSON 模式） |

### teacher_rooms 关联表（新）

```
teacher_rooms: id PK, teacher_id FK->teachers.id ON DELETE CASCADE,
               room_id FK->study_rooms.id ON DELETE CASCADE,
               created_at, UniqueConstraint(teacher_id, room_id)
```

写入时服务端校验 room.room_type ∈ ('training', 'comprehensive')。

## API

### 管理端 `/api/v1/admin/teachers`（重写 admin_teacher.py，带 require_admin_permission）

| 方法 | 路径 | 权限 | 说明 |
|------|------|------|------|
| GET | `` | teacher:view | 分页列表，keyword 模糊搜索；响应 `{items, total, page, page_size}`，items 保留 id/name/avatar/title（兼容排课下拉），附加 specialty/teaching_years/education/school/status/rating/student_count/course_count |
| GET | `/{teacher_id}` | teacher:view | 详情（含 room_ids、qualifications、teaching_tags 列表） |
| POST | `` | teacher:create | 新增 |
| PUT | `/{teacher_id}` | teacher:update | 编辑（room_ids 全量覆盖） |
| DELETE | `/{teacher_id}` | teacher:delete | 删除；存在关联排课时返回 400 拒绝删除，否则级联清理 teacher_rooms 后删除 |
| PATCH | `/{teacher_id}/status` | teacher:status | 停用/启用，body `{status}` |

course_count 由 course_schedules 按 teacher_id 去重 course_id 计数（outerjoin 防空）。

### C 端 `GET /api/v1/teachers/{teacher_id}`

TeacherDetailResponse 增加：specialty、teaching_years、education、school、status、teaching_tags: list[str]、qualifications: list[dict]、rooms: [{id, name}]。仅 status=active 的老师对 C 端可见（停用返回 404），避免 C 端看到停用老师。

## br-admin

- `src/api/teacher/index.ts`：类型 + CRUD 封装，GET 一律 `force: true`（BUG-25）
- `src/views/training/teachers/index.vue`：BasicForm（keyword）+ BasicTable，列：老师（头像+姓名+学历·院校）、专业方向、教龄、学员数、评分、状态 tag、操作（编辑/停用启用/删除，TableAction，删除带确认弹窗与防重复）
- `src/views/training/teachers/edit.vue`：复刻 courses/edit.vue 页面结构——顶部返回+保存栏，卡片式区块：基本信息（姓名*/职称/专业方向/教龄/学历/毕业院校）、头像上传、个人简介、资质认证（动态行 name+sub，增删）、教学特色标签（最多5个，弹窗输入）、所属房间（n-select multiple，选项来自 `GET /v1/admin/rooms?room_type=training|comprehensive`，需两次请求合并或传 room_type 分别拉取——admin_study_room 列表接口 room_type 只支持单值，故分别请求 training 与 comprehensive 再合并）
- 路由：`router/modules/training.ts` 增加 `teachers`（列表，name: training_teachers）与 `teachers/edit/:id?`（name: training_teacher_edit, hideInMenu: true, activeMenu: training_teachers）
- 保存/返回遵循页面跳转模式：导航移出 try/catch，tab 用 splice 清理，fallback 用 `router.push('/training/teachers')` 路径跳转避免 BACK 模式动态路由 name 不一致

## seed_admin.py

```
MenuSeed("training.teachers", "menu", "老师管理", "training:teachers:view", "teachers",
         "TrainingTeachers", "/training/teachers/index", None, "TeamOutlined", 48, parent="training")
MenuSeed("training.teacher_edit", "menu", "编辑老师", "training:teachers:edit", "teachers/edit/:id?",
         "TrainingTeacherEdit", "/training/teachers/edit/index", None, "TeamOutlined", 49, hidden=True, parent="training")
```

目录菜单 path 已是基路径 `/training`，无需改动（BUG-19/24 模式）。按钮种子：teacher:view/create/update/delete/status。TeamOutlined 已在 icons.ts 注册（BUG-19 已修复）。

## br-app profile.vue

- hero 副标题改为 `专业方向 · N年教龄 · 学历`（字段缺失时跳过拼接段）
- 资质认证、教学特色改为读取接口 qualifications/teaching_tags；为空则隐藏对应区块
- 学员评价无库表支撑，保留占位但标注；统计行授课课程数沿用 courses.length
- 规避 BUG-14/20：不改生命周期导入方式，不使用 HTML 实体

## 迁移

新增 alembic revision（down_revision = `c2d3e4f5a6b7`），add_column 七个字段 + create_table teacher_rooms；downgrade 反向。revision id 避免与现有冲突（BUG：revision ID 冲突导致循环依赖）。
