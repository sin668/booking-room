# message-notification-api Delta Spec

## ADDED Requirements

### Requirement: Common notification sending method

br-server SHALL provide a shared notification sending method that all business triggers use to create user notifications, so that type validation, preference filtering, and target information stay consistent.

#### Scenario: Send notification with default target

- **GIVEN** 用户开启了对应类型的通知偏好
- **WHEN** 业务节点通过公共发送方法提交 `user_id`、`type`、`title`、`content` 且未提供 `target_url`
- **THEN** br-server SHALL 创建该通知并补全该类型的默认 `target_url`
- **AND** `booking` SHALL 默认指向 `/pages-sub/orders/index`
- **AND** `activity` SHALL 默认指向 `/pages/index/index`
- **AND** `report` SHALL 默认指向 `/pages-sub/study-record/index`
- **AND** `arrival` SHALL 默认指向 `/pages-sub/qrcode/index`

#### Scenario: Skip notification for disabled preference

- **GIVEN** 用户关闭了 `arrival` 通知偏好
- **WHEN** 业务节点通过公共发送方法提交 `arrival` 类型消息
- **THEN** br-server SHALL NOT 创建该通知

#### Scenario: Reject unsupported type

- **GIVEN** 业务节点通过公共发送方法提交通知
- **WHEN** `type` 不是 `booking`、`activity`、`report`、`arrival` 之一
- **THEN** br-server SHALL 拒绝创建该通知

### Requirement: Arrival reminder API

br-server SHALL provide an authenticated endpoint `POST /api/v1/notifications/arrival-reminder` that creates an `arrival` notification only when the current user is within 500 meters of the specified room.

#### Scenario: Send reminder when user is nearby

- **GIVEN** 用户已登录且 `arrival` 偏好开启
- **WHEN** 客户端提交 `room_id` 与用户坐标，且用户与房间距离不超过 500 米
- **THEN** br-server SHALL 为当前用户创建一条 `arrival` 类型通知
- **AND** 通知标题 SHALL 为 `到店签到提醒`
- **AND** 通知 `target_url` SHALL 为 `/pages-sub/qrcode/index`
- **AND** 通知 `target_type` SHALL 为 `room`，`target_id` SHALL 为该房间 ID
- **AND** 响应 SHALL 返回 `sent=true` 与通知内容

#### Scenario: Skip reminder when user is far away

- **GIVEN** 用户已登录
- **WHEN** 客户端提交坐标与房间距离超过 500 米
- **THEN** br-server SHALL NOT 创建通知
- **AND** 响应 SHALL 返回 `sent=false` 并给出距离

#### Scenario: Skip duplicate reminder within 24 hours

- **GIVEN** 用户已登录且 24 小时内收到过同一房间的到店提醒
- **WHEN** 客户端再次提交该房间的到店提醒请求
- **THEN** br-server SHALL NOT 重复创建通知
- **AND** 响应 SHALL 返回 `sent=false`

#### Scenario: Skip reminder for room without coordinates

- **GIVEN** 目标房间没有有效的经纬度
- **WHEN** 客户端提交到店提醒请求
- **THEN** br-server SHALL NOT 创建通知
- **AND** 响应 SHALL 返回 `sent=false`

#### Scenario: Prevent cross-user reminder creation

- **GIVEN** 客户端未携带有效登录态
- **WHEN** 客户端请求 `POST /api/v1/notifications/arrival-reminder`
- **THEN** br-server SHALL 拒绝请求
- **AND** br-server SHALL 只依据认证上下文确定消息归属用户
- **AND** br-server SHALL NOT 接受客户端传入的 `user_id`

#### Scenario: Existing reminder keeps navigation target

- **GIVEN** 用户已收到一条 `arrival` 类型通知
- **WHEN** 客户端展示该通知
- **THEN** 通知 SHALL 包含可直接跳转的 `target_url`
