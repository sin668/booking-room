## ADDED Requirements

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
