# Comet Design Handoff

- Change: course-detail-page
- Phase: design
- Mode: compact
- Context hash: f00931f94e40180e5a6849164c0ef824b4a1e4e487f8262fed0f2e67138188a9

Generated-by: comet-handoff.sh

OpenSpec remains the canonical capability spec. This handoff is a deterministic, source-traceable context pack, not an agent-authored summary.

## openspec/changes/course-detail-page/proposal.md

- Source: openspec/changes/course-detail-page/proposal.md
- Lines: 1-57
- SHA256: a4d561d847b097f4c4711b5a4702441802a0ca486ab1a17cb221e86f29139f8b

```md
## Why

br-app 培训课程列表页已上线，但缺少课程详情页面。用户点击课程后无法查看完整信息（教师、介绍、课程目录、评价等），也无法关注感兴趣的课程。需要参考高保真原型 `prototype/course-detail.html` 实现课程详情页，复用自习室关注机制（`room_follows` 表）并添加类型区分字段。

## What Changes

- **新增课程详情 API**：`GET /api/v1/training/courses/{course_id}` 返回课程完整信息（含教师、教室、课程目录）
- **新增课程课时表**：`course_lessons` 表存储课程目录（课时标题、时长、排序等）
- **扩展关注表**：`room_follows` 表新增 `follow_type` 字段（`room` / `course`），支持课程关注
- **新增课程详情前端页面**：`br-app/src/pages/training/course-detail.vue`，严格参考原型实现
- **课程列表导航**：培训页课程卡片点击跳转到课程详情页
- **底部操作栏**：左侧心形关注按钮 + 价格展示 + 立即预约按钮
- **数据库迁移**：为 `room_follows` 表添加 `follow_type` 列，新增 `course_lessons` 表

## Capabilities

### New Capabilities

- `course-detail-api`: 课程详情后端 API，返回课程完整信息（基本信息、教师、教室、标签、课程目录等）
- `course-lessons`: 课程课时数据模型和 API，支持课程目录展示
- `course-detail-ui`: 课程详情前端页面，包含 Hero 图、课程信息卡、教师信息、课程介绍、课程目录、学员评价、相关课程、底部操作栏（含关注按钮）
- `course-follow`: 课程关注功能，扩展 room_follows 表添加 follow_type 字段，复用已有关注 API 模式

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **br-server**：
  - 新增路由：`br-server/app/api/routes/training.py` 添加课程详情端点
  - 新增服务方法：`br-server/app/services/training_service.py` 添加 `get_course_detail`
  - 新增模型：`br-server/app/models/course_lesson.py` 课时模型
  - 新增 Schema：`br-server/app/schemas/course.py` 添加 `CourseDetailResponse`、`LessonResponse`
  - 模型修改：`br-server/app/models/room_follow.py` 添加 `follow_type` 字段
  - 服务修改：`br-server/app/services/room_follow_service.py` 支持 follow_type 过滤
  - 路由修改：`br-server/app/api/routes/room_follow.py` 接受 follow_type 参数
  - 数据库迁移：新增 alembic 迁移文件（`course_lessons` 表 + `room_follows.follow_type` + `courses.description`）
  - 测试：新增课程详情 API 测试、课时 API 测试和课程关注测试

- **br-app**：
  - 新增页面：`br-app/src/pages/training/course-detail.vue`
  - 路由注册：`br-app/src/pages.json` 添加课程详情页路由
  - API 封装：`br-app/src/api/training.js` 添加 `getCourseDetail`
  - 导航修改：`br-app/src/pages/training/index.vue` 课程卡片添加点击跳转
  - 关注服务扩展：新建 `br-app/src/services/followedCourses.js`

- **数据库**：
  - `room_follows` 表新增 `follow_type` 列（默认值 `room`，向后兼容）
  - 新增 `course_lessons` 表
  - `courses` 表新增 `description` 列

## 回滚方案

- 后端：`follow_type` 字段设默认值 `room`，迁移可安全回滚（downgrade 删除列）；`course_lessons` 表可安全删除
- 前端：新增页面和路由，删除即可回滚，不影响现有功能
- API：新增端点，不影响现有端点

```

