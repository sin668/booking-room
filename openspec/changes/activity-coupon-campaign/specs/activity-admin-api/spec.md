## ADDED Requirements

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
