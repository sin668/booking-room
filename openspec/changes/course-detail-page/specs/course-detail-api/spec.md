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
- `related_courses`：相关课程列表（同分类其他课程，最多 6 门）

**错误场景**：
- 课程不存在 → 404
- 课程状态非 `active` → 404

### REQ-CDA-2: 课程介绍字段

Course 模型新增可选 `description` 字段（String(1000)），用于存储课程详细介绍文本。该字段在课程列表 API 中不返回（避免带宽浪费），仅在详情 API 中返回。

### REQ-CDA-3: 相关课程查询

详情 API 返回的 `related_courses` 字段包含同分类下其他活跃课程（排除当前课程），按 `sort_order` 排序，最多返回 6 门。每门课程包含 `id`、`name`、`cover_image`、`price`。