## openspec/changes/course-detail-page/design.md

- Source: openspec/changes/course-detail-page/design.md
- Lines: 1-91
- SHA256: be6f92fb419b506938200d60238c41aeaa891c2f181684e7a8ced06cef7eef3f

[TRUNCATED]

```md
# Design: 课程详情页

## Context

br-app 已有培训课程列表页（`training/index.vue`）和自习室详情页（`booking/detail.vue`）。课程详情页需要复用自习室详情页的视觉模式（Hero 图 + 上浮信息卡 + 底部操作栏 + 心形关注按钮），但内容结构不同（课程有教师、目录、评价等）。

关注功能现有 `room_follows` 表 + `followedRooms.js` 服务，需要扩展支持课程类型。

课程目录需要新建 `course_lessons` 表存储课时数据，评价数据暂用前端静态占位。

## Goals / Non-Goals

**Goals**：
- 实现与原型高度一致的课程详情页 UI
- 复用自习室详情页的视觉模式，保持设计一致性
- 通过 `follow_type` 字段扩展关注表，避免新建独立表
- 新建 `course_lessons` 表支持课程目录动态数据
- 后端课程详情 API 包含相关课程推荐

**Non-Goals**：
- 不实现评价系统（原型中的评价使用静态占位数据）
- 不实现课程预约流程（底部「立即预约」暂为占位）
- 不实现教师详情页（点击跳转占位）
- 不实现课时视频播放功能

## Decisions

### D-1: 课程详情 API 路由设计

**选择**：`GET /api/v1/training/courses/{course_id}`，复用现有 training router。

**理由**：与现有 `/api/v1/training/courses`（列表）和 `/api/v1/training/rooms/{room_id}`（培训室详情）保持一致的路由风格。

### D-2: follow_type 扩展方案

**选择**：在 `room_follows` 表添加 `follow_type` 列（String(20)，默认 `room`），修改唯一约束为 `(user_id, room_id, follow_type)`。`follow_type=course` 时 `room_id` 存储 `course_id`。

**理由**：用户明确要求「库表也使用一样的，加上类型来区分」；避免新建独立表。

**替代方案**：新建 `course_follows` 表 → 违反用户要求。

### D-3: course_lessons 表设计

**选择**：新建 `course_lessons` 表，字段包含 `course_id`（外键）、`title`、`description`、`duration_minutes`、`sort_order`、`is_free_preview`。

**理由**：
- 课程目录是课程的核心数据，需要持久化存储
- `sort_order` 支持灵活排序
- `is_free_preview` 为后续免费试看功能预留
- 课时数据在课程详情 API 中嵌入返回，无需独立端点

**替代方案**：
- 使用 JSON 字段存储在 courses 表中 → 不利于查询和排序
- 独立课时 API 端点 → 增加请求数，无必要

### D-4: 前端关注服务分离

**选择**：新建 `followedCourses.js` 服务，与 `followedRooms.js` 平行。

**理由**：课程和自习室的本地缓存数据结构不同，使用独立 storage key 避免数据混淆。

### D-5: 课程详情页组件架构

**选择**：单文件组件 `course-detail.vue`，使用 Options API（与 `booking/detail.vue` 一致）。

**理由**：与自习室详情页保持一致的代码风格，单文件组件足够。

### D-6: 评价数据

**选择**：前端使用静态占位数据，不从后端获取。

**理由**：当前无评价数据模型，后续迭代再实现。

## Risks / Trade-offs

- **[follow_type 语义]** `room_id` 列在 `follow_type=course` 时存储 `course_id`，字段名与实际含义不一致 → 迁移时删除 `room_id` 外键约束，改为普通 Integer 列 + 应用层校验。

- **[原型静态数据]** 评价使用前端占位数据，后续迭代需要替换 → 在组件中预留数据接口。

## Migration Plan

```

Full source: openspec/changes/course-detail-page/design.md

## openspec/changes/course-detail-page/tasks.md

- Source: openspec/changes/course-detail-page/tasks.md
- Lines: 1-64
- SHA256: f199c660b17d5ee2fb6d4e73694a5277d0ca1364feb132bd756b51f3f24bc549

