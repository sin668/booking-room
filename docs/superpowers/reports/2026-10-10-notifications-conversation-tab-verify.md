# Verification Report: notifications-conversation-tab (2026-10-10)

- workflow: tweak / schema: spec-driven / verify_mode: full（存在 delta spec）
- review_mode: `off`（tweak 预设状态记录），按 comet-verify 规则跳过自动代码审查，本轮改由下方的人工规格比对 + 断言脚本承担；原因记录于此。
- 基线：`base_ref = 511040a`，实现提交 `10a8035`、`114d0a7`、`3cd4777`

## Summary

| 维度 | 结果 |
| --- | --- |
| Completeness | 9/9 任务已勾选；delta spec 3 个需求全部在源码中找到实现证据 |
| Correctness | 3 需求 / 13 场景：11 项静态与构建证据通过，2 项需小程序模拟器确认 |
| Coherence | 遵循 design.md 全部 5 项决策；发现并修复 1 个 IMPORTANT 缺陷 |

## 证据

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| 编译构建 | `comet check run notifications-conversation-tab build --local -- npm run build:mp-weixin`（cwd `br-app`） | exit=0，日志 `openspec/changes/notifications-conversation-tab/.comet/checks/909a75a7-*.log`；epoch=4 |
| 行为断言脚本 | `node scripts/verify-notification-conversation-tab.js` | 「消息通知页「会话」TAB 验证通过」 |
| OpenSpec 规格 | `comet classic openspec -- validate notifications-conversation-tab` | valid |
| 产物落地 | `dist/build/mp-weixin/pages/notifications/index.wxml` / `index.wxss` | `conversation-item`、`conv-badge`、`conv-name{...text-overflow:ellipsis}`、`.tab-item{flex:1;min-width:0}` 均在编译产物中 |

## 规格场景比对

### Requirement: Notification center page（MODIFIED）
- 短标签「预约/活动/报告/到店」：`notificationTypes.js:4,14,24,34`，脚本断言逐 key 校验；`settingLabel` 全称保留，设置页 `pages/settings/index.vue:120` 不受影响。
- 顺序「全部 → 会话 → 四类」：`pages/notifications/index.vue:188-195`。

### Requirement: Notification filtering（MODIFIED）
- 「MUST NOT 以 conversation 请求通知列表」：`index.vue:297` 条件同时排除 `all` 与 `CONVERSATION_TAB`。

### Requirement: Conversation tab list（ADDED）
- 数据源：`ensureIM()` + `TUIConversationService.getConversationList()` + `TUIStore.watch(StoreName.CONV, { conversationList })`（`index.vue:379-402`），未新增后端接口与第三方依赖。
- 左头像/昵称/最新一行、右时间/未读红点、`>99 → 99+`、未读 0 不渲染徽标：`index.vue:70-100`。
- 单行截断加省略号：`.conv-name` / `.conv-summary` 的 `overflow:hidden;white-space:nowrap;text-overflow:ellipsis`，父级 `min-width:0`（`.conv-line`），编译产物已核对。
- 无头像兜底：首字母占位块 `index.vue:83-85`。
- 空态、失败态与重试：`index.vue:51-68`。
- 返回后未读刷新：`onShow` 命中会话 TAB 时重新拉取（`index.vue:240-249`）。
- 小程序列表可见性（项目 pitfall）：脚本断言全文无 `animation:...backwards`。

### Requirement: Conversation chat entry（ADDED）
- 复用既有聊天页：`index.vue:404-408` 跳转 `/TUIKit/components/TUIChat/index?conversationID=`，与 `pages/edu-market/detail.vue:241` 同一已验证路径；`TUIChat/entry-chat-only.ts:18-26` 要求 `C2C`/`GROUP` 前缀，SDK 的 `conversationID` 天然满足。
- 未登录：沿用 `requireLogin()` 既有引导（`index.vue:257-262`）。

## 发现的问题

1. **IMPORTANT（已修复，`3cd4777`）**：顶部 `mark-all` 的可点区域在会话 TAB 仍然生效，而切换 TAB 不会清空 `notifications`，`markAllNotificationsRead(type)` 会把 `conversation` 当通知类型提交；若走到 `type` 为空的分支还会把所有类型的通知批量标记为已读。修复为 `markAllRead()` 在会话 TAB 直接返回，并给脚本增加同口径断言。触发 verify-fail → build 一次往返（`verify_failures=1`）。
2. **WARNING（接受，不修）**：会话列表不做分页。`getConversationList()` 返回首页会话，本业务只有 1V1 咨询产生的少量会话，达到 SDK 首页上限的概率极低；若日后群聊/会话量增大，需要按 SDK 游标续拉。
3. **WARNING（需人工确认，见下）**：真机/微信开发者工具的运行时行为无法由本环境验证。

## 未能由 Agent 验证的部分（需用户在微信开发者工具确认）

1. 会话 TAB 是否真的拿到会话（`chat-uikit-engine-lite` 在主包页面订阅 `StoreName.CONV.conversationList` 的时序）；
2. 未读红点数字与进入聊天页返回后是否清零；
3. 6 个 TAB 在小屏机型（iPhone SE 宽度）是否仍不裁切。

构建与断言脚本只证明编译与静态口径正确，不替代上述模拟器确认。

## Final Assessment

无未闭合的 CRITICAL 问题；1 个 IMPORTANT 已修复并有断言防回归；2 个 WARNING 中 1 个已记录取舍理由，1 个转成交付前的用户人工确认清单。按 comet-verify 判定：通过（`verify_result` 由守卫记录）。
