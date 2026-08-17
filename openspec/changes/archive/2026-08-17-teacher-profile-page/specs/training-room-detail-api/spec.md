## MODIFIED Requirements

### Requirement: Teacher response includes bio and student_count fields

培训室详情 API 的教师响应结构 SHALL 在现有字段（id、name、avatar、title、rating）基础上新增 `bio`（个人简介，可为 null）和 `student_count`（学员数量，整数，默认 0）字段。

#### Scenario: Teacher with bio in training room detail

- **GIVEN** 培训室 id=1 的一位教师 bio 为 "专注考研政治辅导8年"，student_count 为 328
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** `teachers` 数组中该教师的 `bio` 为 "专注考研政治辅导8年"，`student_count` 为 328

#### Scenario: Teacher with null bio in training room detail

- **GIVEN** 培训室 id=1 的一位教师 bio 为 null
- **WHEN** 客户端发送 `GET /api/v1/training/rooms/1`
- **THEN** `teachers` 数组中该教师的 `bio` 为 null，`student_count` 为 0
