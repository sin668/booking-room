## ADDED Requirements

### Requirement: Booking lifecycle notifications

br-server SHALL send `booking` type notifications through the common notification sending service at booking lifecycle events, and SHALL respect the user's `booking_enabled` preference.

#### Scenario: Booking payment succeeded
- **GIVEN** 用户的座位预约或课程预约支付成功（余额支付、微信支付回调或支付对账确认）
- **WHEN** 订单状态更新为已支付
- **THEN** br-server SHALL 向该用户发送 title 为「预约成功通知」的 `booking` 消息
- **AND** 消息 target_url SHALL 指向订单列表或对应订单详情

#### Scenario: Booking starts within 15 minutes
- **GIVEN** 用户的已支付订单处于待开始或进行中状态
- **WHEN** 订单状态定时任务检测到座位使用开始时间或课程课时开始时间落在当前时间之后 15 分钟以内
- **THEN** br-server SHALL 向该用户发送 title 为「预约开始提醒」的 `booking` 消息
- **AND** 同一订单同一课时 SHALL 最多发送一次提醒

#### Scenario: Booking marked completed
- **GIVEN** 用户的已支付订单仍处于待开始或进行中状态
- **WHEN** 订单状态变更为「已完成」（定时任务推进、核销完成或读取时的状态同步）
- **THEN** br-server SHALL 向该用户发送 title 为「离店核销完成」的 `booking` 消息
- **AND** 同一订单 SHALL 最多发送一次完成消息

#### Scenario: User disabled booking notifications
- **GIVEN** 用户已关闭 `booking` 通知偏好
- **WHEN** 订单发生支付成功、开始提醒或完成事件
- **THEN** br-server SHALL NOT 为该用户创建对应 `booking` 消息

#### Scenario: Duplicate lifecycle event
- **GIVEN** 同一订单的同一生命周期消息已存在
- **WHEN** 支付回调重试、定时任务再次扫描或状态同步再次触发
- **THEN** br-server SHALL NOT 重复创建相同消息

### Requirement: Activity broadcast notification

br-server SHALL provide a common broadcast method that sends `activity` type notifications to all App users and respects the `activity_enabled` preference.

#### Scenario: Broadcast activity message
- **GIVEN** 活动已上架且关联卡券
- **WHEN** 管理端保存活动触发群发
- **THEN** br-server SHALL 为每个符合偏好条件的 App 用户创建一条 `activity` 消息
- **AND** 消息 title SHALL 为活动 title，content SHALL 为活动 description
- **AND** 消息 target_url SHALL 为 `/pages-sub/activity/detail?id=<活动ID>`

#### Scenario: Skip users with disabled activity preference
- **GIVEN** 用户已关闭 `activity` 通知偏好
- **WHEN** br-server 群发活动消息
- **THEN** br-server SHALL NOT 为该用户创建活动消息

#### Scenario: Avoid duplicated broadcast for unchanged activity
- **GIVEN** 同一活动、相同 title 与 content 的活动消息已群发过
- **WHEN** 管理端再次保存该活动
- **THEN** br-server SHALL NOT 再次向全部用户重复发送相同消息
