## MODIFIED Requirements

### Requirement: List training courses API

系统 SHALL 提供 `GET /api/v1/training/courses` 接口，返回按分类过滤的课程分页列表。支持查询参数 `page`（默认 1）、`page_size`（默认 10，最大 50）、`category`（可选，枚举值 "primaryschool"/"middleschool"/"postgraduate"/"civil_service"/"language"/"skills"/"professional"）、`city_id`（可选，整数，≥1）。仅返回 `status=active` 的课程。当 `category` 为空时返回全部分类的课程。当传入 `city_id` 时，按课程所属培训室的城市过滤：仅返回所属培训室 `city_id` 等于指定值，或所属培训室未设置城市（`city_id` 为 null）的课程，与培训室列表的城市过滤口径一致。

#### Scenario: Successful list request with default pagination

- **WHEN** 客户端发送 `GET /api/v1/training/courses` 不带查询参数
- **THEN** 返回 HTTP 200，响应包含 `items`（课程数组）和 `total`、`page`、`page_size` 字段

#### Scenario: Filter courses by category

- **WHEN** 客户端发送 `GET /api/v1/training/courses?category=postgraduate`
- **THEN** 返回 HTTP 200，`items` 仅包含 `category=postgraduate` 的课程

#### Scenario: Filter by non-existent category

- **WHEN** 客户端发送 `GET /api/v1/training/courses?category=nonexistent`
- **THEN** 返回 HTTP 200，`items` 为空数组，`total` 为 0

#### Scenario: Filter courses by city

- **GIVEN** 课程 A 所属培训室 `city_id=1`，课程 B 所属培训室 `city_id=2`，两者均为 `status=active` 且有进行中的固定班课排课
- **WHEN** 客户端发送 `GET /api/v1/training/courses?city_id=1`
- **THEN** 返回 HTTP 200，`items` 仅包含课程 A，不包含课程 B，`total` 等于命中城市的课程数

#### Scenario: Courses in rooms without city always visible

- **GIVEN** 课程 C 所属培训室 `city_id` 为 null（未设置城市），且为 `status=active` 并有进行中的固定班课排课
- **WHEN** 客户端发送 `GET /api/v1/training/courses?city_id=1`
- **THEN** 返回 HTTP 200，`items` 包含课程 C
