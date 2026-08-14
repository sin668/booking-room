# Comet Design Handoff

- Change: training-room-overview
- Phase: design
- Mode: compact
- Context hash: a179c32c141dd55921de77c1a38f1b509953630af29c7a4998af2c6f9c5e6048

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/training-room-overview/proposal.md

- Source: openspec/changes/training-room-overview/proposal.md
- Lines: 1-46
- SHA256: 2bd1545a4f80b4245953e6b60d7b2c1efad4ec1131733ec392ad187151ea3496

```md
## Why

当前自习室详情页（`pages/booking/detail.vue`）仅服务于自习室座位预约场景。随着 `training-course-list` change 引入 `room_type` 字段（study/training/comprehensive），系统已能区分三种房间类型，但详情页尚未根据类型展示差异化内容。培训室和综合室需要展示教室概况、名师团队和课程列表，且底部操作按钮需根据类型调整。参考 `prototype/training-room.html` 高保真原型图，在现有详情页基础上实现条件渲染。

## What Changes

- **修改门店详情页**：`pages/booking/detail.vue` 根据 `room_type` 条件渲染不同内容
  - 自习室（study）：保持现有行为不变
  - 培训室（training）：将"座位概况"替换为"教室概况"，新增"名师团队"横向滚动卡片和"本培训室课程"纵向列表，底部操作栏为心状关注按钮 + "返回课程"按钮
  - 综合室（comprehensive）：保留"座位概况"并在其下方新增"教室概况"、"名师团队"和"本培训室课程"列表，底部操作栏为心状关注按钮 + "预约自习室"按钮
- **新增培训室详情 API**：`GET /api/v1/training/rooms/{room_id}` 返回培训室详情（含教师列表和课程列表），路由定义不使用尾部斜杠（参考 bug-fixed.md BUG-22）
- **新增前端 API 模块**：`br-app/src/api/training.js` 增加 `getTrainingRoomDetail(roomId)` 函数
- **Vue3 生命周期钩子从 `vue` 包导入**（参考 bug-fixed.md BUG-14）
- **避免在模板中使用 `&lt;` 和 `&gt;` HTML 实体**（参考 bug-fixed.md BUG-20）

## Capabilities

### New Capabilities

- `training-room-detail-api`: 培训室详情 API — 按房间 ID 返回培训室基本信息、教师列表和课程列表的接口

### Modified Capabilities

- `study-room-booking-ui`: 门店详情页 requirement 修改为根据 `room_type` 条件渲染：自习室保持现有座位概况 + 立即预约；培训室显示教室概况 + 名师团队 + 课程列表 + 返回课程按钮；综合室显示座位概况 + 教室概况 + 名师团队 + 课程列表 + 预约自习室按钮

## Impact

**影响模块范围**：

- **br-server**（后端 API）:
  - `app/schemas/course.py` — TrainingRoomDetailResponse 新增（含 teachers 和 courses 嵌套对象）
  - `app/services/training_service.py` — 新增 `get_training_room_detail(room_id)` 方法
  - `app/api/routes/training.py` — 新增 `GET /api/v1/training/rooms/{room_id}` 路由
- **br-app**（微信小程序前端）:
  - `src/pages/booking/detail.vue` — 修改为根据 `room_type` 条件渲染
  - `src/api/training.js` — 新增 `getTrainingRoomDetail(roomId)` 函数
- **不涉及 br-admin**

**依赖**:
- 依赖 `training-course-list` change 的后端基础设施：`room_type` 字段、Teacher 模型、Course 模型、培训室/课程列表 API。两个 change 可并行开发，但本 change 的运行时验证需要 `training-course-list` 的数据库迁移已执行。

**回滚方案**:

1. 后端代码：`git revert` 恢复 `training.py` 路由和 service 变更，删除新增的 schema 字段
2. 前端代码：`git revert` 恢复 `detail.vue`，删除 `api/training.js` 中的 `getTrainingRoomDetail` 函数
3. 不涉及数据库迁移（依赖 `training-course-list` 的迁移，不单独创建迁移文件）

```

## openspec/changes/training-room-overview/design.md

