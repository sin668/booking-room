# Comet Design Handoff

- Change: training-course-list
- Phase: design
- Mode: compact
- Context hash: a1d471d8c8813e94aeef84d6f9c34b514762960f33b48ad3fd7553dbfd9674d3

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/training-course-list/proposal.md

- Source: openspec/changes/training-course-list/proposal.md
- Lines: 1-57
- SHA256: d2b749a702450d41d82ea3a6ed076e85aea5bb83ae1719d34e385c25f316e6a7

```md
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

```

## openspec/changes/training-course-list/design.md

- Source: openspec/changes/training-course-list/design.md
- Lines: 1-153
- SHA256: 9cbd75517a8f3aa2e14ba1bc49d9012b3a007ce7a42d8fceb691603722d82d26

[TRUNCATED]

```md
## Context

现有 `study_rooms` 表仅服务于自习室座位预约系统。本变更需要扩展该表增加 `room_type` 字段以区分自习室、培训室和综合室，新建 `teachers` 表和 `courses` 表支撑培训课程列表展示。前端在 br-app 新增培训课程列表页面，参考 `prototype/training.html` 高保真原型图。参见 proposal.md 了解动机。

## Goals / Non-Goals

**Goals:**

- 数据库层：`study_rooms` 表增加 `room_type` 列（枚举，默认 study），新建 `teachers` 表和 `courses` 表（courses 通过 `teacher_id` 外键关联 teachers）
- 后端 API：现有自习室列表 API 支持 room_type 过滤；新建培训室列表和课程列表两个接口
- 前端页面：实现培训课程列表页面，包含分类 TAB 切换、培训室卡片（可展开热门课程）、课程卡片列表、搜索栏 UI
- 现有自习室预约功能不受影响

**Non-Goals:**

- 不实现培训室详情页和课程详情页（training-room.html、course-detail.html）
- 不实现 Admin 后台管理功能（br-admin）
- 不实现课程预约/下单/支付功能
- 不实现后端搜索 API（搜索栏仅前端 UI 展示）
- 不实现教师详情页或教师管理功能（仅创建 teachers 表供 courses 关联）

## Decisions

### 1. room_type 使用字符串枚举而非独立类型表

**选择**：在 `study_rooms` 表增加 `room_type` VARCHAR(20) 列，枚举值为 study / training / comprehensive，默认 study。

**理由**：三种类型是固定枚举，不会频繁增加新类型。使用字符串字段比独立类型表更简单，避免多表 JOIN 开销。现有数据迁移只需设置默认值 study。

**备选方案**：创建独立的 `room_types` 表，通过外键关联。被否决因为类型数量固定且少，独立表增加不必要的复杂度。

### 2. 创建独立 Teacher 表，courses 通过 teacher_id 外键关联

**选择**：创建 `teachers` 表（id, name, avatar, title, rating, created_at, updated_at），`courses` 表通过 `teacher_id` 外键关联 `teachers.id`，不再在 courses 表中存储教师姓名和头像。

**理由**：教师是独立实体，一位教师可讲授多门课程。独立表避免数据冗余（同一教师姓名/头像在多门课程中重复），支持后续教师详情页、教师管理等功能扩展。课程列表通过 JOIN 获取教师信息，性能开销可接受。

**备选方案**：在 courses 表中直接存储 teacher_name 和 teacher_avatar 字段。被否决因为数据冗余，且后续扩展教师功能时需要数据迁移。

### 3. 课程分类使用字符串枚举而非分类表

**选择**：`courses.category` 使用 VARCHAR(30) 枚举字段，值为 primaryschool / middleschool / postgraduate / civil_service / language / skills / professional。

**理由**：分类数量固定且少（7 个枚举值），使用枚举字段足够。本次前端 TAB 先放置 5 个：全部、小学辅导（primaryschool）、中学辅导（middleschool）、公考备考（civil_service）、技能提升（skills），剩余分类（postgraduate/language/professional）后续按需添加 TAB。

**备选方案**：创建 `course_categories` 表。被否决因为分类数量固定且少。

### 4. 培训室列表 API 独立路由前缀

**选择**：新建 `GET /api/v1/training/rooms` 和 `GET /api/v1/training/courses`，使用独立 `/training/` 前缀。

**理由**：培训相关接口是新的业务领域，独立前缀有利于后续扩展（培训室详情、课程详情、预约等）。与现有 `/api/v1/rooms` 区分清晰，避免在现有接口上叠加过多参数。

**备选方案**：在现有 `/api/v1/rooms` 接口增加参数区分培训室和自习室。被否决因为职责不清，且培训室需要附带热门课程数据，响应结构不同。

### 5. 热门课程通过子查询附带返回

**选择**：培训室列表接口中，每个培训室附带最多 3 条 `is_hot=true` 的课程（`hot_courses` 字段）。

**理由**：原型图"全部"TAB 中培训室卡片可展开显示热门课程，一次请求获取所有数据减少前端请求次数。使用子查询限制每间培训室最多 3 条，避免数据量过大。

**备选方案**：前端先请求培训室列表，再为每间培训室单独请求热门课程。被否决因为 N+1 请求问题，用户体验差。

### 6. 综合室在两个列表中都出现

**选择**：room_type 为 comprehensive 的综合室同时出现在自习室列表（`GET /api/v1/rooms`）和培训室列表（`GET /api/v1/training/rooms`）中。

**理由**：综合室可同时作为自习室和培训室使用，需要在两个列表中都可见。用户可以通过自习室列表预约座位，也可以通过培训室列表查看课程。

### 7. 前端页面使用 uni-app 页面组件

**选择**：在 `br-app/src/pages/training/` 目录新建 `index.vue` 页面，使用 Vue3 Composition API + `<script setup>` 语法。

**理由**：遵循 br-app 现有页面结构惯例（如 `pages/booking/detail.vue`、`pages/study-record/index.vue`）。uni-app 框架要求页面放在 `pages/` 目录下并在 `pages.json` 注册。

**注意**：根据 bug-fixed.md BUG-14，`onMounted` 等 Vue 3 生命周期钩子必须从 `vue` 包导入，不能从 `@dcloudio/uni-app` 导入。`onLoad`、`onShow` 等 uni-app 页面钩子从 `@dcloudio/uni-app` 导入。

## Risks / Trade-offs

- **[数据库迁移风险]** → study_rooms 表已有数据，增加 room_type 列需设置安全默认值。迁移脚本使用 `server_default='study'` 确保现有数据自动获得 study 类型。

```