```md
# Tasks: 课程详情页

## 1. 工作区隔离

- [ ] 1.1 创建 git 分支 `course-detail-page` 和对应 worktree

## 2. 数据库迁移

- [ ] 2.1 `courses` 表新增 `description` 列（String(1000)，nullable）
- [ ] 2.2 新建 `course_lessons` 表（course_id, title, description, duration_minutes, sort_order, is_free_preview, created_at, updated_at）
- [ ] 2.3 `room_follows` 表新增 `follow_type` 列（String(20)，默认 `room`，NOT NULL）
- [ ] 2.4 修改 `room_follows` 唯一约束为 `(user_id, room_id, follow_type)`
- [ ] 2.5 删除 `room_follows.room_id` 外键约束，改为普通 Integer 列 + 应用层校验
- [ ] 2.6 生成 alembic 迁移文件并验证

## 3. 后端：CourseLesson 模型与课时数据

- [ ] 3.1 新建 `CourseLesson` 模型（`course_lesson.py`）
- [ ] 3.2 新增 `LessonResponse` Schema
- [ ] 3.3 课时种子数据脚本（为现有活跃课程生成示例课时）

## 4. 后端：课程详情 API

- [ ] 4.1 `Course` 模型添加 `description` 字段
- [ ] 4.2 `RoomFollow` 模型添加 `follow_type` 字段，更新表配置
- [ ] 4.3 新增 `CourseDetailResponse` Schema（含 teacher、room、lessons、related_courses）
- [ ] 4.4 `training_service.py` 新增 `get_course_detail()` 方法（含课时查询和相关课程查询）
- [ ] 4.5 `training.py` 路由新增 `GET /courses/{course_id}` 端点
- [ ] 4.6 更新 `training.js` 前端 API 封装，新增 `getCourseDetail(courseId)`

## 5. 后端：课程关注功能

- [ ] 5.1 `room_follow_service.py` 扩展：follow/unfollow/list 支持 `follow_type` 参数
- [ ] 5.2 `room_follow.py` 路由扩展：接受 `follow_type` 查询参数
- [ ] 5.3 `roomFollows.js` 前端 API 层扩展 `follow_type` 参数传递

## 6. 后端：测试

- [ ] 6.1 课程详情 API 测试（正常、404、非 active 状态、含课时数据）
- [ ] 6.2 课程关注 API 测试（关注、取消、列表、幂等性）
- [ ] 6.3 现有 room_follow 测试回归验证（确保向后兼容）

## 7. 前端：课程详情页

- [ ] 7.1 创建 `course-detail.vue` 页面：Hero 区域 + 自定义导航栏
- [ ] 7.2 课程信息卡（标签、名称、评分、价格）
- [ ] 7.3 教师信息卡（头像、认证、评分）
- [ ] 7.4 课程介绍区域（文本 + 特色亮点网格）
- [ ] 7.5 课程目录区域（从 API 获取课时数据 + 展开/收起）
- [ ] 7.6 学员评价区域（评分汇总 + 静态占位评价列表）
- [ ] 7.7 相关课程横向滚动列表（从 API related_courses 获取）
- [ ] 7.8 底部操作栏（心形关注按钮 + 价格 + 立即预约）

## 8. 前端：关注服务与导航

- [ ] 8.1 新建 `followedCourses.js` 服务（本地缓存 + API 同步）
- [ ] 8.2 `pages.json` 注册课程详情页路由
- [ ] 8.3 `training/index.vue` 课程卡片点击跳转到课程详情页
- [ ] 8.4 课程详情页关注按钮交互（关注/取消 + Toast）

## 9. 构建验证

- [ ] 9.1 后端 pytest 全部通过
- [ ] 9.2 前端 br-app 构建无错误

```

## openspec/changes/course-detail-page/specs/course-detail-api/spec.md

- Source: openspec/changes/course-detail-page/specs/course-detail-api/spec.md
- Lines: 1-41
- SHA256: fcdbe3bd950ca7d784a5199476c346a299b524e8e55cd21c5d86661f16290487