- Source: openspec/changes/training-room-overview/design.md
- Lines: 1-133
- SHA256: 5b85af8cc9eb2efd08de32d48c0dc6ade523bb0c430d39cfe7e482036dbca6ff

[TRUNCATED]

```md
## Context

当前自习室详情页 `pages/booking/detail.vue` 仅服务于自习室座位预约场景，固定展示座位概况统计和"立即预约"按钮。`training-course-list` change 已在 `study_rooms` 表增加 `room_type` 字段（study/training/comprehensive），并创建了 `teachers` 和 `courses` 表及培训室列表/课程列表 API。本 change 在此基础上扩展详情页，根据 `room_type` 条件渲染差异化内容。参见 proposal.md 了解动机。

## Goals / Non-Goals

**Goals:**

- 修改 `pages/booking/detail.vue` 根据 `room_type` 条件渲染：自习室保持不变，培训室显示教室概况+名师团队+课程列表，综合室显示座位概况+教室概况+名师团队+课程列表
- 新建 `GET /api/v1/training/rooms/{room_id}` API 返回培训室详情（含教师和课程数据）
- 前端根据 `room_type` 条件调用不同 API，避免不必要的请求
- 底部操作栏按钮根据 `room_type` 调整

**Non-Goals:**

- 不实现培训课程列表页面（`pages/training/index`，由 `training-course-list` change 负责）
- 不实现课程详情页或课程预约/下单/支付功能
- 不实现教师详情页
- 不涉及 br-admin 后台管理
- 不重复 `training-course-list` 已定义的后端模型和列表 API

## Decisions

### 1. 修改现有 detail.vue 而非创建新页面

**选择**：在现有 `pages/booking/detail.vue` 中根据 `room_type` 条件渲染，而非为培训室创建独立页面。

**理由**：用户明确要求"基于自习室详情页面来实现"，且自习室、培训室和综合室共享大量页面结构（封面图、名称、评分、地址、环境照片等）。条件渲染避免代码重复，一个页面处理三种类型更易维护。综合室同时需要座位和培训数据，单页面更易于组合展示。

**备选方案**：为培训室创建独立页面 `pages/training/room-detail.vue`。被否决因为大量页面结构重复，且综合室需要同时展示座位和培训内容，独立页面无法自然组合。

### 2. 新建培训室详情 API 而非扩展现有房间详情 API

**选择**：新建 `GET /api/v1/training/rooms/{room_id}` 返回培训室详情（含教师和课程），不修改现有 `GET /api/v1/rooms/{room_id}`。

**理由**：现有房间详情 API 服务于自习室预约流程，响应结构以座位为核心。培训室详情需要教师和课程数据，属于不同的业务领域。使用独立的 `/api/v1/training/` 前缀与 `training-course-list` change 的培训室列表 API 保持一致，职责清晰。前端根据 `room_type` 决定是否调用此 API，避免自习室请求不必要的培训数据。

**备选方案**：扩展现有 `GET /api/v1/rooms/{room_id}` 响应增加 `teachers` 和 `courses` 字段。被否决因为自习室请求会附带不必要的培训数据，且两种业务逻辑耦合在同一接口中。

### 3. 前端根据 room_type 条件调用 API

**选择**：前端先通过 `GET /api/v1/rooms/{room_id}` 获取房间基本信息（含 `room_type`），再根据 `room_type` 决定后续 API 调用：
- `study`：调用 `GET /api/v1/rooms/{room_id}/seats/stats` 获取座位统计
- `training`：调用 `GET /api/v1/training/rooms/{room_id}` 获取教师和课程
- `comprehensive`：同时调用座位统计和培训室详情两个 API

**理由**：按需请求减少不必要的网络流量和响应体积。综合室需要两种数据，使用 `Promise.all` 并行请求。

**备选方案**：一次性请求所有数据。被否决因为自习室不需要培训数据，培训室不需要座位数据。

### 4. 教室概况统计数据来源

**选择**：教室概况统计卡片（培训教室数、小班容量、认证讲师数、累计学员数）的数据由后端 `GET /api/v1/training/rooms/{room_id}` 响应提供，前端不硬编码。

**理由**：教室数量和讲师数需要根据数据库实时计算，硬编码会导致数据不准确。后端通过 COUNT 查询和 JOIN 聚合统计数据。

**备选方案**：前端根据已获取的 `teachers` 数组和 `courses` 数组在前端计算统计。被否决因为"培训教室数"和"累计学员数"等指标无法仅从教师和课程列表推导。

### 5. UI 实现参考原型图

**选择**：培训室和综合室的 UI 实现参考 `prototype/training-room.html` 高保真原型图，保持配色 #4F6EF7、背景 #F5F6FA、卡片白色 rounded-2xl shadow-sm 等设计要素一致。

**理由**：项目已有统一的设计规范和原型体系，参考原型图确保视觉一致性。现有 detail.vue 已使用 rpx 单位和 SCSS 变量，新增部分沿用相同样式体系。

## Risks / Trade-offs

- **[依赖风险]** → 本 change 依赖 `training-course-list` change 的数据库迁移（room_type 列、teachers 表、courses 表）。两个 change 可并行开发代码，但运行时验证需要 training-course-list 的迁移已执行。缓解：在 tasks.md 中明确标注依赖关系，验证步骤中先确认 training-course-list 迁移状态。
- **[API 尾部斜杠问题]** → 根据 bug-fixed.md BUG-22，所有新路由定义不得使用尾部斜杠。新路由使用 `@router.get("/{room_id}")` 而非 `@router.get("/{room_id}/")`。
- **[uni-app 生命周期钩子导入]** → 根据 bug-fixed.md BUG-14，`onMounted` 等 Vue 3 生命周期钩子必须从 `vue` 包导入，不能从 `@dcloudio/uni-app` 导入。`onLoad`、`onShow` 等 uni-app 页面钩子从 `@dcloudio/uni-app` 导入。
- **[WXML 非法字符]** → 根据 bug-fixed.md BUG-20，避免在 Vue 模板中使用 `&lt;` 和 `&gt;` HTML 实体，使用 Unicode 字符替代。
- **[页面性能]** → 综合室需要同时请求座位统计和培训室详情两个 API。使用 `Promise.all` 并行请求，页面 loading 状态在两个请求都完成后隐藏。
- **[条件渲染复杂度]** → detail.vue 将包含三种类型的条件渲染逻辑，模板和 script 复杂度增加。通过 computed 属性封装 room_type 判断逻辑，保持模板可读性。

## Migration Plan

1. **后端代码部署**：
   - 在 `training_service.py` 新增 `get_training_room_detail(room_id)` 方法
   - 在 `schemas/course.py` 新增 `TrainingRoomDetailResponse` schema
   - 在 `routes/training.py` 新增 `GET /{room_id}` 路由（不使用尾部斜杠）
   - 运行测试验证

```

