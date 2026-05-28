## ADDED Requirements

### Requirement: Notification center page
br-app SHALL provide a message notification center page reachable from the home page notification bell. The page SHALL display user messages for four notification categories: booking reminders, activity notifications, study reports, and arrival reminders.

#### Scenario: Open notification center
- **GIVEN** 用户已进入 br-app 首页
- **WHEN** 用户点击顶部通知铃铛
- **THEN** 小程序 SHALL 导航到消息通知页面
- **AND** 页面 SHALL 展示消息通知标题和四类消息筛选入口

#### Scenario: Display four notification categories
- **GIVEN** 用户进入消息通知页面
- **WHEN** 页面加载完成
- **THEN** 页面 SHALL 展示“全部”、“预约提醒”、“活动通知”、“学习报告”、“到店提醒”筛选项
- **AND** 每条消息 SHALL 归属到 `booking`、`activity`、`report`、`arrival` 其中一种类型

### Requirement: Notification list states
消息通知页面 SHALL support loading, empty, error, unread, and read states for the notification list.

#### Scenario: Display notification list
- **GIVEN** br-server 通知列表接口返回当前用户多条消息
- **WHEN** 用户进入消息通知页面
- **THEN** 页面 SHALL 按时间倒序展示消息卡片
- **AND** 每条消息 SHALL 展示类型标签、标题、摘要、时间和未读状态

#### Scenario: Empty notification list
- **GIVEN** 当前筛选类型下没有消息
- **WHEN** 消息通知页面加载完成
- **THEN** 页面 SHALL 展示空状态文案
- **AND** 页面 SHALL 保留筛选入口，允许用户切换其他类型

#### Scenario: Notification load failure
- **GIVEN** br-server 通知列表接口加载失败
- **WHEN** 页面加载完成
- **THEN** 页面 SHALL 展示错误提示和重试入口

### Requirement: Notification filtering
消息通知页面 SHALL allow users to filter messages by the four notification categories and all messages.

#### Scenario: Filter by booking reminders
- **GIVEN** 消息通知页面包含多种类型消息
- **WHEN** 用户点击“预约提醒”
- **THEN** 页面 SHALL 仅展示 `booking` 类型消息

#### Scenario: Filter all messages
- **GIVEN** 用户当前位于某个类型筛选
- **WHEN** 用户点击“全部”
- **THEN** 页面 SHALL 展示所有未被隐藏的消息类型

### Requirement: Notification read state
消息通知页面 SHALL allow messages to transition from unread to read through the br-server read API and SHALL update unread indicators only after the operation succeeds.

#### Scenario: Mark notification as read
- **GIVEN** 消息列表中存在未读消息
- **WHEN** 用户点击该消息
- **THEN** 小程序 SHALL 调用 br-server 单条标记已读接口
- **AND** 该消息 SHALL 从未读状态变为已读状态

#### Scenario: Mark notification read failure
- **GIVEN** 消息列表中存在未读消息
- **WHEN** 用户点击该消息且 br-server 单条标记已读接口失败
- **THEN** 小程序 SHALL 保持该消息未读状态
- **AND** 小程序 SHALL 展示失败提示
- **AND** 小程序 SHALL 不跳转业务页面

#### Scenario: Mark all notifications as read
- **GIVEN** 消息通知页面存在未读消息
- **WHEN** 用户点击全部已读操作
- **THEN** 小程序 SHALL 调用 br-server 批量标记已读接口
- **AND** 当前筛选范围内的未读消息 SHALL 全部变为已读

### Requirement: Notification target navigation
消息通知页面 SHALL mark a clicked notification as read first and then route to the notification target.

#### Scenario: Navigate by target URL
- **GIVEN** 消息包含 `target_url`
- **WHEN** 用户点击该消息且标记已读成功
- **THEN** 小程序 SHALL 跳转到 `target_url` 指向的页面

#### Scenario: Navigate by notification type default target
- **GIVEN** 消息不包含 `target_url`
- **WHEN** 用户点击该消息且标记已读成功
- **THEN** 小程序 SHALL 按消息类型跳转到默认页面
- **AND** `booking` SHALL 跳转预约或订单页面
- **AND** `activity` SHALL 跳转首页活动入口
- **AND** `report` SHALL 跳转学习记录页面
- **AND** `arrival` SHALL 跳转我的学习码页面

### Requirement: Notification preferences integration
消息通知页面 SHALL respect the four notification preference switches loaded from br-server preferences: booking, activity, report, and arrival.

#### Scenario: Disabled notification type hint
- **GIVEN** 用户在设置页关闭“活动通知”
- **WHEN** 用户在消息通知页面筛选“活动通知”
- **THEN** 页面 SHALL 展示该类型已关闭的提示
- **AND** 页面 SHALL 仍允许查看该类型历史消息
- **AND** 页面 SHALL 不把该类型未读消息计入首页主动提醒红点

#### Scenario: Enabled notification type
- **GIVEN** 用户在设置页开启“到店打卡提醒”
- **WHEN** 存在未读 `arrival` 类型消息
- **THEN** 消息通知页面 SHALL 正常展示该消息
- **AND** 首页未读摘要 SHALL 可以计入该类型未读数
