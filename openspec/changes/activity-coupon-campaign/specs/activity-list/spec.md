## ADDED Requirements

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
