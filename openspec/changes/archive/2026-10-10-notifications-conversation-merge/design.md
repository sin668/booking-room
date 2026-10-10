# Design: 会话并入全部收件箱 + 头像回退 + 铃铛计入会话未读

## 决策 1：头像回退放在渲染层（message-bubble.vue）

SDK 归一化（`updateNickAndAvatarOfSentMessage` / `_updateMessageProfile`）会把 `conversation.userProfile.avatar` 刷进所有 `in` 气泡，且无空值校验。改数据层风险高、易被 SDK 覆盖。改为渲染层防御：`flow === 'in'` 且 `message.avatar` 为空或等于 `TUIStore.getData(StoreName.USER,'userProfile').avatar`（自己的头像）时传 `''`，`Avatar` 组件已对空 url 回退内置默认头像 `avatar_21.png`。对方恰好与自己同头像属可接受极端情况。

## 决策 2：「全部」TAB 顶部加单条「会话」聚合行

按用户「在最上面加上一行」的字面语义，在通知卡片列表最上方渲染一条「会话」条目（非每条会话各一行，避免与「会话」TAB 重复）：复用 notification-card 头部结构，左「话」图标 +「会话」标签，右最新会话时间 + 未读小红点（`unread-dot`，无数字）。仅当存在至少一条会话时显示；点击进入「会话」TAB（`switchType('conversation')`）。为取到会话数据，`currentType === 'all'` 时也执行 `ensureIM()` + 订阅 `conversationList`。

## 决策 3：铃铛未读复用引擎 totalUnreadCount

首页 `ensureIM()` 后读取 `TUIStore.getData(StoreName.CONV,'totalUnreadCount')` 并订阅其变化，`hasNotification = 后端total_unread>0 || IM totalUnreadCount>0`。onHide/onUnload 取消订阅避免泄漏。IM 未就绪或未登录时该项为 0，不影响后端通知红点。

## 决策 4：源码断言脚本验证，不引测试框架

沿用 `scripts/verify-im-peer-profile.js` 断言：气泡头像回退逻辑、全部 TAB 会话行、铃铛合并 IM 未读。
