## ADDED Requirements

### Requirement: List activities API
系统 SHALL 提供 `GET /api/v1/activities/` 接口，返回热门活动列表。仅返回 `is_active=true` 的活动，按 `sort_order` 升序排列。无需分页（活动数量有限，全量返回）。

#### Scenario: Successful activities request
- **WHEN** 客户端发送 `GET /api/v1/activities/`
- **THEN** 返回 HTTP 200，响应为活动数组，仅包含 `is_active=true` 的记录，按 `sort_order` 升序

#### Scenario: No active activities
- **WHEN** 数据库中无 `is_active=true` 的活动
- **THEN** 返回 HTTP 200，响应为空数组 `[]`

#### Scenario: Admin deactivates activity
- **WHEN** 管理员通过管理端将某活动的 `is_active` 设为 false
- **THEN** 小程序端 `GET /api/v1/activities/` 不再返回该活动

### Requirement: Activity response schema
活动列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`title`（字符串，活动标题）、`description`（字符串，活动描述）、`cover_image`（字符串 URL）、`participant_count`（整数，参与人数展示值）。

#### Scenario: Response field validation
- **WHEN** 客户端请求活动列表
- **THEN** 每个 item 包含 `id`、`title`、`description`、`cover_image`、`participant_count` 字段，类型符合规范

### Requirement: Activity database model
系统 SHALL 创建 `activities` 表，包含字段：`id`（主键，自增）、`title`（VARCHAR，非空）、`description`（VARCHAR，可空）、`cover_image`（VARCHAR，可空）、`participant_count`（整数，默认 0，展示用参与人数）、`sort_order`（整数，默认 0）、`is_active`（布尔，默认 true）、`created_at`、`updated_at`。

#### Scenario: Create activity record
- **WHEN** 向 `activities` 表插入一条记录，`title="沉浸式学习挑战赛"`，`description="累计学习24小时赢好礼"`，`participant_count=326`
- **THEN** 记录成功创建，`is_active` 默认为 true，`participant_count` 为 326
