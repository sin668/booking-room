## Purpose
定义管理端活动管理 API，包括活动列表、创建、详情、更新、删除、上下架、富文本正文、关联卡券配置和活动数据结构，确保运营人员可在后台完整维护活动及其发券规则。
## Requirements
### Requirement: Paginated activity list API
系统 SHALL 提供 `GET /api/v1/admin/activities/` 接口，返回分页活动列表，支持关键词搜索和状态筛选。返回所有活动（含已下架），按 `created_at` 降序排列。

#### Scenario: Successful paginated request
- **WHEN** 管理员发送 `GET /api/v1/admin/activities/?page=1&page_size=10`
- **THEN** 返回 HTTP 200，响应包含 `total`（总数）、`page`（当前页码）、`page_size`（每页数量）、`items`（活动数组）

#### Scenario: Search by keyword
- **WHEN** 管理员发送 `GET /api/v1/admin/activities/?keyword=学习`
- **THEN** 返回标题或描述中包含"学习"的活动列表

#### Scenario: Filter by active status
- **WHEN** 管理员发送 `GET /api/v1/admin/activities/?is_active=true`
- **THEN** 仅返回 `is_active=true` 的活动

#### Scenario: Empty result set
- **WHEN** 数据库中无匹配的活动记录
- **THEN** 返回 HTTP 200，`items` 为空数组，`total` 为 0

### Requirement: Create activity API
系统 SHALL 提供 `POST /api/v1/admin/activities/` 接口，创建新活动。

#### Scenario: Successful creation
- **WHEN** 管理员发送 `POST /api/v1/admin/activities/`，body 包含 `title="沉浸式学习挑战赛"`、`description="累计学习24小时赢好礼"`、`cover_image="https://example.com/img.jpg"`、`participant_count=0`、`sort_order=1`、`is_active=true`
- **THEN** 返回 HTTP 201，响应包含新创建的活动完整信息（含 `id`、`created_at`、`updated_at`）

#### Scenario: Missing required field
- **WHEN** 管理员发送 `POST /api/v1/admin/activities/`，body 缺少 `title`
- **THEN** 返回 HTTP 422，响应包含字段校验错误信息

### Requirement: Get activity detail API
系统 SHALL 提供 `GET /api/v1/admin/activities/{activity_id}/` 接口，返回活动详情。

#### Scenario: Successful detail request
- **WHEN** 管理员发送 `GET /api/v1/admin/activities/1/`
- **THEN** 返回 HTTP 200，响应包含该活动的所有字段（含 `sort_order`、`is_active`、`created_at`、`updated_at`）

#### Scenario: Activity not found
- **WHEN** 管理员请求不存在的活动 ID
- **THEN** 返回 HTTP 404，响应包含错误信息

### Requirement: Update activity API
系统 SHALL 提供 `PUT /api/v1/admin/activities/{activity_id}/` 接口，更新活动信息。仅更新请求中包含的字段。

#### Scenario: Successful update
- **WHEN** 管理员发送 `PUT /api/v1/admin/activities/1/`，body 包含 `title="更新后的标题"`
- **THEN** 返回 HTTP 200，响应包含更新后的活动信息，`title` 为"更新后的标题"，`updated_at` 自动刷新

#### Scenario: Activity not found
- **WHEN** 管理员更新不存在的活动 ID
- **THEN** 返回 HTTP 404

### Requirement: Delete activity API
系统 SHALL 提供 `DELETE /api/v1/admin/activities/{activity_id}/` 接口，删除活动。

#### Scenario: Successful deletion
- **WHEN** 管理员发送 `DELETE /api/v1/admin/activities/1/`
- **THEN** 返回 HTTP 204，活动记录从数据库中删除

#### Scenario: Activity not found
- **WHEN** 管理员删除不存在的活动 ID
- **THEN** 返回 HTTP 404

### Requirement: Toggle activity status API
系统 SHALL 提供 `PATCH /api/v1/admin/activities/{activity_id}/status/` 接口，切换活动上下架状态。

#### Scenario: Successful toggle to active
- **WHEN** 管理员发送 `PATCH /api/v1/admin/activities/1/status/`，body 包含 `is_active=true`
- **THEN** 返回 HTTP 200，活动 `is_active` 更新为 true

#### Scenario: Successful toggle to inactive
- **WHEN** 管理员发送 `PATCH /api/v1/admin/activities/1/status/`，body 包含 `is_active=false`
- **THEN** 返回 HTTP 200，活动 `is_active` 更新为 false，该活动不再出现在小程序端公开列表中

#### Scenario: Activity not found
- **WHEN** 管理员切换不存在的活动 ID 的状态
- **THEN** 返回 HTTP 404

