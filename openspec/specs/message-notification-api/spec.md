# message-notification-api Specification

## Purpose
定义 br-server 用户消息通知的存储、查询、已读与偏好管理能力，并为业务节点提供统一的公共发送入口和到店签到提醒接口。
## Requirements
### Requirement: Notification data ownership
br-server SHALL store user notifications with current-user ownership and four supported notification types: `booking`, `activity`, `report`, and `arrival`.

#### Scenario: Create notification for user
- **GIVEN** 后端业务调用通知服务创建消息
- **WHEN** 服务收到 `user_id`、`type`、`title`、`content` 和可选目标信息
- **THEN** br-server SHALL 创建归属于该用户的通知记录
- **AND** 通知记录 SHALL 默认 `is_read=false`
- **AND** 通知类型 SHALL 只允许 `booking`、`activity`、`report`、`arrival`

#### Scenario: Reject unsupported notification type
- **GIVEN** 后端业务调用通知服务创建消息
- **WHEN** `type` 不是 `booking`、`activity`、`report`、`arrival` 之一
- **THEN** br-server SHALL 拒绝创建该通知

### Requirement: Notification list API
br-server SHALL provide an authenticated notification list API for the current user.

#### Scenario: List current user notifications
- **GIVEN** 用户已登录且存在多条通知
- **WHEN** 客户端请求 `GET /api/v1/notifications`
- **THEN** br-server SHALL 返回当前用户的通知分页列表
- **AND** 结果 SHALL 按 `created_at` 倒序排列
- **AND** 响应 SHALL 包含分页信息

#### Scenario: Filter notifications by type
- **GIVEN** 用户已登录且存在多种类型通知
- **WHEN** 客户端请求 `GET /api/v1/notifications?type=booking`
- **THEN** br-server SHALL 仅返回当前用户的 `booking` 类型通知

#### Scenario: Prevent cross-user notification listing
- **GIVEN** 用户已登录
- **WHEN** 客户端请求通知列表
- **THEN** br-server SHALL 从认证上下文确定用户身份
- **AND** br-server SHALL NOT 接受客户端传入的 `user_id` 作为查询范围

### Requirement: Unread summary API
br-server SHALL provide an authenticated unread summary API that counts only enabled notification types for the current user.

#### Scenario: Get unread summary
- **GIVEN** 用户已登录且 4 类通知偏好均开启
- **WHEN** 客户端请求 `GET /api/v1/notifications/unread-summary`
- **THEN** br-server SHALL 返回 `total_unread`
- **AND** br-server SHALL 返回 `booking`、`activity`、`report`、`arrival` 各类型未读数

#### Scenario: Exclude disabled notification type from summary
- **GIVEN** 用户已关闭 `activity` 通知偏好
- **AND** 用户存在未读 `activity` 通知
- **WHEN** 客户端请求 `GET /api/v1/notifications/unread-summary`
- **THEN** br-server SHALL NOT 将 `activity` 未读数计入 `total_unread`

### Requirement: Notification read APIs
br-server SHALL provide authenticated APIs to mark one notification or a filtered set of notifications as read for the current user.

#### Scenario: Mark one notification as read
- **GIVEN** 用户已登录且拥有一条未读通知
- **WHEN** 客户端请求 `POST /api/v1/notifications/{id}/read`
- **THEN** br-server SHALL 将该通知更新为 `is_read=true`
- **AND** br-server SHALL 设置 `read_at`

#### Scenario: Reject marking another user's notification
- **GIVEN** 用户已登录
- **WHEN** 客户端请求 `POST /api/v1/notifications/{id}/read` 且该通知不属于当前用户
- **THEN** br-server SHALL NOT 更新该通知

#### Scenario: Mark all notifications as read
- **GIVEN** 用户已登录且拥有多条未读通知
- **WHEN** 客户端请求 `POST /api/v1/notifications/read-all`
- **THEN** br-server SHALL 将当前用户所有未读通知更新为已读

#### Scenario: Mark notifications by type as read
- **GIVEN** 用户已登录且拥有多条未读通知
- **WHEN** 客户端请求 `POST /api/v1/notifications/read-all` 并指定 `type=report`
- **THEN** br-server SHALL 仅将当前用户 `report` 类型未读通知更新为已读

### Requirement: Notification preference APIs
br-server SHALL provide authenticated APIs to read and update the current user's notification preferences.

#### Scenario: Get default preferences
- **GIVEN** 用户已登录且没有通知偏好记录
- **WHEN** 客户端请求 `GET /api/v1/notifications/preferences`
- **THEN** br-server SHALL 返回 4 类通知均开启的默认偏好
- **AND** br-server MAY 创建默认偏好记录

#### Scenario: Update preferences
- **GIVEN** 用户已登录
- **WHEN** 客户端请求 `PUT /api/v1/notifications/preferences` 并提交 4 类开关
- **THEN** br-server SHALL 保存当前用户的通知偏好
- **AND** br-server SHALL 返回更新后的通知偏好

#### Scenario: Prevent cross-user preference access
- **GIVEN** 用户已登录
- **WHEN** 客户端读取或更新通知偏好
- **THEN** br-server SHALL 从认证上下文确定用户身份
- **AND** br-server SHALL NOT 接受客户端传入的 `user_id` 作为读写目标

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

