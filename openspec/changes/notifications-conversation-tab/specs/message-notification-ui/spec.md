# message-notification-ui Delta Spec

## MODIFIED Requirements

### Requirement: Notification center page
br-app SHALL provide a message notification center page reachable from the home page notification bell. The page SHALL display user messages for four notification categories (booking reminders, activity notifications, study reports, arrival reminders) using short category labels, and SHALL additionally expose an instant-messaging conversation tab.

#### Scenario: Open notification center
- **GIVEN** 用户已进入 br-app 首页
- **WHEN** 用户点击顶部通知铃铛
- **THEN** 小程序 SHALL 导航到消息通知页面
- **AND** 页面 SHALL 展示消息通知标题和消息筛选入口

#### Scenario: Display four notification categories
- **GIVEN** 用户进入消息通知页面
- **WHEN** 页面加载完成
- **THEN** 页面 SHALL 按「全部」「会话」「预约」「活动」「报告」「到店」顺序展示筛选项
- **AND** 每条系统通知 SHALL 归属到 `booking`、`activity`、`report`、`arrival` 其中一种类型
- **AND** 通知卡片上的类型标签 SHALL 使用「预约」「活动」「报告」「到店」短标签

### Requirement: Notification filtering
消息通知页面 SHALL allow users to filter messages by the four notification categories and all messages. The conversation tab SHALL be a view switch rather than a notification category: selecting it MUST NOT send a notification list request with a category the backend does not define.

#### Scenario: Filter by booking reminders
- **GIVEN** 消息通知页面包含多种类型消息
- **WHEN** 用户点击「预约」
- **THEN** 页面 SHALL 仅展示 `booking` 类型消息

#### Scenario: Filter all messages
- **GIVEN** 用户当前位于某个类型筛选
- **WHEN** 用户点击「全部」
- **THEN** 页面 SHALL 展示所有未被隐藏的消息类型

#### Scenario: Switch to conversation tab
- **GIVEN** 用户当前位于任意通知类型筛选
- **WHEN** 用户点击「会话」
- **THEN** 页面 SHALL 展示会话列表并隐藏通知列表与其空态文案
- **AND** 页面 MUST NOT 以 `conversation` 等未定义类型请求 br-server 通知列表接口

## ADDED Requirements

### Requirement: Conversation tab list
消息通知页面 SHALL 在「会话」TAB 展示当前登录用户的即时通讯会话列表，数据与排序 MUST 来自即时通讯 SDK 的会话数据（按最后一条消息时间倒序），MUST NOT 要求后端新建会话聚合接口。每条会话 SHALL 在左侧展示对方头像、昵称与最新一条消息内容，在右侧展示消息时间与未读条数。

#### Scenario: Display conversation items
- **GIVEN** 当前用户存在至少一个会话
- **WHEN** 用户切到「会话」TAB 且会话数据加载成功
- **THEN** 每条会话 SHALL 展示头像、昵称与最新一条消息的单行摘要
- **AND** 昵称与消息摘要超出可用宽度时 SHALL 单行截断并以省略号结尾，MUST NOT 换行或撑破行高
- **AND** 每条会话 SHALL 在右侧展示该会话的消息时间
- **AND** 未读数大于 0 时 SHALL 以红色徽标展示未读条数，未读数为 0 时 MUST NOT 展示徽标
- **AND** 未读数大于 99 时徽标 SHALL 展示 `99+`

#### Scenario: Conversation without avatar or name
- **GIVEN** 某会话缺少对方头像或昵称
- **WHEN** 「会话」TAB 渲染该会话
- **THEN** 页面 SHALL 以占位头像与兜底名称展示该行，MUST NOT 出现空白行或破图

#### Scenario: Empty conversation list
- **GIVEN** 当前用户没有任何会话
- **WHEN** 「会话」TAB 加载完成
- **THEN** 页面 SHALL 展示空状态文案
- **AND** 页面 SHALL 保留全部筛选入口允许用户切回通知类型

#### Scenario: Conversation service unavailable
- **GIVEN** 即时通讯初始化或会话拉取失败
- **WHEN** 用户处于「会话」TAB
- **THEN** 页面 SHALL 展示失败提示与重试入口
- **AND** 用户切回其他 TAB 时通知列表 SHALL 正常可用

#### Scenario: Conversation unread refreshes on return
- **GIVEN** 用户从「会话」TAB 进入某个聊天页面并读完消息
- **WHEN** 用户返回消息通知页面且仍处于「会话」TAB
- **THEN** 页面 SHALL 重新拉取会话数据
- **AND** 该会话的未读徽标 SHALL 按最新未读数显示或消失

### Requirement: Conversation chat entry
消息通知页面 SHALL allow opening an existing chat page from a conversation item without creating a second conversation surface.

#### Scenario: Open chat from conversation item
- **GIVEN** 「会话」TAB 展示了至少一条会话
- **WHEN** 用户点击该会话
- **THEN** 小程序 SHALL 跳转到已有的聊天页面并定位到被点击的会话
- **AND** 系统 MUST NOT 新建独立的会话详情页面

#### Scenario: Not logged in
- **GIVEN** 用户尚未登录 br-app
- **WHEN** 用户尝试进入「会话」TAB
- **THEN** 页面 SHALL 沿用既有的登录引导行为
- **AND** 页面 MUST NOT 展示他人会话数据
