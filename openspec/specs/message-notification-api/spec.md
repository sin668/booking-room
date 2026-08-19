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
