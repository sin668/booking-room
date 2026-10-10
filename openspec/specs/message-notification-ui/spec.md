# message-notification-ui Specification

## Purpose
定义 br-app 小程序端消息通知中心的界面行为：从首页铃铛进入的消息中心页面在四类通知（预约提醒、活动通知、学习报告、到店提醒）下的列表展示与空/错误/未读状态、类型筛选、已读状态流转与跳转目标，以及与通知偏好开关的联动。
## Requirements
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

### Requirement: Profile page message entry with unread count

「我的」页 SHALL 在「我的评价」之后提供「我的消息」菜单入口，结构与相邻菜单项一致（图标色块 + 文案 + 右侧统计文案 + 右侧箭头）。入口右侧 SHALL 展示当前用户的未读消息数量，形如 `X条未读`；该数量 MUST 来自后端未读汇总接口的 `total_unread`，其统计口径 MUST 与首页通知铃铛保持一致。未读数为 0 时该统计文案 SHALL 留空而 MUST NOT 显示 `0条未读`。点击该入口 MUST 跳转到已有的消息通知页面，MUST NOT 为「我的」页新建第二份消息列表页。该入口的展示与统计 MUST NOT 把消息标记为已读。

#### Scenario: Message entry navigates to notification center

- **GIVEN** 用户已登录并停留在「我的」页
- **WHEN** 用户点击「我的消息」
- **THEN** 小程序导航到消息通知页面
- **AND** 消息的已读状态不因此次点击而改变

#### Scenario: Message entry shows unread count

- **GIVEN** 当前登录用户有 2 条未读消息
- **WHEN** 用户打开「我的」页
- **THEN** 「我的消息」行右侧显示 `2条未读`

#### Scenario: Message entry hides count when nothing unread

- **GIVEN** 当前登录用户没有未读消息
- **WHEN** 用户打开「我的」页
- **THEN** 「我的消息」行右侧不显示统计文案
- **AND** 该行仍然可见并可点击进入消息通知页面

#### Scenario: Unread count refreshes on page show

- **GIVEN** 用户在消息通知页面把消息全部读完
- **WHEN** 用户返回「我的」页
- **THEN** 「我的消息」行重新拉取未读数
- **AND** 右侧统计文案随之消失

### Requirement: IM sign-in follows system sign-in and sign-out

The client SHALL keep the Tencent IM sign-in aligned with the system (br-app) session: signing into the system SHALL (re)establish IM sign-in for that user when the message center is opened, and signing out of the system SHALL sign out of IM and reset the IM module state so the next system sign-in cannot reuse the previous user's IM session.

#### Scenario: Sign out of system also signs out of IM
- **GIVEN** 用户 A 已登录系统且已完成 IM 登录（进入过「会话」TAB）
- **WHEN** 用户 A 退出系统登录
- **THEN** 客户端 SHALL 调用 IM 登出（`TUILogin.logout`）
- **AND** IM 模块的已初始化标记 SHALL 被重置为未初始化

#### Scenario: Next user signs in gets their own IM session
- **GIVEN** 用户 A 已退出系统登录，IM 已随退出登出并被重置
- **WHEN** 用户 B 登录系统并打开「会话」TAB
- **THEN** 客户端 SHALL 以 B 的身份重新登录 IM
- **AND** 「会话」TAB SHALL 显示 B 的会话列表，而不是 A 残留的会话

#### Scenario: Receiver sees sender profile and unread badge after switching account
- **GIVEN** 发送者 A 给接收者 B 发送消息后退出，B 随后登录系统
- **WHEN** B 打开「会话」TAB
- **THEN** 该会话行 SHALL 显示发送者 A 在本系统设置的头像与昵称
- **AND** 未读消息条数 SHALL 以带数字的红点展示
- **AND** 点击该会话 SHALL 进入与 A 的会话窗口

### Requirement: Peer avatar falls back to default when peer has no avatar

In the TUIChat message window, an incoming message bubble SHALL show a generic default avatar when the peer has no avatar, and SHALL NOT display the current logged-in user's own avatar on the peer's side.

#### Scenario: Peer without avatar shows default
- **GIVEN** 对方用户从未在本系统或 IM 设置头像，而当前登录用户已设置头像
- **WHEN** 当前用户进入与该对方的 C2C 会话窗口
- **THEN** 左侧对方消息气泡的头像 SHALL 显示默认头像
- **AND** 该头像 SHALL NOT 等于当前登录用户自己的头像

#### Scenario: Own sent messages keep own avatar
- **GIVEN** 当前登录用户已设置头像
- **WHEN** 查看自己发出的消息（右侧气泡）
- **THEN** 右侧气泡 SHALL 显示当前登录用户自己的头像

### Requirement: Conversation entry in the All tab

The message center "全部" (All) tab SHALL surface conversations by rendering a single conversation entry at the top of the notification list, styled like the other notification cards: a "话" icon with a "会话" label on the left, and the latest conversation time with an unread indicator dot (without a number) on the right. The entry SHALL only appear when the user has at least one conversation, and tapping it SHALL open the "会话" tab.

#### Scenario: All tab shows conversation entry at top
- **GIVEN** 用户至少有一个会话
- **WHEN** 用户打开消息通知页「全部」TAB
- **THEN** 通知列表最上方 SHALL 出现一条「会话」条目
- **AND** 其左侧 SHALL 显示「话」图标与「会话」标签
- **AND** 其右侧 SHALL 显示最新会话时间与未读小红点，红点 SHALL NOT 包含数字

#### Scenario: No conversation hides entry
- **GIVEN** 用户没有任何会话
- **WHEN** 用户打开「全部」TAB
- **THEN** 列表 SHALL NOT 出现「会话」条目
- **AND** 后端通知列表 SHALL 正常展示

#### Scenario: Tapping conversation entry opens conversation tab
- **GIVEN** 「全部」TAB 顶部显示了「会话」条目
- **WHEN** 用户点击该条目
- **THEN** 页面 SHALL 切换到「会话」TAB 并展示会话列表

### Requirement: Home bell counts unread conversations

The home page notification bell red dot SHALL be shown when either the server notification unread count is greater than zero OR the IM total unread conversation count is greater than zero.

#### Scenario: Only unread conversations light the bell
- **GIVEN** 用户没有未读后端通知，但存在未读会话消息
- **WHEN** 用户停留在或返回首页
- **THEN** 首页顶部铃铛 SHALL 显示红点

#### Scenario: No unread keeps bell clean
- **GIVEN** 用户既无未读后端通知也无未读会话消息
- **WHEN** 用户停留在或返回首页
- **THEN** 首页铃铛 SHALL NOT 显示红点