Full source: openspec/changes/training-room-overview/design.md

## openspec/changes/training-room-overview/tasks.md

- Source: openspec/changes/training-room-overview/tasks.md
- Lines: 1-73
- SHA256: f5eeb6aeee5123428cec60605ebcd1f0187ceb792f77b6af05e84fa28eb65223

```md
## 1. 后端 Schema

- [ ] 1.1 在 `br-server/app/schemas/course.py` 新增 `TrainingRoomDetailResponse`：包含房间基本信息字段（id、name、description、cover_image、address、business_hours、status、room_type、min_price、city_id、city_name、rating）+ `teachers` 数组（TeacherResponse 嵌套）+ `courses` 数组（CourseResponse 嵌套）+ 教室概况统计字段（classroom_count、class_capacity、teacher_count、total_students）
- [ ] 1.2 确认 `TeacherResponse`（id、name、avatar、title、rating）已在 `br-server/app/schemas/teacher.py` 中定义（由 `training-course-list` change 创建），如不存在则创建
- [ ] 1.3 确认 `CourseResponse`（含 teacher 嵌套对象、tags 数组解析）已在 `br-server/app/schemas/course.py` 中定义（由 `training-course-list` change 创建），如不存在则创建

## 2. 后端 Service

- [ ] 2.1 在 `br-server/app/services/training_service.py` 新增 `get_training_room_detail(room_id: int)` 方法：查询 `study_rooms` 表中 `room_type in (training, comprehensive)` 且指定 id 的房间，如果不存在或类型不匹配返回 None
- [ ] 2.2 在 `get_training_room_detail` 中查询该房间下所有 `status=active` 的课程（JOIN teachers 获取教师信息），按 `sort_order` 排序
- [ ] 2.3 在 `get_training_room_detail` 中从课程列表提取去重后的教师列表
- [ ] 2.4 在 `get_training_room_detail` 中聚合教室概况统计数据：培训教室数（该房间下 status=active 的课程总数）、小班容量（固定值 8-12）、认证讲师数（去重教师数）、累计学员数（该房间所有课程 enrollment_count 之和）
- [ ] 2.5 组装 `TrainingRoomDetailResponse` 并返回

## 3. 后端 API Routes

- [ ] 3.1 在 `br-server/app/api/routes/training.py` 新增 `GET /{room_id}` 路由（**注意：路由定义不使用尾部斜杠，参考 bug-fixed.md BUG-22**），调用 `training_service.get_training_room_detail(room_id)`，返回 `TrainingRoomDetailResponse`
- [ ] 3.2 路由处理 404 情况：房间不存在或类型不是 training/comprehensive 时返回 HTTP 404
- [ ] 3.3 确认路由已在 `br-server/app/main.py` 中注册（由 `training-course-list` change 创建的 training_router，新增路由会自动包含）

## 4. 后端测试

- [ ] 4.1 在 `br-server/tests/test_training_api.py` 新增培训室详情接口测试：正常请求培训室详情（验证响应字段完整性：房间信息、teachers 数组、courses 数组、教室概况统计）
- [ ] 4.2 新增综合室详情请求测试：验证综合室返回与培训室相同的结构
- [ ] 4.3 新增 404 场景测试：请求自习室 room_id 返回 404、请求不存在的 room_id 返回 404
- [ ] 4.4 新增教师去重测试：多门课程关联同一教师时 teachers 数组去重
- [ ] 4.5 新增空课程场景测试：培训室无课程时 teachers 和 courses 数组为空
- [ ] 4.6 新增 tags 解析测试：课程 tags 字段从逗号分隔字符串解析为数组
- [ ] 4.7 新增无教师课程测试：课程未关联教师时 teacher 字段为 null
- [ ] 4.8 运行 `pytest tests/test_training_api.py -q` 确保全部测试通过（**注意：依赖 training-course-list change 的数据库迁移已执行**）

## 5. 前端 API 模块

- [ ] 5.1 在 `br-app/src/api/training.js` 新增 `getTrainingRoomDetail(roomId)` 函数，封装 `GET /api/v1/training/rooms/{room_id}` 请求（**注意：URL 不使用尾部斜杠，参考 bug-fixed.md BUG-22**）

## 6. 前端页面实现

- [ ] 6.1 修改 `br-app/src/pages/booking/detail.vue` 的 `data()` 增加 `trainingData`（存储培训室详情数据：teachers、courses、教室概况统计）和 `roomType`（从房间信息获取 room_type 字段）
- [ ] 6.2 修改 `loadData()` 方法：先调用 `fetchBookingRoom(this.roomId)` 获取房间基本信息和 room_type，再根据 room_type 条件调用后续 API（**注意：Vue3 生命周期钩子从 `vue` 包导入，参考 bug-fixed.md BUG-14**）
  - room_type=study：调用 `getSeatStats(this.roomId)`（现有逻辑）
  - room_type=training：调用 `getTrainingRoomDetail(this.roomId)`
  - room_type=comprehensive：`Promise.all` 并行调用 `getSeatStats` 和 `getTrainingRoomDetail`
- [ ] 6.3 新增 computed 属性：`isStudyRoom`、`isTrainingRoom`、`isComprehensiveRoom`、`trainingRoomStats`（教室概况统计）、`teachers`（名师团队列表）、`courses`（课程列表）
- [ ] 6.4 在模板中添加条件渲染：培训室显示教室概况（替换座位概况）、名师团队横向滚动卡片、本培训室课程纵向列表
- [ ] 6.5 综合室模板中保留座位概况，并在其下方添加教室概况、名师团队、课程列表
- [ ] 6.6 实现教室概况统计卡片 UI（参考 prototype/training-room.html，2x2 网格：培训教室数、小班容量、认证讲师、累计学员）
- [ ] 6.7 实现名师团队横向滚动卡片 UI（教师头像、姓名、头衔、评分，横向 scroll-view）
- [ ] 6.8 实现本培训室课程纵向列表 UI（封面图、课程名、状态标签、教师信息、排课时间、价格、预约入口，参考 prototype/training-room.html）
- [ ] 6.9 修改底部操作栏条件渲染：
  - study：心状关注按钮 + "立即预约"按钮（现有逻辑）
  - training：心状关注按钮 + "返回课程"按钮（跳转到 `pages/training/index`）
  - comprehensive：心状关注按钮 + "预约自习室"按钮（跳转到座位选择页）
- [ ] 6.10 实现空状态提示：培训室无课程时名师团队和课程列表区域显示"暂无课程"
- [ ] 6.11 新增"返回课程"按钮的 `onBackToCourses()` 方法和"预约自习室"按钮的 `onBookStudy()` 方法
- [ ] 6.12 **注意：避免在 Vue 模板中使用 `&lt;` 和 `&gt;` HTML 实体，使用 Unicode 字符（参考 bug-fixed.md BUG-20）**
- [ ] 6.13 新增 SCSS 样式：教室概况统计卡片、名师团队卡片、课程列表卡片、培训室简介、教学设施网格等样式，保持与现有 detail.vue 风格一致（rpx 单位、SCSS 变量、rounded-2xl shadow-sm）

## 7. 代码审查与重构

- [ ] 7.1 确保后端 Clean Architecture 分层：routes 仅处理 HTTP → services 处理业务逻辑 → models 定义数据 → schemas 定义响应
- [ ] 7.2 消除重复代码：复用 `training-course-list` change 已定义的 `TeacherResponse` 和 `CourseResponse`，不重复定义
- [ ] 7.3 确保前端组件分层：detail.vue 调用 api 模块，api 模块调用 utils/request.js
- [ ] 7.4 检查所有新路由无尾部斜杠，与现有路由风格一致

## 8. API 文档更新

- [ ] 8.1 在 `docs/api.md` 补充 `GET /api/v1/training/rooms/{room_id}` 接口文档（路径、路径参数、响应示例、404 场景说明）

## 9. 最终验证

- [ ] 9.1 运行后端全部测试：`conda activate booking-room && cd br-server && pytest tests/ -q`（**注意：依赖 training-course-list change 的数据库迁移已执行**）
- [ ] 9.2 前端构建验证：`nvm use v22.22.0 && cd br-app && npm run build`
- [ ] 9.3 验证现有自习室预约功能不受影响（自习室详情页行为与修改前完全一致）

```

