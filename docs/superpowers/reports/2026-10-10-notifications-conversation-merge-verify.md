# 验证报告: notifications-conversation-merge

**日期**: 2026-10-10
**验证模式**: full（存在 delta spec）
**结论**: PASS

## 背景（用户三项诉求）

1. 学习者478642 无头像时，TUIChat 会话窗口左侧气泡错误显示成林sam~（当前用户）的头像，应显示默认头像。
2. 会话消息应显示在「全部」TAB：在通知列表最上方加一行，左侧「话」图标 +「会话」标签，右侧时间 + 未读小红点（无数字）。
3. 有未读会话消息时首页铃铛也要显示红点（把未读会话计入）。

## 检查清单

| # | 检查项 | 结果 | 证据 |
|---|--------|------|------|
| 1 | tasks.md 全部完成 | PASS | 5/5 checked |
| 2 | 改动文件与 tasks 一致 | PASS | message-bubble.vue、notifications/index.vue、index/index.vue、verify 脚本 |
| 3 | 编译通过 | PASS | `npm run build:mp-weixin` exit=0，build 证据已登记 |
| 4 | 相关测试通过 | PASS | `node scripts/verify-im-peer-profile.js` exit=0 |
| 5 | 无安全问题 | PASS | 纯前端渲染/订阅逻辑，无新增外部输入或密钥 |
| 6 | 集成代码审查 | PASS | 见下 |
| 7 | 核心/边界场景 | PASS | 见 delta spec 覆盖 |

## 集成代码审查

- **头像回退（message-bubble.vue）**：`resolvedAvatarUrl` 仅对 `flow === 'in'` 生效；`!avatar` 或 `avatar === selfAvatar`（读 `StoreName.USER.userProfile.avatar`）时传 `''`，`Avatar` 组件对空 url 回退内置 `avatar_21.png`。out 消息不受影响，仍显示自己头像。极端：对方恰好与自己用同一头像 URL 会被判为默认，属可接受权衡。
- **全部 TAB 会话行（notifications/index.vue）**：`showConversationEntry = currentType==='all' && conversationSummary`；`conversationSummary` 取 `conversations[0]`（IM 列表按最后消息时间倒序），`hasUnread = 任一会话 unreadCount>0`。红点复用 `unread-dot`（无数字）。`onShow/switchType/refreshList/loadInitialData` 在 'all' 时也 `loadConversations()`，复用既有 `conversationList` 订阅。点击 `goConversationTab → switchType('conversation')`。无会话时不渲染该行，通知列表照常。
- **铃铛（index/index.vue）**：`loadIMUnread` 先 `ensureIM()`，未就绪/游客直接返回不影响后端红点；订阅 `StoreName.CONV.totalUnreadCount`（引擎默认 0，SDK `getTotalUnreadMessageCount` 初始化 + `TOTAL_UNREAD_MESSAGE_COUNT_UPDATED` 更新）。`hasNotification || hasIMUnread` 控制红点。`onHide/onUnload` 取消订阅避免泄漏。依赖上一 change 的 `resetIM`：换账号后 `ensureIM` 重新登录，`totalUnreadCount` 归属正确账号。

## Delta Spec 场景覆盖（message-notification-ui）

- 对方无头像显示默认 / 自己消息保留自己头像 → resolvedAvatarUrl 分支 ✓
- 全部 TAB 顶部会话行（话/会话 + 时间 + 无数字红点）/ 无会话不显示 / 点击进入会话 TAB → showConversationEntry + goConversationTab ✓
- 仅未读会话点亮铃铛 / 无未读不点亮 → hasNotification || hasIMUnread + totalUnreadCount ✓

## WARNING

- 三项均为 UI/前端逻辑，源码断言 + 构建已覆盖正确性；「对方无头像显示默认」「全部 TAB 会话行」「铃铛计入会话未读」的端到端表现建议真机回归（尤其多账号切换后 `totalUnreadCount` 是否随之刷新）。

## SUGGESTION

- 「全部」TAB 会话行为单条聚合入口（最新会话 + 是否有未读），非逐条会话；若后续需要每条会话都进「全部」，可改为遍历 `conversations` 渲染多卡片。

## 最终结论

**PASS** — 7 项全通过，无 CRITICAL/IMPORTANT。可归档。
