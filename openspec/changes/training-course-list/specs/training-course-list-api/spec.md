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

#### Scenario: Successful list request with default pagination

- **WHEN** 客户端发送 `GET /api/v1/training/courses` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（课程数组）和 `total`、`page`、`page_size` 字段

#### Scenario: Filter courses by category

- **WHEN** 客户端发送 `GET /api/v1/training/courses?category=postgraduate`
- **THEN** 返回 HTTP 200，`items` 仅包含 `category=postgraduate` 的课程

#### Scenario: Filter by non-existent category

- **WHEN** 客户端发送 `GET /api/v1/training/courses?category=nonexistent`
- **THEN** 返回 HTTP 200，`items` 为空数组，`total` 为 0

### Requirement: Training room response schema

培训室列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`name`（字符串）、`description`（字符串，可空）、`cover_image`（字符串 URL，可空）、`address`（字符串）、`city_id`（整数或 null）、`city_name`（字符串或 null）、`business_hours`（字符串，可空）、`status`（字符串）、`room_type`（字符串，枚举 "study"/"training"/"comprehensive"）、`min_price`（数字）、`hot_courses`（数组，每项包含 `id`、`name`、`cover_image`、`teacher`（对象，含 `id`、`name`、`avatar`，可为 null）、`price`、`enrollment_count`）。

#### Scenario: Response field validation

- **WHEN** 客户端请求培训室列表
- **THEN** 每个 item 包含 `id`、`name`、`description`、`cover_image`、`address`、`business_hours`、`status`、`room_type`、`min_price`、`hot_courses` 字段，类型符合规范

#### Scenario: Training room with no hot courses

- **GIVEN** 培训室 id=1 没有任何 `is_hot=true` 的课程
- **WHEN** 客户端请求培训室列表
- **THEN** 该培训室的 `hot_courses` 为空数组

### Requirement: Course response schema

课程列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`name`（字符串）、`cover_image`（字符串 URL，可空）、`teacher`（对象，含 `id`、`name`、`avatar`、`title`、`rating`，可为 null）、`category`（字符串，枚举值 "primaryschool"/"middleschool"/"postgraduate"/"civil_service"/"language"/"skills"/"professional"）、`price`（数字，单位元/课时）、`rating`（数字）、`enrollment_count`（整数）、`schedule`（字符串，可空）、`tags`（数组，从逗号分隔字符串解析）、`status`（字符串）、`room_id`（整数）、`room_name`（字符串，所属培训室名称）。

#### Scenario: Response field validation

- **WHEN** 客户端请求课程列表
- **THEN** 每个 item 包含 `id`、`name`、`cover_image`、`teacher`、`category`、`price`、`rating`、`enrollment_count`、`schedule`、`tags`、`status`、`room_id`、`room_name` 字段

#### Scenario: Course with teacher

- **GIVEN** 课程关联了教师（teacher_id 不为 null）
- **WHEN** 客户端请求课程列表
- **THEN** 该课程的 `teacher` 字段包含 `id`、`name`、`avatar`、`title`、`rating` 信息

#### Scenario: Course without teacher

- **GIVEN** 课程未关联教师（teacher_id 为 null）
- **WHEN** 客户端请求课程列表
- **THEN** 该课程的 `teacher` 字段为 null

#### Scenario: Course tags parsing

- **GIVEN** 课程 `tags` 字段值为 "多媒体,小班,1对1"
- **WHEN** 客户端请求课程列表
- **THEN** 该课程的 `tags` 字段返回为 `["多媒体", "小班", "1对1"]`

#### Scenario: Course without tags

- **GIVEN** 课程 `tags` 字段值为 null
- **WHEN** 客户端请求课程列表
- **THEN** 该课程的 `tags` 字段返回为空数组 `[]`
