## ADDED Requirements

### Requirement: List banners API
系统 SHALL 提供 `GET /api/v1/banners/` 接口，返回当前生效的轮播图列表。仅返回 `is_active=true` 的轮播图，按 `sort_order` 升序排列。无需分页（轮播图数量有限，全量返回）。

#### Scenario: Successful banners request
- **WHEN** 客户端发送 `GET /api/v1/banners/`
- **THEN** 返回 HTTP 200，响应为轮播图数组，仅包含 `is_active=true` 的记录，按 `sort_order` 升序

#### Scenario: No active banners
- **WHEN** 数据库中无 `is_active=true` 的轮播图
- **THEN** 返回 HTTP 200，响应为空数组 `[]`

### Requirement: Banner response schema
轮播图列表响应中每个 item SHALL 包含以下字段：`id`（整数）、`image_url`（字符串 URL）、`title`（字符串，轮播图标题文字）、`subtitle`（字符串，可空，轮播图副标题）、`cta_text`（字符串，可空，CTA 按钮文案，如"立即领取"）、`link_type`（枚举 "none"/"page"/"room"/"url"）、`link_value`（字符串，可空）、`sort_order`（整数）。

#### Scenario: Response field validation
- **WHEN** 客户端请求轮播图列表
- **THEN** 每个 item 包含 `id`、`image_url`、`title`、`subtitle`、`cta_text`、`link_type`、`link_value`、`sort_order` 字段，类型符合规范

### Requirement: Banner database model
系统 SHALL 创建 `banners` 表，包含字段：`id`（主键，自增）、`image_url`（VARCHAR，非空）、`title`（VARCHAR，非空，轮播图标题）、`subtitle`（VARCHAR，可空，副标题）、`cta_text`（VARCHAR，可空，CTA 按钮文案）、`link_type`（VARCHAR，默认 "none"，枚举值 "none"/"page"/"room"/"url"）、`link_value`（VARCHAR，可空）、`sort_order`（整数，默认 0）、`is_active`（布尔，默认 true）、`created_at`、`updated_at`。

#### Scenario: Create banner record
- **WHEN** 向 `banners` 表插入一条记录，`image_url="https://example.com/banner1.jpg"`，`title="新用户首单立减20元"`，`cta_text="立即领取"`，`sort_order=1`
- **THEN** 记录成功创建，`link_type` 默认为 "none"，`is_active` 默认为 true，`sort_order` 为 1