```md
# Course Detail API

## ADDED Requirements

### REQ-CDA-1: 课程详情端点

系统提供 `GET /api/v1/training/courses/{course_id}` 端点，返回课程完整详情。

**响应字段**：
- `id`：课程 ID
- `name`：课程名称
- `cover_image`：封面图 URL（可空）
- `category`：分类标识
- `price`：单价（Decimal）
- `rating`：评分
- `enrollment_count`：已学人数
- `schedule`：上课时间描述（可空）
- `tags`：标签列表
- `status`：课程状态
- `is_hot`：是否热销
- `description`：课程介绍（可空）
- `teacher`：教师信息对象（可空），含 `id`、`name`、`avatar`、`title`、`rating`
- `room`：教室信息对象，含 `id`、`name`、`address`、`cover_image`
- `lessons`：课时列表，按 `sort_order` 升序排列，每项含 `id`、`title`、`description`、`duration_minutes`、`sort_order`、`is_free_preview`
- `related_courses`：相关课程列表（同分类其他课程，最多 6 门）

**错误场景**：
- 课程不存在 → 404
- 课程状态非 `active` → 404

### REQ-CDA-2: 课程介绍字段

Course 模型新增可选 `description` 字段（String(1000)），用于存储课程详细介绍文本。该字段在课程列表 API 中不返回（避免带宽浪费），仅在详情 API 中返回。

### REQ-CDA-3: 相关课程查询

详情 API 返回的 `related_courses` 字段包含同分类下其他活跃课程（排除当前课程），按 `sort_order` 排序，最多返回 6 门。每门课程包含 `id`、`name`、`cover_image`、`price`。

### REQ-CDA-4: 课时数据嵌入

课程详情 API 的 `lessons` 字段从 `course_lessons` 表查询，按 `sort_order` 升序排列。无课时时返回空数组。

```

## openspec/changes/course-detail-page/specs/course-detail-ui/spec.md

- Source: openspec/changes/course-detail-page/specs/course-detail-ui/spec.md
- Lines: 1-55
- SHA256: 16cb79f50319143ee2d7cf121970626538fb4e205c7ff24884f4f58befbcbabb

```md
# Course Detail UI

## ADDED Requirements

### REQ-CDU-1: 课程详情页布局

课程详情页 (`/pages/training/course-detail?course_id=X`) 严格参考原型 `prototype/course-detail.html`，自上而下包含以下区块：

1. **Hero 区域**：全宽封面图 + 渐变遮罩 + 返回按钮（左上）+ 分享按钮（右上）
2. **课程信息卡**：白色圆角卡片，上浮覆盖 Hero 底部
   - 标签行（热销/分类标签）
   - 课程名称（大标题）
   - 评分 + 已学人数 + 课时数
   - 价格区域（单价 + 全套价格说明 + 热销标识）
3. **教师信息卡**：可点击跳转到教师主页（占位）
   - 头像 + 认证标识 + 姓名 + 认证讲师标签
   - 教学领域 + 教龄 + 学历
   - 评分 + 学员数
4. **课程介绍**：介绍文本 + 特色亮点网格（2x2）
5. **课程目录**：从后端 API 获取课时数据，每项含播放图标 + 标题 + 时长 + 状态
   - 默认展示前 4 节，「查看全部 N 课时」展开
   - 无课时时显示「暂无课程目录」占位
6. **学员评价**：评分汇总 + 评价列表（静态占位数据）
   - 默认展示 2 条，「查看全部评价」按钮
7. **相关课程**：横向滚动卡片列表（从 API 的 related_courses 获取）
8. **底部操作栏**（固定定位）：
   - 左侧：心形关注按钮（♥）
   - 中间：价格展示（单价起）
   - 右侧：「立即预约」按钮

### REQ-CDU-2: 课程列表导航

培训课程列表页 (`/pages/training/index`) 中：
- 「全部」标签下的培训室卡片中的热门课程点击 → 跳转课程详情页
- 分类标签下的课程卡片点击 → 跳转课程详情页

导航方式：`uni.navigateTo({ url: '/pages/training/course-detail?course_id=' + courseId })`

### REQ-CDU-3: 底部操作栏交互

- **关注按钮**：默认空心心形，点击后变为实心心形（红色），再次点击取消关注
- 关注状态从本地存储 + 后端 API 同步
- 关注/取消关注操作显示 Toast 提示
- **立即预约**：点击跳转到课程预约确认页（占位，暂显示 Toast）

### REQ-CDU-4: 页面路由注册

在 `pages.json` 中注册课程详情页路由，使用 `navigationStyle: custom` 自定义导航栏。

### REQ-CDU-5: 样式规范

- 使用项目现有 SCSS 变量（`$primary`、`$text-primary` 等）
- 卡片使用 `rounded-2xl` + `shadow-sm` 风格
- 动画使用 `fadeInUp` 入场动画
- 颜色严格参考原型：primary `#4F6EF7`、文字 `#2D3436`/`#636E72`/`#B2BEC3`