## openspec/changes/training-room-overview/specs/study-room-booking-ui/spec.md

- Source: openspec/changes/training-room-overview/specs/study-room-booking-ui/spec.md
- Lines: 1-74
- SHA256: 2b32d8ba0d5b3e19b62a7917b4a6556279985d634ec1e8c57a8499b45c17759c

```md
## MODIFIED Requirements

### Requirement: Store detail page
系统 SHALL 提供门店详情页（`pages/booking/detail.vue`），参照 `prototype/store-detail.html` 和 `prototype/training-room.html` 高保真原型图。页面 SHALL 根据 `room_type` 条件渲染不同内容：

**自习室（study）**：页面包含顶部封面大图、门店名称和营业状态标签、评分、地址（含距离）、营业时间、区域标签（静音区/键盘区/VIP区/WiFi/充电插座）、环境照片横向滚动列表、座位概况统计卡片（总座位/可用/已占/维护中）、底部固定栏（心状关注按钮 + "立即预约"按钮）。点击"立即预约"跳转到座位选择页。

**培训室（training）**：页面包含顶部封面大图、培训室名称和营业状态标签、评分、地址、营业时间、设施标签（多媒体教室/小班授课/一对一辅导/WiFi/空调开放）、培训室简介、环境照片横向滚动列表、教学设施网格（白板/投影仪/空调/隔音墙/WiFi/充电口）、教室概况统计卡片（培训教室数/小班容量/认证讲师/累计学员）、名师团队横向滚动卡片（教师头像、姓名、头衔、评分）、本培训室课程纵向列表（封面图、课程名、状态标签、教师信息、排课时间、价格、预约按钮）、底部固定栏（心状关注按钮 + "返回课程"按钮）。点击"返回课程"跳转到培训课程列表页。

**综合室（comprehensive）**：页面包含顶部封面大图、综合室名称和营业状态标签、评分、地址、营业时间、区域标签、环境照片横向滚动列表、座位概况统计卡片（总座位/可用/已占/维护中）、教室概况统计卡片（培训教室数/小班容量/认证讲师/累计学员）、名师团队横向滚动卡片、本培训室课程纵向列表、底部固定栏（心状关注按钮 + "预约自习室"按钮）。点击"预约自习室"跳转到座位选择页。

页面 SHALL 通过 `GET /api/v1/rooms/{room_id}` 获取房间基本信息（含 `room_type` 字段），当 `room_type` 为 `training` 或 `comprehensive` 时 SHALL 额外调用 `GET /api/v1/training/rooms/{room_id}` 获取教师和课程数据。当 `room_type` 为 `study` 或 `comprehensive` 时 SHALL 调用 `GET /api/v1/rooms/{room_id}/seats/stats` 获取座位统计数据。

#### Scenario: Display study room detail
- **GIVEN** 用户进入详情页，`room_id=1`，该房间 `room_type=study`
- **WHEN** 页面加载完成
- **THEN** 页面展示封面图、名称、营业状态、评分、地址、营业时间、区域标签、环境照片、座位概况统计卡片
- **AND** 底部固定栏显示心状关注按钮和"立即预约"按钮

#### Scenario: Study room navigate to seat select
- **WHEN** 用户在自习室详情页点击"立即预约"按钮
- **THEN** 跳转到座位选择页，传递 `room_id` 参数

#### Scenario: Display training room detail
- **GIVEN** 用户进入详情页，`room_id=4`，该房间 `room_type=training`
- **WHEN** 页面加载完成
- **THEN** 页面展示封面图、培训室名称、营业状态、评分、地址、营业时间、设施标签、培训室简介、环境照片、教学设施网格、教室概况统计卡片、名师团队横向滚动卡片、本培训室课程纵向列表
- **AND** 不显示座位概况统计卡片
- **AND** 底部固定栏显示心状关注按钮和"返回课程"按钮

#### Scenario: Training room navigate to course list
- **WHEN** 用户在培训室详情页点击"返回课程"按钮
- **THEN** 跳转到培训课程列表页（`pages/training/index`）

#### Scenario: Display comprehensive room detail
- **GIVEN** 用户进入详情页，`room_id=7`，该房间 `room_type=comprehensive`
- **WHEN** 页面加载完成
- **THEN** 页面展示封面图、综合室名称、营业状态、评分、地址、营业时间、区域标签、环境照片、座位概况统计卡片、教室概况统计卡片、名师团队横向滚动卡片、本培训室课程纵向列表
- **AND** 底部固定栏显示心状关注按钮和"预约自习室"按钮

#### Scenario: Comprehensive room navigate to seat select
- **WHEN** 用户在综合室详情页点击"预约自习室"按钮
- **THEN** 跳转到座位选择页，传递 `room_id` 参数

#### Scenario: Training room teachers display
- **GIVEN** 培训室有 3 位关联教师
- **WHEN** 培训室详情页加载完成
- **THEN** 名师团队区域横向滚动展示 3 张教师卡片，每张卡片包含头像、姓名、头衔和评分

#### Scenario: Training room courses display
- **GIVEN** 培训室有 5 门 `status=active` 的课程
- **WHEN** 培训室详情页加载完成
- **THEN** 本培训室课程区域纵向展示 5 张课程卡片，每张卡片包含封面图、课程名、状态标签、教师信息、排课时间、价格和预约入口

#### Scenario: Training room with no courses
- **GIVEN** 培训室没有关联任何课程
- **WHEN** 培训室详情页加载完成
- **THEN** 名师团队区域和本培训室课程区域显示空状态提示"暂无课程"

#### Scenario: Room not found
- **WHEN** 用户进入详情页，`room_id` 对应的房间不存在
- **THEN** 显示错误提示并返回上一页

#### Scenario: Follow room toggle
- **GIVEN** 用户在任意类型房间详情页
- **WHEN** 用户点击心状关注按钮
- **THEN** 切换关注状态，关注时显示红色心形图标，取消关注时显示灰色心形描边

#### Scenario: Conditional API calls based on room type
- **GIVEN** 用户进入详情页，`room_id` 对应的房间 `room_type=training`
- **WHEN** 页面加载数据
- **THEN** 调用 `GET /api/v1/rooms/{room_id}` 获取房间基本信息
- **AND** 调用 `GET /api/v1/training/rooms/{room_id}` 获取教师和课程数据
- **AND** 不调用 `GET /api/v1/rooms/{room_id}/seats/stats`

```

