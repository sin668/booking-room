# Design: 课程详情页

## Context

br-app 已有培训课程列表页（`training/index.vue`）和自习室详情页（`booking/detail.vue`）。课程详情页需要复用自习室详情页的视觉模式（Hero 图 + 上浮信息卡 + 底部操作栏 + 心形关注按钮），但内容结构不同（课程有教师、目录、评价等）。

关注功能现有 `room_follows` 表 + `followedRooms.js` 服务，需要扩展支持课程类型。

## Goals / Non-Goals

**Goals**：
- 实现与原型高度一致的课程详情页 UI
- 复用自习室详情页的视觉模式，保持设计一致性
- 通过 `follow_type` 字段扩展关注表，避免新建独立表
- 后端课程详情 API 包含相关课程推荐

**Non-Goals**：
- 不实现课时/章节数据模型（原型中的课程目录使用静态占位数据）
- 不实现评价系统（原型中的评价使用静态占位数据）
- 不实现课程预约流程（底部「立即预约」暂为占位）
- 不实现教师详情页（点击跳转占位）

## Decisions

### D-1: 课程详情 API 路由设计

**选择**：`GET /api/v1/training/courses/{course_id}`，复用现有 training router。

**理由**：与现有 `/api/v1/training/courses`（列表）和 `/api/v1/training/rooms/{room_id}`（培训室详情）保持一致的路由风格。

**替代方案**：新建 course router → 增加路由复杂度，无实质收益。

### D-2: follow_type 扩展方案

**选择**：在 `room_follows` 表添加 `follow_type` 列（String(20)，默认 `room`），修改唯一约束为 `(user_id, room_id, follow_type)`。`follow_type=course` 时 `room_id` 存储 `course_id`。

**理由**：
- 用户明确要求「库表也使用一样的，加上类型来区分」
- 避免新建独立表，减少维护成本
- 默认值 `room` 确保现有数据和 API 向后兼容

**替代方案**：
- 新建 `course_follows` 表 → 违反用户要求，增加表数量
- 使用通用 `follows` 表（多态关联）→ 过度设计

### D-3: 前端关注服务分离

**选择**：新建 `followedCourses.js` 服务，与 `followedRooms.js` 平行。

**理由**：
- 课程和自习室的本地缓存数据结构不同（课程无 address、city 等字段）
- 使用独立 storage key `followed_courses` 避免数据混淆
- 两个服务都调用相同的 `roomFollows.js` API 层，只是传不同 `follow_type`

### D-4: 课程详情页组件架构

**选择**：单文件组件 `course-detail.vue`，使用 Options API（与项目现有页面一致）。

**理由**：
- 项目现有页面（`booking/detail.vue`、`training/index.vue`）均使用 Options API 或 `<script setup>`，但详情页（`booking/detail.vue`）使用 Options API
- 单文件组件足够，无需拆分子组件（页面内容不复杂）
- 与自习室详情页保持一致的代码风格

### D-5: 课程目录和评价数据

**选择**：前端使用静态占位数据，不从后端获取。

**理由**：
- 当前数据库无 `lessons` 和 `reviews` 表
- 原型中的目录和评价为展示效果，实际数据需要后续迭代
- 避免为占位数据创建临时表和 API

## Risks / Trade-offs

- **[follow_type 语义]** `room_id` 列在 `follow_type=course` 时存储 `course_id`，字段名与实际含义不一致 → 可接受，因为外键约束已移除（`course_id` 不引用 `study_rooms.id`），且查询时按 `follow_type` 过滤不会产生歧义。但需要注意：`follow_type=course` 的记录不能有 `ForeignKey("study_rooms.id")` 约束。
  - **缓解**：迁移时不添加外键约束到 `room_id` 对 courses 的引用，仅在应用层保证一致性。或者，由于 `room_id` 已有外键指向 `study_rooms.id`，需要在迁移中处理——将 `follow_type=course` 的 `room_id` 值改为存储课程所属的 `room_id`，或者删除外键约束改为软引用。
  - **最终方案**：迁移时删除 `room_id` 的外键约束，改为普通 Integer 列 + 应用层校验。`follow_type=room` 时 `room_id` 引用 `study_rooms.id`，`follow_type=course` 时 `room_id` 存储 `course_id`。

- **[原型静态数据]** 课程目录和评价使用前端占位数据，后续迭代需要替换 → 在组件中预留数据接口，方便后续对接。

## Migration Plan

1. **数据库迁移**：
   - 添加 `follow_type` 列到 `room_follows`（默认 `room`，NOT NULL）
   - 修改唯一约束为 `(user_id, room_id, follow_type)`
   - 删除 `room_id` 外键约束（改为软引用）
   - 添加 `description` 列到 `courses` 表

2. **部署顺序**：先部署后端（API + 迁移），再部署前端

3. **回滚**：迁移 downgrade 删除新列，恢复唯一约束和外键
