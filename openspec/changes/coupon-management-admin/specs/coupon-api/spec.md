## MODIFIED Requirements

### Requirement: 卡券适用范围规则
系统 SHALL 支持四类适用范围：全场通用、首次预约、VIP专享、指定座位类型。全场通用卡券可用于任意座位预约；首次预约卡券 MUST 仅对没有成功预约历史的用户可用；VIP专享卡券 MUST 仅对 `membership_level` 为 `vip` 或 `svip` 的用户可用；指定座位类型卡券 MUST 仅对对应 `seat.zone` 的订单可用。

#### Scenario: 全场通用卡券可用于任意座位
- **GIVEN** 用户拥有全场通用卡券
- **WHEN** 用户预约任意可预约座位
- **THEN** 该卡券满足适用范围校验

#### Scenario: 首次预约卡券仅对首次预约可用
- **GIVEN** 用户拥有首次预约卡券
- **WHEN** 用户没有 `confirmed` 或 `completed` 预约历史
- **THEN** 该卡券满足适用范围校验

#### Scenario: VIP专享卡券仅对VIP用户可用
- **GIVEN** 用户拥有 VIP 专享卡券（scope=vip_only）
- **WHEN** 用户 `membership_level` 为 `vip` 或 `svip`
- **THEN** 该卡券满足适用范围校验

#### Scenario: 非VIP用户无法使用VIP专享卡券
- **GIVEN** 用户拥有 VIP 专享卡券（scope=vip_only）
- **WHEN** 用户 `membership_level` 为 `none`
- **THEN** 该卡券不满足适用范围校验
- **AND** 预约可用卡券接口不返回该卡券

#### Scenario: 指定座位类型卡券仅匹配对应区域
- **GIVEN** 用户拥有仅限 `vip` 座位的卡券
- **WHEN** 用户预约 `seat.zone` 为 `vip` 的座位
- **THEN** 该卡券满足适用范围校验

#### Scenario: VIP专享卡券不出现在非VIP用户卡券列表
- **GIVEN** 用户 `membership_level` 为 `none` 且拥有 VIP 专享卡券
- **WHEN** 用户请求 `GET /api/v1/coupons?status=available`
- **THEN** 系统不返回该 VIP 专享卡券