Full source: openspec/changes/training-course-list/design.md

## openspec/changes/training-course-list/tasks.md

- Source: openspec/changes/training-course-list/tasks.md
- Lines: 1-72
- SHA256: 07147e16d190906b8e5a0c9e8f3178dc337313afbc49224a8be8cd3924a821c4

```md
## 1. 数据库迁移与模型

- [ ] 1.1 创建 Alembic 迁移文件：`study_rooms` 表增加 `room_type` 列（VARCHAR(20), server_default='study', nullable=False），同一迁移中创建 `teachers` 表和 `courses` 表（courses 含 teacher_id 外键关联 teachers.id，参照 specs/training-course-list-api Teacher/Course database model）
- [ ] 1.2 更新 `br-server/app/models/study_room.py`：增加 `room_type` 字段（Mapped[str], default="study"）
- [ ] 1.3 创建 `br-server/app/models/teacher.py`：定义 Teacher 模型（name, avatar, title, rating, created_at, updated_at）
- [ ] 1.4 创建 `br-server/app/models/course.py`：定义 Course 模型（room_id FK, teacher_id FK→teachers.id 可空, name, cover_image, category, price, rating, enrollment_count, schedule, tags, status, is_hot, sort_order, created_at, updated_at）
- [ ] 1.5 在 `br-server/app/models/__init__.py` 注册 Teacher 和 Course 模型导出
- [ ] 1.6 执行 `alembic upgrade head` 并验证迁移成功

## 2. 后端 Schema

- [ ] 2.1 更新 `br-server/app/schemas/study_room.py`：StudyRoomResponse 增加 `room_type` 字段；RoomCreate/RoomUpdate 增加 `room_type` 可选字段
- [ ] 2.2 创建 `br-server/app/schemas/teacher.py`：定义 TeacherResponse（id, name, avatar, title, rating）
- [ ] 2.3 创建 `br-server/app/schemas/course.py`：定义 CourseResponse（含 teacher 嵌套对象、tags 数组解析）、CourseListResponse、TrainingRoomResponse（含 hot_courses，hot_courses 中每条含 teacher 嵌套对象）、TrainingRoomListResponse

## 3. 后端 Service

- [ ] 3.1 更新 `br-server/app/services/study_room_service.py`：`list_study_rooms` 和 `admin_list_rooms` 支持 `room_type` 过滤参数
- [ ] 3.2 创建 `br-server/app/services/training_service.py`：实现 `list_training_rooms`（查询 room_type in [training, comprehensive]，附带热门课程，JOIN teachers 获取教师信息）和 `list_courses`（按 category 过滤，JOIN study_rooms 获取 room_name，JOIN teachers 获取教师信息）
- [ ] 3.3 更新 `br-server/app/services/seed_data.py`：增加 3 间培训室（room_type=training）和 1 间综合室（room_type=comprehensive），约 5 位教师数据，以及约 10 条课程数据覆盖 primaryschool/middleschool/civil_service/skills 分类

## 4. 后端 API Routes

- [ ] 4.1 更新 `br-server/app/api/routes/study_room.py`：list_study_rooms 增加 `room_type` 查询参数（Query(None, pattern="^(study|training|comprehensive)$")）
- [ ] 4.2 创建 `br-server/app/api/routes/training.py`：GET /api/v1/training/rooms（培训室列表）和 GET /api/v1/training/courses（课程列表），**注意：路由定义不得使用尾部斜杠（参考 bug-fixed.md BUG-22）**
- [ ] 4.3 在 `br-server/app/main.py` 注册 training_router

## 5. 后端测试

- [ ] 5.1 创建 `br-server/tests/test_training_api.py`：测试培训室列表（默认分页、城市过滤、综合室出现、自习室排除、热门课程附带含教师信息）、课程列表（分类过滤、分页、tags 解析、teacher 嵌套对象）
- [ ] 5.2 更新 `br-server/tests/test_api_homepage.py` 或 `test_admin_room_routes.py`：增加 room_type 过滤和响应字段验证
- [ ] 5.3 运行 `pytest tests/ -q` 确保全部测试通过

## 6. 前端 API 模块

- [ ] 6.1 创建 `br-app/src/api/training.js`：封装 getTrainingRooms(params) 和 getTrainingCourses(params) 接口调用

## 7. 前端页面实现

- [ ] 7.1 创建 `br-app/src/pages/training/index.vue` 页面骨架（参考 prototype/training.html 高保真原型图，保持配色 #4F6EF7、背景 #F5F6FA、卡片 rounded-2xl shadow-sm）
- [ ] 7.2 实现搜索栏 UI（placeholder "搜索课程、老师"，纯展示不触发后端请求）
- [ ] 7.3 实现分类 TAB 栏（全部 + 小学辅导/中学辅导/公考备考/技能提升，横向滚动，选中高亮下划线。各 TAB 对应 category 值：小学辅导=primaryschool、中学辅导=middleschool、公考备考=civil_service、技能提升=skills）
- [ ] 7.4 实现"全部"TAB 培训室卡片列表（封面图、名称、营业状态、评分、地址、设施标签、可展开热门课程）
- [ ] 7.5 实现培训室卡片展开/收起热门课程（max-height 过渡动画，展开图标旋转）
- [ ] 7.6 实现分类 TAB 课程卡片列表（封面图、名称、状态标签、教师信息、所属培训室、评分、报名人数、价格、预约按钮）
- [ ] 7.7 实现加载状态和空状态提示（"暂无培训室"/"暂无课程"）
- [ ] 7.8 在 `br-app/src/pages.json` 注册培训页面路由（pages/training/index）
- [ ] 7.9 **注意：Vue3 生命周期钩子（onMounted 等）从 `vue` 包导入，不能从 `@dcloudio/uni-app` 导入（参考 bug-fixed.md BUG-14）**
- [ ] 7.10 **注意：避免在 Vue 模板中使用 `&lt;` 和 `&gt;` HTML 实体，使用 Unicode 字符（参考 bug-fixed.md BUG-20）**

## 8. 前端底部导航

- [ ] 8.1 在底部导航栏（tabBar 或自定义组件）增加"培训"入口，图标使用 graduation-cap，点击导航到 pages/training/index

## 9. 代码审查与重构

- [ ] 9.1 确保后端 Clean Architecture 分层：routes 仅处理 HTTP → services 处理业务逻辑 → models 定义数据 → schemas 定义响应
- [ ] 9.2 消除重复代码：room_type 枚举值和 category 枚举值提取为常量复用
- [ ] 9.3 确保前端组件分层：页面调用 api 模块，api 模块调用 utils/request.js
- [ ] 9.4 检查所有新路由无尾部斜杠，现有路由风格一致

## 10. API 文档更新

- [ ] 10.1 在 `docs/api.md` 补充 `GET /api/v1/training/rooms` 接口文档（路径、参数、响应示例）
- [ ] 10.2 在 `docs/api.md` 补充 `GET /api/v1/training/courses` 接口文档
- [ ] 10.3 更新 `docs/api.md` 中 `GET /api/v1/rooms` 接口文档，增加 `room_type` 查询参数和响应字段说明

## 11. 最终验证

- [ ] 11.1 运行后端全部测试：`conda activate booking-room && cd br-server && pytest tests/ -q`
- [ ] 11.2 前端构建验证：`nvm use v22.22.0 && cd br-app && npm run build`
- [ ] 11.3 验证现有自习室预约功能不受影响

```

