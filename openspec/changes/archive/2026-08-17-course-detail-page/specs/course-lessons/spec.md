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
