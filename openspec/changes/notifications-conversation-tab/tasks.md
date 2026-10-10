# Tasks: 消息通知页「会话」TAB

## 1. 通知类型标签精简

- [x] 1.1 将 `br-app/src/utils/notificationTypes.js` 中四类 `label` 改为「预约」「活动」「报告」「到店」，保持 `key`、`settingLabel`、`defaultTarget`、`iconText` 不变
- [x] 1.2 确认设置页仍展示全称偏好文案，通知页 TAB 与卡片类型标签使用短标签

## 2. 会话 TAB 与列表

- [ ] 2.1 在 `br-app/src/pages/notifications/index.vue` 的 TAB 序列中「全部」之后插入「会话」（值 `conversation`），切换时不请求通知列表接口
- [ ] 2.2 接入既有 IM 能力：进入会话 TAB 时 `ensureIM()` + `TUIConversationService.getConversationList()`，通过 `TUIStore.watch(StoreName.CONV, { conversationList })` 订阅更新，卸载/离开时 `unwatch`
- [ ] 2.3 渲染会话行：左侧头像（缺失时占位）、昵称、最新一条消息（单行截断省略号）；右侧时间、未读数红点徽标（0 不显示，>99 显示 `99+`）
- [ ] 2.4 覆盖空态与失败态（含重试入口），并保证列表节点不使用 `animation ... backwards` 以免小程序端不可见
- [ ] 2.5 `onShow` 回到会话 TAB 时重新拉取会话列表以刷新未读

## 3. 打开聊天与验证

- [ ] 3.1 点击会话行按既有方式跳转 `/TUIKit/components/TUIChat/index?conversationID=<会话ID>`
- [ ] 3.2 执行 `npm run build:mp-weixin` 构建通过，并按验证规格逐项核对消息通知页 6 个 TAB 与会话列表行为
