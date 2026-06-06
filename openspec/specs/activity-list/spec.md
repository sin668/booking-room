## Purpose
定义用户端热门活动能力，包括公开活动列表 API、活动详情 API、活动领券 API、响应结构和活动基础数据模型，确保小程序首页与活动详情页可以稳定展示活动内容。
## Requirements
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

### Requirement: 用户端活动详情 API
系统 SHALL 提供 `GET /api/v1/activities/{activity_id}/` 接口，返回已上架活动详情。响应 SHALL 包含活动基础字段、清洗后的活动富文本正文和活动卡券列表。

#### Scenario: 查询已上架活动详情
- **GIVEN** 活动已上架
- **WHEN** 客户端请求 `GET /api/v1/activities/1/`
- **THEN** 系统返回 HTTP 200
- **AND** 响应包含活动标题、描述、封面、参与人数、`content_html` 和 `activity_coupons`

#### Scenario: 活动详情返回安全富文本
- **GIVEN** 活动存在富文本正文
- **WHEN** 客户端请求活动详情
- **THEN** 系统返回清洗后的 `content_html`
- **AND** 响应不包含可执行脚本或事件属性

#### Scenario: 查询不存在的活动
- **GIVEN** 活动 ID 不存在
- **WHEN** 客户端请求 `GET /api/v1/activities/9999/`
- **THEN** 系统返回 HTTP 404

#### Scenario: 查询已下架活动
- **GIVEN** 活动已下架
- **WHEN** 客户端请求该活动详情
- **THEN** 系统返回 HTTP 404

### Requirement: 用户端活动领券 API
系统 SHALL 提供 `POST /api/v1/activities/{activity_id}/coupons/{activity_coupon_id}/claim` 接口，用于当前登录用户领取活动卡券。

#### Scenario: 领取成功
- **GIVEN** 用户已登录且满足领取条件
- **WHEN** 客户端请求活动领券接口
- **THEN** 系统返回 HTTP 200
- **AND** 响应包含新创建的用户卡券信息和最新领取状态

#### Scenario: 重复领取超限
- **GIVEN** 用户已达到该活动卡券每人限领数量
- **WHEN** 客户端请求活动领券接口
- **THEN** 系统返回 HTTP 409
- **AND** 响应包含可读错误信息
