# 消息通知前端与后端 REST 设计

日期：2026-05-28

## 背景

br-app 首页已有通知铃铛，“我的设置”也已有通知设置分组，但当前缺少真实消息中心和后端数据来源。这个变更把消息通知作为一个完整闭环处理：br-server 提供 REST 接口和用户偏好，br-app 提供消息中心、首页红点、设置开关联动和点击跳转。

## 范围

本次变更包含：

- br-server 通知数据模型、通知偏好模型、迁移、schema、service、router 和测试。
- br-app 消息通知 API 封装、消息中心页面、首页铃铛跳转与未读红点、设置页 4 类通知偏好读写。
- OpenSpec 规格更新，明确后端 REST API 是主路径。

本次变更不包含：

- 微信订阅消息授权、模板消息发送或服务端推送。
- 管理后台消息配置。
- 复杂事件总线。V1 只提供 `create_notification(...)` 服务方法，供未来业务生产者调用。

## 通知类型

统一使用 4 个类型键：

- `booking`: 预约提醒
- `activity`: 活动通知
- `report`: 学习报告/学习周报
- `arrival`: 到店提醒/到店打卡提醒

前端页面、后端数据模型、设置偏好和未读摘要都使用同一套枚举。

## 后端设计

新增 `notifications` 表：

- `id`
- `user_id`
- `type`
- `title`
- `content`
- `target_url`
- `target_type`
- `target_id`
- `is_read`
- `created_at`
- `read_at`

新增 `notification_preferences` 表：

- `user_id`
- `booking_enabled`
- `activity_enabled`
- `report_enabled`
- `arrival_enabled`
- `updated_at`

所有接口都必须基于当前登录用户，不接受客户端传入 `user_id` 作为查询或更新范围。新用户默认 4 类通知均开启。

## REST API

后端提供：

- `GET /api/v1/notifications`
  - 参数：`type?`、`page`、`page_size`
  - 返回当前用户分页通知列表，按创建时间倒序。
- `GET /api/v1/notifications/unread-summary`
  - 返回 `total_unread` 和 4 类未读数。
  - `total_unread` 只统计用户已开启类型。
- `POST /api/v1/notifications/{id}/read`
  - 标记当前用户拥有的单条通知为已读。
- `POST /api/v1/notifications/read-all`
  - 参数或 body：`type?`
  - 标记当前用户全部或指定类型通知为已读。
- `GET /api/v1/notifications/preferences`
  - 返回当前用户 4 类通知开关。
- `PUT /api/v1/notifications/preferences`
  - 保存当前用户 4 类通知开关。

## 前端设计

新增 `br-app/src/api/notifications.js`，页面只调用 API 封装，不直接拼接请求路径。API 封装包含：

- `getNotifications(params)`
- `getNotificationUnreadSummary()`
- `markNotificationRead(id)`
- `markAllNotificationsRead(type?)`
- `getNotificationPreferences()`
- `updateNotificationPreferences(payload)`

新增 `pages/notifications/index`：

- 提供“全部、预约提醒、活动通知、学习报告、到店提醒”筛选。
- 展示加载、空状态、错误重试、下拉刷新、未读/已读状态。
- 点击消息先调用单条已读接口。成功后优先跳转 `target_url`，没有 `target_url` 时按类型跳转默认页面。
- 关闭的通知类型仍可筛选并查看历史消息，但展示“该类通知已关闭”提示。

首页通知铃铛：

- 点击跳转消息通知页面。
- 页面显示和刷新时调用 unread summary。
- unread summary 失败时隐藏红点，不阻塞首页主内容。

设置页通知开关：

- 页面加载时读取后端偏好。
- 用户切换后保存到后端。
- 保存失败时回滚该开关并 toast 提示。

## 点击跳转规则

消息点击行为采用“先已读，后跳转”：

- `target_url` 存在：跳转 `target_url`。
- `booking` 无 `target_url`：跳转预约/订单页面。
- `activity` 无 `target_url`：跳转首页活动入口。
- `report` 无 `target_url`：跳转学习记录页面。
- `arrival` 无 `target_url`：跳转我的学习码页面。

如果标记已读失败，消息保持未读，展示错误提示，不跳转。

## 错误处理

- 通知列表加载失败：消息中心展示错误状态和重试入口。
- unread summary 加载失败：首页隐藏红点，不阻塞主内容。
- 单条已读失败：保持未读，toast 提示，不跳转。
- 全部已读失败：保持原列表状态，toast 提示。
- 偏好保存失败：回滚开关，toast 提示。

## 测试策略

后端测试覆盖：

- 当前用户消息列表、类型筛选、分页。
- unread summary 只统计已开启类型。
- 单条已读和批量已读。
- 偏好默认值、更新和读取。
- 跨用户消息和偏好不能读取或修改。

前端验证覆盖：

- `pnpm run build:h5`。
- 首页铃铛跳转和红点显示/隐藏。
- 消息中心筛选、空状态、错误重试、下拉刷新。
- 点击消息已读后跳转。
- 已读失败不跳转。
- 设置页偏好读取、保存和失败回滚。

## OpenSpec 更新

本设计对应 OpenSpec change：`add-message-notification-frontend`。

需要同步维护：

- `message-notification-api`: 后端 REST API 能力。
- `message-notification-ui`: 前端消息中心能力。
- `homepage-ui`: 首页通知铃铛入口和未读红点。
- `profile-settings-ui`: 我的设置 4 类通知偏好。