### Requirement: Admin activity response schema
管理端活动响应 SHALL 包含所有字段：`id`（整数）、`title`（字符串）、`description`（字符串，可空）、`cover_image`（字符串 URL，可空）、`participant_count`（整数）、`sort_order`（整数）、`is_active`（布尔）、`created_at`（日期时间字符串）、`updated_at`（日期时间字符串）。

#### Scenario: Response field validation
- **WHEN** 管理员请求活动详情或列表
- **THEN** 每个 item 包含上述所有字段，类型符合规范

### Requirement: Admin activity request schema
创建/更新活动请求 SHALL 包含：`title`（字符串，必填，最长 100 字符）、`description`（字符串，可空，最长 500 字符）、`cover_image`（字符串 URL，可空，最长 512 字符）、`participant_count`（整数，默认 0，最小 0）、`sort_order`（整数，默认 0）、`is_active`（布尔，默认 true）。

#### Scenario: Create request with all fields
- **WHEN** 管理员提交包含所有字段的创建请求
- **THEN** 系统使用提供的值创建活动记录

#### Scenario: Create request with defaults
- **WHEN** 管理员仅提交 `title` 字段
- **THEN** 系统使用默认值创建：`participant_count=0`、`sort_order=0`、`is_active=true`

### Requirement: 管理端活动富文本正文
系统 SHALL 允许管理端在创建和更新活动时提交活动详情富文本正文。富文本正文 SHALL 保存为活动详情字段，并在保存前过滤脚本、事件属性和不允许的标签。

#### Scenario: 创建活动时提交富文本正文
- **GIVEN** 管理员拥有活动管理权限
- **WHEN** 管理员请求 `POST /api/v1/admin/activities/` 并提交 `content_html`
- **THEN** 系统保存清洗后的活动富文本正文
- **AND** 管理端活动详情响应返回该富文本正文

#### Scenario: 富文本包含脚本内容
- **GIVEN** 管理员拥有活动管理权限
- **WHEN** 管理员提交包含 `<script>` 或事件属性的 `content_html`
- **THEN** 系统保存前移除不安全内容
- **AND** 响应中不包含可执行脚本

### Requirement: 管理端活动卡券请求字段
系统 SHALL 允许管理端在创建和更新活动时提交 `activity_coupons` 字段。每个活动卡券配置 SHALL 包含卡券模板信息或卡券模板 ID、总库存、每人限领数量、领取开始时间、领取结束时间、启用状态、排序和展示文案。

#### Scenario: 创建活动时提交关联卡券
- **GIVEN** 管理员拥有活动管理权限
- **WHEN** 管理员请求 `POST /api/v1/admin/activities/` 并提交活动基础信息和 `activity_coupons`
- **THEN** 系统创建活动
- **AND** 系统创建或关联卡券模板
- **AND** 系统保存活动卡券配置

#### Scenario: 每人限领数量无效
- **GIVEN** 管理员拥有活动管理权限
- **WHEN** 管理员提交 `per_user_limit` 小于 1 的活动卡券配置
- **THEN** 系统返回 HTTP 422
- **AND** 不保存该活动卡券配置

### Requirement: 管理端活动详情返回关联卡券
系统 SHALL 在管理端活动详情接口中返回活动关联卡券配置，包含卡券规则、库存、已领取数量、每人限领数量、领取时间、启用状态、排序和展示文案。

#### Scenario: 查看活动详情中的卡券配置
- **GIVEN** 活动存在且已配置活动卡券
- **WHEN** 管理员请求 `GET /api/v1/admin/activities/{activity_id}/`
- **THEN** 系统返回 HTTP 200
- **AND** 响应包含 `activity_coupons` 数组

### Requirement: 管理端活动卡券发布校验
系统 SHALL 在活动发布或上架时校验启用的活动卡券配置。启用的活动卡券 MUST 关联启用的卡券模板，且总库存不得小于已领取数量。

#### Scenario: 发布包含有效卡券的活动
- **GIVEN** 活动包含启用且配置完整的活动卡券
- **WHEN** 管理员将活动上架
- **THEN** 系统返回 HTTP 200
- **AND** 用户端活动详情可展示该活动卡券

#### Scenario: 发布包含无效卡券的活动
- **GIVEN** 活动包含启用但未关联有效卡券模板的活动卡券
- **WHEN** 管理员将活动上架
- **THEN** 系统返回 HTTP 422
- **AND** 活动上架状态不变

### Requirement: 管理端活动卡券编辑保护
系统 SHALL 允许管理员编辑活动卡券展示文案、领取时间、启用状态和排序。对于已产生领取记录的活动卡券，系统 MUST 禁止将总库存调整为小于已领取数量。

#### Scenario: 调整库存低于已领取数量
- **GIVEN** 活动卡券总库存为 100 且已领取数量为 20
- **WHEN** 管理员将总库存修改为 10
- **THEN** 系统返回 HTTP 422
- **AND** 原库存配置保持不变
