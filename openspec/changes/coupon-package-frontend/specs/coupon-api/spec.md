## ADDED Requirements

### Requirement: 卡券数据库模型
系统 SHALL 提供卡券模板表 `coupons` 和用户卡券表 `user_coupons`。`coupons` SHALL 保存卡券规则，包括名称、说明、类型、金额/折扣、使用门槛、适用范围、生效时间、过期时间和启用状态。`user_coupons` SHALL 保存用户持有卡券，包括用户、卡券模板、状态、使用订单和使用时间。

#### Scenario: 创建用户卡券记录
- **GIVEN** 系统存在一张启用的卡券模板
- **WHEN** 后台或种子数据为用户创建 `user_coupons` 记录
- **THEN** 用户卡券关联该用户和卡券模板
- **AND** 初始状态为 `available`

### Requirement: 卡券类型规则
系统 SHALL 支持三类卡券：满减券、立减券、折扣券。满减券 SHALL 在订单原价达到门槛时抵扣固定金额；立减券 SHALL 不要求门槛或门槛为 0 时抵扣固定金额；折扣券 SHALL 按折扣比例计算抵扣金额。所有金额计算 MUST 使用 Decimal 并保留 2 位小数。

#### Scenario: 满减券抵扣
- **GIVEN** 用户拥有“满20减3”卡券
- **WHEN** 订单原价为 24.00
- **THEN** 抵扣金额为 3.00
- **AND** 实付金额为 21.00

#### Scenario: 立减券抵扣
- **GIVEN** 用户拥有“首单立减20”卡券
- **WHEN** 订单原价为 18.00
- **THEN** 抵扣金额为 18.00
- **AND** 实付金额为 0.00

#### Scenario: 折扣券抵扣
- **GIVEN** 用户拥有“VIP专享8折”卡券
- **WHEN** 订单原价为 50.00
- **THEN** 抵扣金额为 10.00
- **AND** 实付金额为 40.00

### Requirement: 卡券适用范围规则
系统 SHALL 支持三类适用范围：全场通用、首次预约、指定座位类型。首次预约卡券 MUST 仅对没有成功预约历史的用户可用；指定座位类型卡券 MUST 仅对对应 `seat.zone` 的订单可用。

#### Scenario: 全场通用卡券可用于任意座位
- **GIVEN** 用户拥有全场通用卡券
- **WHEN** 用户预约任意可预约座位
- **THEN** 该卡券满足适用范围校验

#### Scenario: 首次预约卡券仅对首次预约可用
- **GIVEN** 用户拥有首次预约卡券
- **WHEN** 用户没有 `confirmed` 或 `completed` 预约历史
- **THEN** 该卡券满足适用范围校验

#### Scenario: 指定座位类型卡券仅匹配对应区域
- **GIVEN** 用户拥有仅限 `vip` 座位的卡券
- **WHEN** 用户预约 `seat.zone` 为 `vip` 的座位
- **THEN** 该卡券满足适用范围校验

### Requirement: 用户卡券列表 API
系统 SHALL 提供 `GET /api/v1/coupons` 接口，返回当前登录用户的卡券列表。接口 SHALL 支持 `status=available|used|expired` 查询参数。`expired` 状态 SHALL 基于卡券模板 `expires_at` 动态判断。

#### Scenario: 查询可使用卡券
- **GIVEN** 已登录用户拥有未使用且未过期的卡券
- **WHEN** 客户端请求 `GET /api/v1/coupons?status=available`
- **THEN** 返回 HTTP 200
- **AND** 响应只包含当前用户未使用且未过期的卡券

#### Scenario: 查询已过期卡券
- **GIVEN** 已登录用户拥有未使用但 `expires_at` 早于当前时间的卡券
- **WHEN** 客户端请求 `GET /api/v1/coupons?status=expired`
- **THEN** 返回 HTTP 200
- **AND** 响应包含该过期卡券

#### Scenario: 未登录无法查询卡券
- **GIVEN** 用户未登录
- **WHEN** 客户端请求 `GET /api/v1/coupons`
- **THEN** 返回 HTTP 401

### Requirement: 预约可用卡券 API
系统 SHALL 提供 `GET /api/v1/coupons/available-for-booking` 接口，根据 `seat_id`、`date`、`start_time`、`end_time` 返回当前用户对该预约可用的卡券。响应 SHALL 包含订单原价、每张卡券的抵扣金额和预计实付金额。

#### Scenario: 查询预约可用卡券
- **GIVEN** 已登录用户选择了可预约座位和时段
- **WHEN** 客户端请求 `GET /api/v1/coupons/available-for-booking?seat_id=1&date=2026-05-01&start_time=09:00&end_time=12:00`
- **THEN** 返回 HTTP 200
- **AND** 响应包含该预约可用卡券列表、每张卡券的 `discount_amount` 和 `payable_amount`

#### Scenario: 不返回不满足门槛的卡券
- **GIVEN** 用户拥有满 20 减 3 卡券
- **WHEN** 预约订单原价为 18.00
- **THEN** 可用卡券响应不包含该卡券

#### Scenario: 不返回已使用卡券
- **GIVEN** 用户拥有一张状态为 `used` 的卡券
- **WHEN** 客户端查询预约可用卡券
- **THEN** 可用卡券响应不包含该卡券

### Requirement: 卡券使用状态流转
系统 SHALL 在预约下单成功后将被使用的用户卡券状态更新为 `used`，记录 `used_booking_id` 和 `used_at`。系统 SHALL 在取消使用卡券的 `confirmed` 预约时恢复卡券为 `available`，清空 `used_booking_id` 和 `used_at`。

#### Scenario: 下单成功后卡券变为已使用
- **GIVEN** 用户使用可用卡券创建预约
- **WHEN** 预约创建成功
- **THEN** 用户卡券状态变为 `used`
- **AND** `used_booking_id` 指向新预约

#### Scenario: 取消预约后恢复卡券
- **GIVEN** 用户取消一笔使用卡券的 `confirmed` 预约
- **WHEN** 取消成功
- **THEN** 对应用户卡券状态恢复为 `available`
- **AND** `used_booking_id` 和 `used_at` 被清空