```

## openspec/changes/course-detail-page/specs/course-follow/spec.md

- Source: openspec/changes/course-detail-page/specs/course-follow/spec.md
- Lines: 1-34
- SHA256: c69ad20faa13b027d64f5ad944af83ca49386924dfa47749289d51dcfca0a302

```md
# Course Follow

## ADDED Requirements

### REQ-CF-1: follow_type 字段

`room_follows` 表新增 `follow_type` 列（String(20)，默认值 `room`，不可为空），用于区分关注类型：
- `room`：自习室/培训室关注（现有数据）
- `course`：课程关注

唯一约束调整为 `(user_id, room_id, follow_type)`，允许同一用户同时关注同一教室的房间和课程。

### REQ-CF-2: 关注 API 扩展

现有关注 API 端点接受可选 `follow_type` 查询参数：
- `POST /api/v1/room-follows/{target_id}?follow_type=course`：关注课程
- `DELETE /api/v1/room-follows/{target_id}?follow_type=course`：取消关注课程
- `GET /api/v1/room-follows?follow_type=course`：获取关注的课程列表

当 `follow_type=course` 时，`room_id` 字段实际存储 `course_id`。

### REQ-CF-3: 前端关注服务

新建 `br-app/src/services/followedCourses.js`，提供课程关注的本地缓存和 API 同步：
- `followCourse(course)`：本地缓存 + 后端持久化
- `unfollowCourse(courseId)`：本地移除 + 后端删除
- `isCourseFollowed(courseId)`：检查本地缓存
- 使用独立的 storage key `followed_courses`

### REQ-CF-4: 向后兼容

- 现有 `room_follows` 数据在迁移时自动填充 `follow_type = 'room'`
- 现有 API 不传 `follow_type` 时默认为 `room`，行为不变
- 现有前端关注自习室功能不受影响

```

## openspec/changes/course-detail-page/specs/course-lessons/spec.md

- Source: openspec/changes/course-detail-page/specs/course-lessons/spec.md
- Lines: 1-28
- SHA256: 4021a93462675779705f211c3835675664cd6ccaa0d6c855f9394243a4dca5d4

```md
# Course Lessons

## ADDED Requirements

### REQ-CL-1: course_lessons 数据模型

新增 `course_lessons` 表，字段：
- `id`：主键（自增）
- `course_id`：外键关联 `courses.id`（NOT NULL）
- `title`：课时标题（String(200)，NOT NULL）
- `description`：课时描述（String(500)，nullable）
- `duration_minutes`：时长（分钟，Integer，nullable）
- `sort_order`：排序序号（Integer，默认 0）
- `is_free_preview`：是否免费试看（Boolean，默认 false）
- `created_at`：创建时间
- `updated_at`：更新时间

索引：`course_id` 上建索引，按 `(course_id, sort_order)` 排序查询。

### REQ-CL-2: 课时列表 API

课程详情 API 的响应中包含 `lessons` 字段，返回该课程的所有课时，按 `sort_order` 升序排列。

每个课时响应包含：`id`、`title`、`description`、`duration_minutes`、`sort_order`、`is_free_preview`。

### REQ-CL-3: 种子数据

为新表提供种子数据脚本，为现有活跃课程生成示例课时数据（每门课程 4-12 个课时），用于开发和测试。

```