## openspec/changes/training-course-list/specs/study-room-booking-api/spec.md

- Source: openspec/changes/training-course-list/specs/study-room-booking-api/spec.md
- Lines: 1-53
- SHA256: ea775d4af8cabf3b7ccff67a136ba6d77541f137305847aea57d0bdd6cee4f56

```md
## MODIFIED Requirements

### Requirement: List study rooms API
系统 SHALL 提供 `GET /api/v1/rooms` 接口，返回自习室分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`city_id`（可选，整数，按城市过滤）、`room_type`（可选，枚举值 "study"/"training"/"comprehensive"，按房间类型过滤）。仅返回 `status=open` 的房间。当 `city_id` 为空时返回全部城市的房间。当 `room_type` 为空时返回全部类型的房间。响应中每个 item SHALL 包含 `room_type` 字段。

#### Scenario: Successful list request with default pagination
- **WHEN** 客户端发送 `GET /api/v1/rooms` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（房间数组）和 `total`、`page`、`page_size` 字段，`page_size` 默认为 10，返回全部类型的房间

#### Scenario: List request with custom page size
- **WHEN** 客户端发送 `GET /api/v1/rooms?page=2&page_size=5`
- **THEN** 返回 HTTP 200，`page` 为 2，`page_size` 为 5，`items` 包含第 2 页的 5 条记录

#### Scenario: Page size exceeds maximum
- **WHEN** 客户端发送 `GET /api/v1/rooms?page_size=100`
- **THEN** 返回 HTTP 200，`page_size` 被限制为最大值 50

#### Scenario: Filter rooms by city
- **WHEN** 客户端发送 `GET /api/v1/rooms?city_id=1`
- **THEN** 返回 HTTP 200，`items` 仅包含 `city_id=1` 的房间

#### Scenario: Filter by non-existent city
- **WHEN** 客户端发送 `GET /api/v1/rooms?city_id=999`（不存在或 inactive 的城市）
- **THEN** 返回 HTTP 200，`items` 为空数组，`total` 为 0

#### Scenario: Filter rooms by room_type
- **WHEN** 客户端发送 `GET /api/v1/rooms?room_type=study`
- **THEN** 返回 HTTP 200，`items` 仅包含 `room_type=study` 的自习室

#### Scenario: Filter rooms by training type
- **WHEN** 客户端发送 `GET /api/v1/rooms?room_type=training`
- **THEN** 返回 HTTP 200，`items` 仅包含 `room_type=training` 的培训室

#### Scenario: Response includes room_type field
- **GIVEN** 房间列表有数据
- **WHEN** 客户端发送 `GET /api/v1/rooms`
- **THEN** 每个 item 包含 `room_type` 字段，值为 "study"、"training" 或 "comprehensive"

### Requirement: Study room response schema
自习室列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`name`（字符串）、`description`（字符串，可空）、`cover_image`（字符串 URL）、`address`（字符串）、`business_hours`（字符串，如 "08:00-22:00"）、`status`（枚举 "open"/"closed"）、`room_type`（枚举 "study"/"training"/"comprehensive"）、`min_price`（数字，单位元）、`city_id`（整数或 null）、`city_name`（字符串或 null，城市名称）。

#### Scenario: Response field validation
- **WHEN** 客户端请求自习室列表
- **THEN** 每个 item 包含 `id`、`name`、`description`、`cover_image`、`address`、`business_hours`、`status`、`room_type`、`min_price`、`city_id`、`city_name` 字段，类型符合规范

#### Scenario: Room without city
- **WHEN** 客户端请求包含 `city_id=null` 的自习室
- **THEN** 该 item 的 `city_id` 为 null，`city_name` 为 null

#### Scenario: Room type field values
- **GIVEN** 存在 room_type 分别为 study、training、comprehensive 的房间
- **WHEN** 客户端请求房间列表
- **THEN** 每个 item 的 `room_type` 字段为 "study"、"training" 或 "comprehensive" 之一

```

