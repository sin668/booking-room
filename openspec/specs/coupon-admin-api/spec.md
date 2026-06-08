# coupon-admin-api Specification

## Purpose
TBD - created by archiving change coupon-management-admin. Update Purpose after archive.
## Requirements
### Requirement: 管理后台卡券列表查询接口
系统 SHALL 提供 `GET /api/v1/admin/coupons` 接口，返回卡券模板分页列表。接口 SHALL 支持按关键词（名称）、卡券类型（`type`）、适用范围（`scope`）和启用状态（`is_active`）筛选。所有接口 MUST 经过 RBAC 权限校验。

#### Scenario: 分页查询卡券列表
- **GIVEN** 管理员已登录并具有卡券管理权限
- **WHEN** 管理员请求 `GET /api/v1/admin/coupons?page=1&page_size=10`
- **THEN** 系统返回 HTTP 200
- **AND** 响应包含 total、page、page_size 和 items 数组
- **AND** 每个 item 包含 id、name、description、type、discount_amount、discount_percent、min_order_amount、scope、seat_zone、valid_from、expires_at、is_active、created_at、updated_at

#### Scenario: 按关键词搜索卡券
- **GIVEN** 系统存在名称包含"新用户"的卡券
- **WHEN** 管理员请求 `GET /api/v1/admin/coupons?keyword=新用户`
- **THEN** 响应 items 仅包含名称匹配的卡券

#### Scenario: 按类型筛选
- **GIVEN** 系统存在类型为 `threshold_amount_off` 和 `percentage_off` 的卡券
- **WHEN** 管理员请求 `GET /api/v1/admin/coupons?type=threshold_amount_off`
- **THEN** 响应 items 仅包含满减券

#### Scenario: 无权限访问
- **GIVEN** 管理员无卡券管理权限
- **WHEN** 请求 `GET /api/v1/admin/coupons`
- **THEN** 系统返回 HTTP 403

### Requirement: 管理后台卡券详情查询接口
系统 SHALL 提供 `GET /api/v1/admin/coupons/{id}` 接口，返回单个卡券模板详情。

#### Scenario: 查询存在的卡券
- **GIVEN** 系统存在 id 为 1 的卡券
- **WHEN** 管理员请求 `GET /api/v1/admin/coupons/1`
- **THEN** 系统返回 HTTP 200
- **AND** 响应包含该卡券的完整字段

#### Scenario: 查询不存在的卡券
- **WHEN** 管理员请求 `GET /api/v1/admin/coupons/999`
- **THEN** 系统返回 HTTP 404

### Requirement: 管理后台创建卡券接口
系统 SHALL 提供 `POST /api/v1/admin/coupons` 接口，创建新卡券模板。必填字段为 name、type、valid_from、expires_at。type 为 `threshold_amount_off` 时 discount_amount MUST 非空且 min_order_amount > 0；type 为 `amount_off` 时 discount_amount MUST 非空且 min_order_amount 可为 0；type 为 `percentage_off` 时 discount_percent MUST 在 1-99 之间。

#### Scenario: 创建满减券
- **GIVEN** 管理员具有卡券管理权限
- **WHEN** 管理员提交 `{ name: "满20减3", type: "threshold_amount_off", discount_amount: 3, min_order_amount: 20, scope: "all", valid_from: "2026-06-01", expires_at: "2026-12-31" }`
- **THEN** 系统返回 HTTP 201
- **AND** 创建的卡券 is_active 默认为 true

#### Scenario: 创建折扣券
- **WHEN** 管理员提交 `{ name: "VIP8折", type: "percentage_off", discount_percent: 80, scope: "vip_only", valid_from: "2026-06-01", expires_at: "2026-12-31" }`
- **THEN** 系统返回 HTTP 201

#### Scenario: 缺少必填字段
- **WHEN** 管理员提交 `{ name: "测试券" }` 缺少 type、valid_from、expires_at
- **THEN** 系统返回 HTTP 422
- **AND** 响应包含缺失字段的校验错误信息

#### Scenario: 优惠规则与类型不匹配
- **WHEN** 管理员提交 type 为 `percentage_off` 但提供了 discount_amount 而非 discount_percent
- **THEN** 系统返回 HTTP 422

### Requirement: 管理后台更新卡券接口
系统 SHALL 提供 `PUT /api/v1/admin/coupons/{id}` 接口，更新卡券模板。仅允许修改未关联任何活动卡券配置或所有关联活动卡券配置均已停用的卡券的 type 和优惠规则字段。

#### Scenario: 更新卡券名称
- **GIVEN** 存在 id 为 1 的卡券
- **WHEN** 管理员提交 `{ name: "新名称" }`
- **THEN** 系统返回 HTTP 200
- **AND** 卡券名称更新为"新名称"

#### Scenario: 更新已关联活动卡券的类型
- **GIVEN** 卡券 id 为 1 且存在启用的 ActivityCoupon 关联
- **WHEN** 管理员尝试修改 type 字段
- **THEN** 系统返回 HTTP 409
- **AND** 响应提示该卡券已被活动关联，无法修改类型

### Requirement: 管理后台卡券启停接口
系统 SHALL 提供 `PATCH /api/v1/admin/coupons/{id}/status` 接口，切换卡券启用/停用状态。

#### Scenario: 停用卡券
- **GIVEN** 存在启用的卡券
- **WHEN** 管理员提交 `{ is_active: false }`
- **THEN** 系统返回 HTTP 200
- **AND** 该卡券不再出现在用户可用卡券列表中

#### Scenario: 启用卡券
- **GIVEN** 存在停用的卡券且未过期
- **WHEN** 管理员提交 `{ is_active: true }`
- **THEN** 系统返回 HTTP 200

#### Scenario: 启用已过期卡券
- **GIVEN** 存在停用且已过期的卡券
- **WHEN** 管理员尝试启用
- **THEN** 系统返回 HTTP 400
- **AND** 响应提示卡券已过期，无法启用

### Requirement: 管理后台卡券删除接口
系统 SHALL 提供 `DELETE /api/v1/admin/coupons/{id}` 接口，删除卡券模板。仅允许删除未被任何活动卡券配置关联的卡券。

#### Scenario: 删除未关联卡券
- **GIVEN** 卡券未被任何 ActivityCoupon 关联
- **WHEN** 管理员请求删除
- **THEN** 系统返回 HTTP 200

#### Scenario: 删除已关联卡券
- **GIVEN** 卡券被 ActivityCoupon 关联
- **WHEN** 管理员请求删除
- **THEN** 系统返回 HTTP 409
- **AND** 响应提示存在活动关联，无法删除

