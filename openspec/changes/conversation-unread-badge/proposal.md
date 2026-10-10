# Proposal: conversation-unread-badge

## Why

消息通知页「会话」TAB 能实时收到对方的新消息（摘要与时间已更新），但红点里的未读条数始终不显示。

根因不在渲染层，也不在数据模型层，而在 TUIChat 页面的会话切换生命周期：

- `chat-uikit-engine-lite` 的 `StoreName.APP.enableAutoMessageRead` 默认值为 `true`。
- 引擎收到消息推送时，`updateTargetMessageList` 先按 `currentConversationID` 过滤，命中当前会话的消息分支会直接调用 `chat.setMessageRead({ conversationID })`，因此**该会话的 `unreadCount` 会被清零并保持为 0**。
- 只有 `TUIConversationService.switchConversation('')` 才会把 `currentConversationID` 清空。而 `br-app/src/TUIKit/components/TUIChat/index.vue` 只在 Vue 的 `onUnmounted` 里调用 `reset()`（即 `switchConversation('')`），`onUnload` 里只调用了 `logout(false)`；小程序端页面栈出栈时 `onUnmounted` 不保证触发，且微信侧上一页的 `onShow` 早于被弹出页面的卸载回调。

结果：用户从「会话」TAB 进入聊天窗口再返回后，对方会话一直残留为 SDK 的当前会话，之后对方发来的每一条消息都被自动置已读，未读数恒为 0，红点自然不出现；同时聊天窗口显示的仍是残留的对方会话，而不是本次要打开的会话。

## What

在 TUIChat 页面由平台保证的卸载生命周期（`onUnload`）中清除当前会话，使离开聊天页后新到的消息重新累计未读数，红点数字得以显示；并保证下次进入聊天页不会复用上一个残留会话。

不新增后端接口、不新增依赖、不改动会话列表渲染与徽标样式（已确认渲染层与模型层均正确）。

## Impact

- Affected capability: `message-notification-ui`
- Affected code: `br-app/src/TUIKit/components/TUIChat/index.vue`
- Affected checks: `br-app/scripts/verify-im-peer-profile.js`（补充生命周期断言）