## openspec/changes/training-course-list/specs/training-course-list-api/spec.md

- Source: openspec/changes/training-course-list/specs/training-course-list-api/spec.md
- Lines: 1-142
- SHA256: 61854c95ab6528c1de71f6e5b3fc75ed9c47257bcc463a3f72cae7662e7db59d

[TRUNCATED]

```md
## Purpose

培训课程列表 API 提供培训室列表和分类课程列表的查询接口，支撑 br-app 培训课程列表页面的数据展示，包括培训室附带的热门推荐课程。

## ADDED Requirements

### Requirement: Teacher database model

系统 SHALL 创建 `teachers` 表，包含字段：`id`（主键，自增）、`name`（VARCHAR(50)，教师姓名，非空）、`avatar`（VARCHAR(512)，教师头像 URL，可空）、`title`（VARCHAR(50)，职称/头衔，可空，如 "考研政治 · 8年教龄"）、`rating`（DECIMAL(3,1)，评分，默认 0.0）、`created_at`、`updated_at`。

#### Scenario: Create teacher record

- **GIVEN** 管理员创建一位教师
- **WHEN** 向 `teachers` 表插入一条记录，`name="李明华"`，`title="考研政治 · 8年教龄"`
- **THEN** 记录成功创建，`id` 自增，`rating` 默认为 0.0

#### Scenario: Teacher with avatar

- **GIVEN** 管理员创建一位教师并设置头像
- **WHEN** 向 `teachers` 表插入 `name="陈雅琪"`，`avatar="https://example.com/avatar.jpg"`
- **THEN** 记录成功创建，`avatar` 字段存储头像 URL

### Requirement: Course database model

系统 SHALL 创建 `courses` 表，包含字段：`id`（主键，自增）、`room_id`（外键关联 study_rooms.id，非空，表示所属培训室）、`teacher_id`（外键关联 teachers.id，可空，表示授课教师）、`name`（VARCHAR(100)，课程名称，非空）、`cover_image`（VARCHAR(512)，封面图 URL，可空）、`category`（VARCHAR(30)，课程分类，非空，枚举值 "primaryschool"/"middleschool"/"postgraduate"/"civil_service"/"language"/"skills"/"professional"）、`price`（DECIMAL(10,2)，每课时价格，非空）、`rating`（DECIMAL(3,1)，评分，默认 0.0）、`enrollment_count`（INTEGER，报名人数，默认 0）、`schedule`（VARCHAR(200)，排课时间描述，可空）、`tags`（VARCHAR(200)，标签逗号分隔，可空）、`status`（VARCHAR(20)，默认 "active"，枚举值 "active"/"inactive"）、`is_hot`（BOOLEAN，是否热门推荐，默认 false）、`sort_order`（INTEGER，排序权重，默认 0）、`created_at`、`updated_at`。

#### Scenario: Create course record

- **GIVEN** 管理员已创建一间 room_type 为 training 的培训室和一位教师
- **WHEN** 向 `courses` 表插入一条记录，`room_id=1`，`teacher_id=1`，`name="考研政治冲刺班"`，`category="postgraduate"`，`price=80.00`
- **THEN** 记录成功创建，`id` 自增，`status` 默认为 "active"，`rating` 默认为 0.0，`enrollment_count` 默认为 0，`is_hot` 默认为 false

#### Scenario: Course belongs to training room

- **GIVEN** 一间 room_type 为 study 的自习室，id=1
- **WHEN** 向 `courses` 表插入 `room_id=1` 的记录
- **THEN** 记录成功创建（数据库层不强制 room_type 校验，由应用层控制）

#### Scenario: Course without teacher

- **GIVEN** 管理员已创建一间培训室但尚未创建教师
- **WHEN** 向 `courses` 表插入 `room_id=1`，`teacher_id=null`，`name="自习辅导"`，`category="skills"`，`price=30.00`
- **THEN** 记录成功创建，`teacher_id` 为 null

### Requirement: List training rooms API

系统 SHALL 提供 `GET /api/v1/training/rooms` 接口，返回 `room_type` 为 `training` 或 `comprehensive` 的培训室分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`city_id`（可选）。仅返回 `status=open` 的培训室。每个培训室附带最多 3 条 `is_hot=true` 的热门推荐课程。

#### Scenario: Successful list request with default pagination

- **WHEN** 客户端发送 `GET /api/v1/training/rooms` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（培训室数组）和 `total`、`page`、`page_size` 字段，`page_size` 默认为 10

#### Scenario: Training rooms include hot courses

- **GIVEN** 培训室 id=1 有 5 门 `is_hot=true` 的课程
- **WHEN** 客户端发送 `GET /api/v1/training/rooms`
- **THEN** 返回的培训室 item 中 `hot_courses` 字段包含最多 3 条热门课程

#### Scenario: Filter training rooms by city

- **WHEN** 客户端发送 `GET /api/v1/training/rooms?city_id=1`
- **THEN** 返回 HTTP 200，`items` 仅包含 `city_id=1` 的培训室

#### Scenario: Comprehensive room appears in training list

- **GIVEN** 一间 room_type 为 comprehensive 的综合室，status=open
- **WHEN** 客户端发送 `GET /api/v1/training/rooms`
- **THEN** 该综合室出现在返回结果中

#### Scenario: Study room excluded from training list

- **GIVEN** 一间 room_type 为 study 的自习室，status=open
- **WHEN** 客户端发送 `GET /api/v1/training/rooms`
- **THEN** 该自习室不出现在返回结果中

### Requirement: List training courses API

系统 SHALL 提供 `GET /api/v1/training/courses` 接口，返回按分类过滤的课程分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`category`（可选，枚举值 "primaryschool"/"middleschool"/"postgraduate"/"civil_service"/"language"/"skills"/"professional"）。仅返回 `status=active` 的课程。当 `category` 为空时返回全部分类的课程。


```

