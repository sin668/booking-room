## ADDED Requirements

### Requirement: Seat response schema
座位列表响应 SHALL 包含以下字段：`id`（整数）、`room_id`（整数）、`seat_number`（字符串，如 "A-01"）、`zone`（枚举字符串 "quiet"/"keyboard"/"vip"）、`position`（字符串，如 "靠窗"）、`floor`（整数）、`price_per_hour`（数字，单位元）、`status`（枚举字符串 "available"/"maintenance"）、`row`（整数）、`col`（整数）。当带时间参数查询时额外返回 `is_available`（布尔值）。

#### Scenario: Seat response field validation
- **WHEN** 客户端请求座位列表
- **THEN** 每个座位包含 `id`、`room_id`、`seat_number`、`zone`、`position`、`floor`、`price_per_hour`、`status`、`row`、`col` 字段，类型符合规范

#### Scenario: Seat with availability flag
- **WHEN** 客户端请求座位列表并传入 `date`、`start_time`、`end_time` 参数
- **THEN** 每个座位额外包含 `is_available` 字段，已被预约的座位 `is_available=false`，可选座位 `is_available=true`，维护中座位 `is_available=false`
