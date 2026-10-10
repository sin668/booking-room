## ADDED Requirements

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