Full source: openspec/changes/training-course-list/specs/training-course-list-api/spec.md

## openspec/changes/training-course-list/specs/training-course-list-ui/spec.md

- Source: openspec/changes/training-course-list/specs/training-course-list-ui/spec.md
- Lines: 1-119
- SHA256: c9ffa0c9a94945b37e3a0d5046f8acdce56046b883efdfd6a0bbfe57d730cf2e

[TRUNCATED]

```md
## Purpose

培训课程列表页面提供培训室浏览和分类课程查看功能，用户可切换分类 TAB 查看不同类型的课程列表，在"全部"TAB 查看培训室列表及其热门推荐课程。

## ADDED Requirements

### Requirement: Training course list page entry

系统 SHALL 在 br-app 底部导航栏增加"培训"入口，点击后导航到培训课程列表页面 `pages/training/index`。页面参考 `prototype/training.html` 高保真原型图，保持总体风格一致。

#### Scenario: Navigate to training page

- **GIVEN** 用户在 br-app 首页
- **WHEN** 用户点击底部导航栏"培训"入口
- **THEN** 导航到培训课程列表页面，默认显示"全部"TAB 的培训室列表

### Requirement: Category tab switching

培训课程列表页面 SHALL 显示横向滚动的分类 TAB 栏，包含"全部"和 4 个分类标签（小学辅导、中学辅导、公考备考、技能提升）。默认选中"全部"TAB。点击不同 TAB 时切换显示内容。各 TAB 对应的 category 枚举值：小学辅导=primaryschool、中学辅导=middleschool、公考备考=civil_service、技能提升=skills。

#### Scenario: Default tab is all

- **GIVEN** 用户刚进入培训课程列表页面
- **WHEN** 页面加载完成
- **THEN** "全部"TAB 处于选中状态，页面显示培训室列表

#### Scenario: Switch to category tab

- **GIVEN** 用户在"全部"TAB
- **WHEN** 用户点击"小学辅导"TAB
- **THEN** "小学辅导"TAB 处于选中状态，页面切换为 category=primaryschool 的课程列表

#### Scenario: Switch back to all tab

- **GIVEN** 用户在"小学辅导"TAB
- **WHEN** 用户点击"全部"TAB
- **THEN** "全部"TAB 处于选中状态，页面切换回培训室列表

### Requirement: Training room card with expandable courses

"全部"TAB 的培训室列表 SHALL 显示培训室卡片。每张卡片包含培训室封面图、名称、营业状态标签、评分、距离、地址、设施标签和"热门推荐课程"展开按钮。点击卡片可跳转到培训室详情页（详情页不在本次范围内，预留跳转入口）。点击"热门推荐课程"展开按钮可展开/收起热门课程列表。

#### Scenario: Display training room card

- **GIVEN** 培训室列表有数据
- **WHEN** 用户在"全部"TAB
- **THEN** 显示培训室卡片列表，每张卡片包含封面图、名称、营业状态、评分、地址、设施标签

#### Scenario: Expand hot courses

- **GIVEN** 培训室卡片处于收起状态
- **WHEN** 用户点击"热门推荐课程"展开按钮
- **THEN** 卡片下方展开热门课程列表，展开图标旋转 180 度

#### Scenario: Collapse hot courses

- **GIVEN** 培训室卡片处于展开状态
- **WHEN** 用户再次点击"热门推荐课程"展开按钮
- **THEN** 热门课程列表收起，展开图标恢复原位

#### Scenario: Hot course item display

- **GIVEN** 培训室卡片已展开，有热门课程数据
- **WHEN** 用户查看展开的课程列表
- **THEN** 每条课程显示封面图、课程名称、教师姓名、报名人数和价格

### Requirement: Course card display

分类 TAB 的课程列表 SHALL 显示课程卡片。每张卡片包含课程封面图、名称、状态标签（热销/新课/名师/推荐）、教师头像和姓名、所属培训室名称、评分、报名人数、价格（/课时）和"预约"按钮。点击课程卡片预留跳转到课程详情页（不在本次范围内）。

#### Scenario: Display course card

- **GIVEN** 分类课程列表有数据
- **WHEN** 用户在某个分类 TAB
- **THEN** 显示课程卡片列表，每张卡片包含封面图、名称、状态标签、教师信息、所属培训室、评分、报名人数、价格和预约按钮

#### Scenario: Course card without status tag

- **GIVEN** 课程没有特殊状态标签
- **WHEN** 用户查看课程卡片

```

Full source: openspec/changes/training-course-list/specs/training-course-list-ui/spec.md