## openspec/changes/training-room-overview/specs/training-room-detail-api/spec.md

- Source: openspec/changes/training-room-overview/specs/training-room-detail-api/spec.md
- Lines: 1-58
- SHA256: e18fb03fc1ddb625327c38ccc558c136e599f63626219d06e2590ee07aa8d1cd

```md
## Purpose

培训室详情 API 提供按房间 ID 查询单个培训室详情的接口，返回培训室基本信息、关联教师列表和课程列表，支撑 br-app 培训室概况页面的数据展示。

## ADDED Requirements

### Requirement: Get training room detail API

系统 SHALL 提供 `GET /api/v1/training/rooms/{room_id}` 接口，按房间 ID 返回培训室详情。仅返回 `room_type` 为 `training` 或 `comprehensive` 的房间。响应 SHALL 包含房间基本信息、教师列表（关联该房间下课程的教师去重后列表）和课程列表（该房间下所有 `status=active` 的课程）。路由定义不使用尾部斜杠。

#### Scenario: Successful detail request for training room

- **GIVEN** 一间 `room_type=training` 且 `status=open` 的培训室，id=1
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** 返回 HTTP 200，响应包含房间基本信息（id、name、description、cover_image、address、business_hours、status、room_type、min_price、city_id、city_name、rating）、`teachers` 数组和 `courses` 数组

#### Scenario: Successful detail request for comprehensive room

- **GIVEN** 一间 `room_type=comprehensive` 且 `status=open` 的综合室，id=5
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/5`
- **THEN** 返回 HTTP 200，响应结构与培训室相同，包含教师列表和课程列表

