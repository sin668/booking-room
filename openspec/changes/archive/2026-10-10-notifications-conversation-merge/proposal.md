## Why

消息通知中心与首页铃铛在「会话（IM 聊天）」上有三处体验缺陷：

1. **对方无头像时错误显示成自己的头像**：进入 TUIChat 会话窗口，若对方（如「学习者478642」）从未设置头像，腾讯云 IM SDK 的归一化逻辑会把当前登录用户（林sam~）的头像写进 `conversation.userProfile`，导致左侧对方气泡显示成自己的车头像，而不是默认头像。
2. **「全部」TAB 不含会话**：会话消息只在「会话」TAB 出现，用户在「全部」收件箱看不到有会话消息进来。
3. **首页铃铛不计会话未读**：首页顶部铃铛红点只统计后端通知 `total_unread`，未读会话消息不会点亮铃铛。

## What Changes

- TUIChat 气泡头像：对 `flow === 'in'` 的消息，当头像为空或等于当前用户自己的头像时回退到默认头像。
- 「全部」TAB：在通知列表最上方增加一行「会话」条目（左侧「话」图标 + 「会话」标签，右侧最新会话时间 + 未读小红点，红点不含数字），点击进入「会话」TAB。
- 首页铃铛：`hasNotification` 改为「后端通知未读 或 IM 会话未读」任一为真即显示红点。

## Impact

- Affected capability: `message-notification-ui`
- Affected code: `br-app/src/TUIKit/components/TUIChat/message-list/message-elements/message-bubble.vue`、`br-app/src/pages/notifications/index.vue`、`br-app/src/pages/index/index.vue`、`br-app/scripts/verify-im-peer-profile.js`
