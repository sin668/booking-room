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

1. **数据库迁移**：
   - 添加 `description` 列到 `courses` 表
   - 创建 `course_lessons` 表
   - 添加 `follow_type` 列到 `room_follows`（默认 `room`，NOT NULL）
   - 修改 `room_follows` 唯一约束为 `(user_id, room_id, follow_type)`
   - 删除 `room_follows.room_id` 外键约束

2. **部署顺序**：先部署后端（API + 迁移），再部署前端

3. **回滚**：迁移 downgrade 删除新表和新列，恢复唯一约束和外键
