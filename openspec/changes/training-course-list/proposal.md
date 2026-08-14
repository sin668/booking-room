## Why

当前系统仅支持自习室预约（座位制），缺少培训课程浏览入口。业务需要扩展到培训领域，在 br-app 增加培训课程列表页面，让用户浏览培训室和分类课程。为此需要扩展现有 study_rooms 表增加 room_type 字段，区分自习室、培训室和综合室，并新建 Teacher 和 Course 模型支撑课程列表展示。

## What Changes

- **StudyRoom 模型扩展**：增加 `room_type` 字段（枚举：study / training / comprehensive），默认值 `study`，现有数据自动迁移为 `study`
- **现有自习室列表 API 修改**：`GET /api/v1/rooms` 响应增加 `room_type` 字段，支持 `room_type` 查询参数过滤
- **新建 Teacher 模型**：创建 `teachers` 表，包含教师姓名、头像、职称/头衔、评分等字段
- **新建 Course 模型**：包含课程名称、封面图、`teacher_id` 外键关联 teachers 表、分类（枚举值 primaryschool/middleschool/postgraduate/civil_service/language/skills/professional）、价格、评分、报名人数、所属培训室、排课时间、标签、状态等字段
- **新建培训室列表 API**：`GET /api/v1/training/rooms` 返回 `room_type` 为 `training` 或 `comprehensive` 的培训室列表，每间培训室附带热门推荐课程
- **新建课程列表 API**：`GET /api/v1/training/courses` 返回按分类过滤的课程列表，支持分页
- **新建培训课程列表页面**：br-app 新增 `pages/training/index.vue`，包含分类 TAB 切换（全部、小学辅导、中学辅导、公考备考、技能提升）、培训室卡片（可展开热门课程）、课程卡片列表、搜索栏 UI

## Capabilities

### New Capabilities

- `training-course-list-api`: 培训课程列表 API — 培训室列表接口（含热门推荐课程）、课程分类列表接口、Teacher 数据模型、Course 数据模型
- `training-course-list-ui`: 培训课程列表页面 — 分类 TAB 切换、培训室卡片展开/收起热门课程、课程卡片列表、搜索栏 UI

### Modified Capabilities

- `study-room-booking-api`: StudyRoom 模型增加 `room_type` 字段，自习室列表 API 响应增加 `room_type` 并支持按类型过滤

## Impact

**影响模块范围**：

- **br-server**（后端 API + 数据模型）:
  - `app/models/study_room.py` — 增加 room_type 字段
  - `app/models/teacher.py` — 新建 Teacher 模型
  - `app/models/course.py` — 新建 Course 模型（含 teacher_id 外键）
  - `app/schemas/study_room.py` — 响应 schema 增加 room_type
  - `app/schemas/teacher.py` — 新建教师 schema
  - `app/schemas/course.py` — 新建课程 schema（含 teacher 嵌套对象）
  - `app/services/study_room_service.py` — 列表查询支持 room_type 过滤
  - `app/services/training_service.py` — 新建培训服务
  - `app/api/routes/study_room.py` — 增加 room_type 查询参数
  - `app/api/routes/training.py` — 新建培训路由
  - `app/main.py` — 注册新路由
  - `alembic/versions/` — 新建迁移文件（增加 room_type 列 + 创建 teachers 表和 courses 表）
  - `app/services/seed_data.py` — 增加培训室、教师和课程种子数据
  - `tests/` — 新建培训相关测试
- **br-app**（微信小程序前端）:
  - `src/pages/training/index.vue` — 新建培训课程列表页
  - `src/api/training.js` — 新建培训 API 模块
  - `src/pages.json` — 注册新页面路由
  - `src/components/` — 新建培训室卡片和课程卡片组件
- **不涉及 br-admin**

**回滚方案**：

1. 数据库层：`alembic downgrade -1` 回滚迁移（删除 room_type 列、courses 表和 teachers 表）
2. 后端代码：`git revert` 恢复修改文件，删除新增文件（teacher.py、course.py、training_service.py、training.py 等）
3. 前端代码：删除 `pages/training/` 目录和 `api/training.js`，恢复 `pages.json`
4. 种子数据：回滚迁移会自动删除新增的培训室、教师和课程数据
