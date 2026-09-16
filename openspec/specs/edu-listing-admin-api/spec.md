# edu-listing-admin-api Specification

## Purpose
定义「教培供需」后台审核 API 能力：管理员对供需信息进行筛选查询、通过、拒绝与下架，权限在后端强制执行。
## Requirements
### Requirement: 供需信息审核列表

系统 SHALL 提供 `GET /api/v1/admin/edu-listings` 返回供需信息审核列表，支持按 `keyword`（标题模糊匹配）、`listing_type`、`status` 筛选与分页，响应为 `{ items, total, page, page_size }`。每条 item MUST 携带发布者昵称与发布者认证状态摘要。该接口 MUST 要求管理员登录态。

#### Scenario: 按状态筛选待审核

- **Given** 存在多种审核状态的供需信息
- **When** 管理员请求列表并传 `status=pending`
- **Then** 返回的 `items` 仅包含待审核信息

#### Scenario: 关键词搜索

- **Given** 存在标题包含「数学」的供需信息
- **When** 管理员请求列表并传 `keyword=数学`
- **Then** 返回的 `items` 标题均匹配该关键词

### Requirement: 审核通过 / 拒绝 / 下架

系统 SHALL 提供审核操作接口，允许管理员将供需信息流转为 `approved`（通过）、`rejected`（拒绝）或 `offline`（下架）。拒绝 MUST 要求填写拒绝理由，否则返回 400/422。审核操作 MUST 记录审核时间与审核人。该接口 MUST 通过 `require_admin_permission` 在后端强制权限校验。

#### Scenario: 通过后出现在广场

- **Given** 一条 `pending` 状态的供需信息
- **When** 管理员执行通过操作
- **Then** 该信息 `status` 变为 `approved`，并可出现在 C 端综合广场列表中

#### Scenario: 拒绝必须填理由

- **Given** 一条 `pending` 状态的供需信息
- **When** 管理员执行拒绝操作但未提供拒绝理由
- **Then** 返回错误且不改变状态

#### Scenario: 下架已通过信息

- **Given** 一条 `approved` 状态的供需信息
- **When** 管理员执行下架操作
- **Then** 该信息 `status` 变为 `offline`，不再出现在 C 端综合广场列表中

#### Scenario: 无权限管理员被拒绝

- **Given** 一个不具备教培供需审核权限码的管理员
- **When** 调用审核操作接口
- **Then** 返回 403

