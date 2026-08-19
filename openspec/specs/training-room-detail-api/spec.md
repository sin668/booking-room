## Purpose

培训室详情 API 提供按房间 ID 查询单个培训室详情的接口，返回培训室基本信息、关联教师列表和课程列表，支撑 br-app 培训室概况页面的数据展示。

## Requirements

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
