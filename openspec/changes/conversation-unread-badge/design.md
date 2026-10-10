# Design: conversation-unread-badge

## Decision 1: 在 `onUnload` 清除当前会话，而不是依赖 `onUnmounted`

`onUnload` 是 uni-app 小程序端页面出栈时保证触发的生命周期，`onUnmounted` 在 mp-weixin 页面栈场景不保证执行。因此把清除当前会话的动作放进 `onUnload`：

```js
onUnload(() => {
  // 清除当前会话，否则引擎会把该会话的新消息自动置为已读，unreadCount 恒为 0
  reset();
  logout(false)...
});
```

保留 `onUnmounted` 里原有的 `reset()`：H5 与组件化场景仍需要它，且 `switchConversation('')` 幂等（引擎对空 conversationID 只是把 `currentConversationID` 写为 `''` 并重置 chat 消息列表），重复调用无副作用。

不新增「记录本会话是否由本页打开」之类的判断：清除空当前会话本身没有代价，加判断反而引入状态。

## Decision 2: 不改动会话列表读取路径

已核实渲染与数据两层都正确，因此不引入 `getTotalUnreadMessageCount()` 之类的兜底：

- 编译产物 `br-app/dist/build/mp-weixin/pages/notifications/index.wxml` 内徽标条件绑定 `wx:if="{{item.g}}"` + `class="conv-badge"`，`index.js` 内 `g: a.unreadCount > 0`，样式 `.conv-badge` 有尺寸与红色背景。
- 官方 `src/TUIKit/components/TUIConversation/conversation-list/index.vue:55` 同样直接使用 `conversation.unreadCount > 0`，与本页面取法一致。
- 引擎会话模型 `initProxy`/`updateProperties` 会复制 SDK `Conversation` 的自有键（仅跳过 `_` 前缀），`unreadCount` 在其中。

## Decision 3: 自检用断言脚本，不加测试框架

沿用 `br-app/scripts/verify-im-peer-profile.js` 的 assert 风格，追加两条断言：`onUnload` 内调用了清除当前会话；清除动作仍成对存在（不会因修改而漏掉 `onUnmounted`）。
