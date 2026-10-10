# Design: 消息通知页「会话」TAB

## Context

- 消息通知页 `br-app/src/pages/notifications/index.vue` 用 `currentType`（`all` + 4 个类型）驱动 TAB 与列表，数据源是 `getNotifications()` 单一接口。
- IM 能力已落地：`br-app/src/utils/im.js` 的 `ensureIM()` 负责 `TUILogin.login` + `TUIChatEngine.login`；`br-app/src/pages/edu-market/detail.vue` 已用 `uni.navigateTo('/TUIKit/components/TUIChat/index?conversationID=C2C<user>')` 打开单聊，`TUIKit/components/TUIChat/entry-chat-only.ts` 解析该参数并 `switchConversation`。
- TUIKit 自带会话列表页 `TUIKit/components/TUIConversation/index.vue`，其数据源是 `TUIStore.watch(StoreName.CONV, { conversationList })`。

## Goals / Non-Goals

Goals：会话 TAB 复用现有 IM 登录与聊天页；通知列表逻辑零改动。
Non-Goals：不做会话长按操作（置顶/免打扰/删除）、不做全局未读汇总与首页红点、不引入 TUIConversation 页面组件、不做已读上报、不改后端。

## Decisions

1. **数据源用 `TUIStore` + `TUIConversationService.getConversationList()`，不自建会话接口。**
   `conversationList` 元素已提供 `getShowName()` / `getAvatar()` / `getLastMessage('text')` / `getLastMessage('time')` / `unreadCount` / `conversationID`，正是需求所需的全部字段，且排序、时间格式化、撤回与图片消息占位文案均由 SDK 处理。备选：调用后端聚合会话（需新增接口 + 存储 IM 消息，成本远超收益，放弃）；直接内嵌 `TUIConversation` 组件（会把 TUIKit 子包组件拉进主包且样式不可控，放弃）。

2. **打开聊天沿用 `?conversationID=` 路由参数。**
   与 `edu-market/detail.vue` 完全一致的跳转串，无需在通知页调用 `switchConversation`，避免与 `entry-chat-only.ts` 的初始化时序竞争。

3. **TAB 以 `conversation` 虚拟值表示，与后端通知类型解耦。**
   `switchType('conversation')` 时不调用 `getNotifications()`，避免把非法 `type` 传给后端（参考 bug-fixed.md BUG-13：不要构造后端不接受的参数）。

4. **会话列表在通知页内自渲染，不引用 TUIKit 组件。**
   主包页面只 `import` npm 包 `@tencentcloud/chat-uikit-engine-lite`（与 `utils/im.js` 同源，已在依赖中），头像用原生 `<image>` + 首字母占位；样式沿用本页卡片风格，避免跨子包引用。

5. **标签精简改 `label` 而非新增字段。**
   `label` 仅被通知页（TAB、卡片类型标签、空态文案）消费，设置页消费 `settingLabel`，因此一处改动即覆盖需求且无副作用；空态 `暂无预约消息` 读语义仍通顺。

## Risks / Trade-offs

- [未登录 IM 时会话列表为空] → 进入会话 TAB 时 `await ensureIM()`，失败展示既有错误态与「重新加载」按钮，不影响其他 TAB。
- [小程序主包引入 engine-lite 增大包体] → `utils/im.js` 已在主包引入 `tui-core-lite`/engine-lite，本改动不新增第三方运行时依赖。
- [动态插入列表在小程序因动画不可见]（见项目 pitfall 记录）→ 会话列表节点不使用 `animation` + `backwards` 填充。
- [从聊天页返回后会话未读数不同步] → `onShow` 时对会话 TAB 重新 `getConversationList()`，SDK 返回最新未读。

## Migration Plan

无数据迁移与配置变更，随小程序版本发布；回滚见 proposal.md「回滚方案」。
