# study-room-booking-api Delta Spec

## MODIFIED Requirements

### Requirement: Study room response schema
自习室列表与详情响应中每个 item SHALL 包含以下字段：`id`（整数）、`name`（字符串）、`description`（字符串，可空）、`cover_image`（字符串 URL）、`address`（字符串）、`business_hours`（字符串，如 "08:00-22:00"）、`status`（枚举 "open"/"closed"）、`room_type`（枚举 "study"/"training"/"comprehensive"）、`min_price`（数字，单位元）、`city_id`（整数或 null）、`city_name`（字符串或 null，城市名称）、`latitude`（数字或 null，GCJ-02 纬度）、`longitude`（数字或 null，GCJ-02 经度）。

#### Scenario: Response field validation
- **WHEN** 客户端请求自习室列表或详情
- **THEN** 每个 item 包含 `id`、`name`、`description`、`cover_image`、`address`、`business_hours`、`status`、`room_type`、`min_price`、`city_id`、`city_name`、`latitude`、`longitude` 字段，类型符合规范

#### Scenario: Room without city
- **WHEN** 客户端请求包含 `city_id=null` 的自习室
- **THEN** 该 item 的 `city_id` 为 null，`city_name` 为 null

#### Scenario: Room without coordinates
- **WHEN** 客户端请求尚未配置经纬度的自习室
- **THEN** 该 item 的 `latitude` 和 `longitude` 均为 null，其他字段不受影响

#### Scenario: Room with coordinates
- **GIVEN** 一间已配置 GCJ-02 坐标的自习室
- **WHEN** 客户端请求该自习室详情
- **THEN** `latitude` 和 `longitude` 返回 JSON 数字，精度保留至小数点后 7 位以内

#### Scenario: Room type field values
- **GIVEN** 存在 room_type 分别为 study、training、comprehensive 的房间
- **WHEN** 客户端请求房间列表
- **THEN** 每个 item 的 `room_type` 字段为 "study"、"training" 或 "comprehensive" 之一
