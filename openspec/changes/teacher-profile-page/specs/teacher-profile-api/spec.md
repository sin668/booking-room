## Purpose

教师详情 API 提供按教师 ID 查询单个教师详情的接口，返回教师基本信息及其所授活跃课程列表，支撑 br-app 教师简介页面的数据展示。

## ADDED Requirements

### Requirement: Get teacher detail API

系统 SHALL 提供 `GET /api/v1/teachers/{teacher_id}` 接口，按教师 ID 返回教师详情。响应 SHALL 包含教师基本信息和该教师所授的所有活跃课程列表。路由定义不使用尾部斜杠。

#### Scenario: Successful detail request for teacher with courses

- **GIVEN** 一位 id=1 的教师，关联了 3 门 `status=active` 的课程
- **WHEN** 客户端发送 `GET /api/v1/teachers/1`
- **THEN** 返回 HTTP 200，响应包含教师基本信息（id、name、avatar、title、rating、bio、student_count）和 `courses` 数组
- **AND** 每门课程包含 id、name、cover_image、category、price、rating、enrollment_count、schedule、tags（数组）、status、room_id、room_name、lesson_count（课时数）

#### Scenario: Teacher with no courses

- **GIVEN** 一位 id=2 的教师，未关联任何活跃课程
- **WHEN** 客户端发送 `GET /api/v1/teachers/2`
- **THEN** 返回 HTTP 200，`courses` 数组为空

#### Scenario: Non-existent teacher returns 404

- **WHEN** 客户端发送 `GET /api/v1/teachers/999`
- **THEN** 返回 HTTP 404，错误信息说明教师不存在

#### Scenario: Teacher detail includes bio and student_count

- **GIVEN** 一位 id=1 的教师，`bio` 字段为 "专注考研政治辅导8年"，`student_count` 为 328
- **WHEN** 客户端发送 `GET /api/v1/teachers/1`
- **THEN** 响应中 `bio` 为 "专注考研政治辅导8年"，`student_count` 为 328

#### Scenario: Teacher with null bio

- **GIVEN** 一位 id=3 的教师，`bio` 字段为 null
- **WHEN** 客户端发送 `GET /api/v1/teachers/3`
- **THEN** 响应中 `bio` 为 null

#### Scenario: Course lesson_count in response

- **GIVEN** 教师 id=1 的一门课程关联了 12 个课时（course_lessons 记录）
- **WHEN** 客户端发送 `GET /api/v1/teachers/1`
- **THEN** 该课程的 `lesson_count` 为 12