#### Scenario: Study room returns 404

- **GIVEN** 一间 `room_type=study` 的自习室，id=2
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/2`
- **THEN** 返回 HTTP 404，错误信息说明该房间不是培训室

#### Scenario: Non-existent room returns 404

- **WHEN** 客户端发送 `GET /api/v1/training/rooms/999`
- **THEN** 返回 HTTP 404，错误信息说明房间不存在

#### Scenario: Training room with teachers and courses

- **GIVEN** 培训室 id=1 关联了 3 门课程，其中 2 门课程关联了教师 A 和教师 B，1 门课程未关联教师
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** `teachers` 数组包含 2 位教师（去重后），`courses` 数组包含 3 门课程
- **AND** 每位教师的字段包含 id、name、avatar、title、rating
- **AND** 每门课程的字段包含 id、name、cover_image、teacher（嵌套对象或 null）、category、price、rating、enrollment_count、schedule、tags（数组）、status、room_id、room_name

#### Scenario: Training room with no courses

- **GIVEN** 培训室 id=3 没有关联任何课程
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/3`
- **THEN** 返回 HTTP 200，`teachers` 数组为空，`courses` 数组为空

#### Scenario: Course tags parsing in detail response

- **GIVEN** 培训室 id=1 的一门课程 `tags` 字段值为 "多媒体,小班,1对1"
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** 该课程的 `tags` 字段返回为 `["多媒体", "小班", "1对1"]`

#### Scenario: Course without teacher in detail response

- **GIVEN** 培训室 id=1 的一门课程未关联教师（teacher_id 为 null）
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** 该课程的 `teacher` 字段为 null

```
