## ADDED Requirements

### Requirement: 用户卡券来源记录
系统 SHALL 支持记录用户卡券来源。通过活动领取生成的用户卡券 SHALL 记录来源类型、来源活动 ID 和来源活动卡券配置 ID。

#### Scenario: 活动领券生成来源记录
- **GIVEN** 用户通过活动详情领取卡券成功
- **WHEN** 系统创建用户卡券记录
- **THEN** 用户卡券包含 `source_type=activity`
- **AND** 用户卡券包含来源活动 ID 和来源活动卡券配置 ID

### Requirement: 活动来源卡券参与现有卡券查询
系统 SHALL 在用户卡券列表和预约可用卡券接口中返回活动来源卡券，并按既有卡券状态、有效期、门槛和适用范围规则进行过滤。

#### Scenario: 查询活动来源可用卡券
- **GIVEN** 用户拥有一张活动来源的未使用且未过期卡券
- **WHEN** 用户请求 `GET /api/v1/coupons?status=available`
- **THEN** 系统返回该卡券
- **AND** 响应包含来源活动信息或来源类型

#### Scenario: 预约查询过滤不可用活动卡券
- **GIVEN** 用户拥有一张活动来源卡券
- **AND** 该卡券不满足当前预约订单门槛
- **WHEN** 用户查询预约可用卡券
- **THEN** 系统不返回该卡券
