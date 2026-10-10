# Verification Report: conversation-unread-badge

- 日期：2026-10-10
- workflow：tweak（classic）
- verify_mode：full（scale 建议 full：tasks 4 > 3）
- review_mode：off —— tweak 预设默认关闭自动代码审查，按 comet-verify 规则在此记录原因；本次改动为 4 行生命周期修复，正确性由 SDK 源码取证 + 编译产物核对 + assert 自检覆盖
- 基线：`4871f93 tweak: 离开 TUIChat 时释放 IM 当前会话，修复会话 TAB 未读红点不显示`

## Summary

| Dimension | Status |
| --- | --- |
| Completeness | 4/4 tasks 勾选；delta spec 1 个 requirement（4 场景）全部有实现落点 |
| Correctness | 根因与修复均由 SDK 源码 + 编译产物证据支撑；相关自检 4/4 通过 |
| Coherence | 符合 change design.md 三条决策；与官方 TUIKit 取数口径一致；无新增依赖、无后端改动 |

**结论：PASS（0 CRITICAL / 0 IMPORTANT / 1 WARNING / 1 SUGGESTION）**

## 检查项与证据

1. **tasks.md 全部完成** — `comet guard build` 的 `[PASS] tasks.md all tasks checked`；4 项均为 `[x]`。
2. **改动文件与任务描述一致** — `git show --stat 4871f93`：实现文件仅 `br-app/src/TUIKit/components/TUIChat/index.vue`（+4 行）与 `br-app/scripts/verify-im-peer-profile.js`（+14 行），其余 5 个文件为本次 change 的 OpenSpec 产物，与任务 1/2/4 一一对应，无越界改动。
3. **编译通过** — `comet check run conversation-unread-badge build --local -- npm run build:mp-weixin` → `exit=0`，日志 `openspec/changes/conversation-unread-badge/.comet/checks/3df9506c-34c5-4615-b0bb-d8e9be3bd4aa.log`；产物 `DONE Build complete.`。
4. **相关测试通过** — `test:im-peer-profile`（含本次新增的会话释放断言）、`test:conversation-tab`、`test:wechat-appid`、`test:profile-links` 四条均通过。注：`npm run test:scripts` 全链中 `test:refactor`、`test:course-schedule` 为**本次改动前既已失效**的断言，与本 change 无关，未越界修改。
5. **无安全问题** — diff 内无密钥、无新增外部输入、无 eval/动态拼接；未新增接口与依赖。
6. **集成代码审查** — `review_mode: off`（tweak 预设），按规则跳过并在本节记录原因；替代证据为下方场景取证。
7. **需求/失败/边界场景**（openspec-verify-change 的 Completeness+Correctness）：

   | Requirement / Scenario | 取证 |
   | --- | --- |
   | Leaving the chat page clears the current conversation | `br-app/src/TUIKit/components/TUIChat/index.vue:103` `onUnload` 内 `reset()`；`reset` = `TUIConversationService.switchConversation('')`；引擎 `switchConversation` 空 ID 分支写入 `currentConversationID=""`、`currentConversation=null`（`node_modules/@tencentcloud/chat-uikit-engine-lite/index.js` 42904 起） |
   | Peer reply after leaving the chat window | 引擎 `updateTargetMessageList` 以 `currentConversationID` 过滤推送消息，`0===n.length` 直接返回，不再调用 `chat.setMessageRead`；会话 `updateUnreadCount` 走 `this.unreadCount += i` 累积分支（`lite-chat/professional.es.js` 294790 起）；徽标渲染口径与官方 `src/TUIKit/components/TUIConversation/conversation-list/index.vue:55` 一致 |
   | Next chat entry opens the requested conversation | `entry-chat-only.ts:26` `onLoad` 仍调用 `switchConversation(options.conversationID)`；清除后 `n===e` 的同会话短路不再可能命中 |
   | Reading inside the chat window still clears unread | `enableAutoMessageRead` 默认 `true`（引擎 `defaultStore`），进入会话时 `switchConversation` 对旧/新会话调用 `setMessageRead` → 未读保持 0，行为未回归 |

   编译产物核对（小程序端）：`br-app/dist/build/mp-weixin/TUIKit/components/index.js` 内 `U=()=>{e.et.switchConversation("")}` 且 `onUnload(()=>{U(),a.logout()...})`，说明修复确实进入了小程序运行包，而非仅存在于源码。

## 与 Design Doc 的一致性（tweak：设计记录为 change 内 design.md）

- 决策 1（`onUnload` 释放 + 保留 `onUnmounted`）：实现一致，未新增状态判断。
- 决策 2（不改动会话列表读取路径、不加 `getTotalUnreadMessageCount` 兜底）：实现一致，页面文件零改动。
- 决策 3（沿用 assert 脚本而非测试框架）：实现一致，断言追加在 `verify-im-peer-profile.js`。
- delta spec 与 design.md 无矛盾，无需 Spec 漂移决策。
- `docs/superpowers/specs/` 下无本 change 的独立 Design Doc（tweak 跳过 brainstorming/writing-plans，设计记录在 `openspec/changes/conversation-unread-badge/design.md`），可定位。

## WARNING / SUGGESTION

- **WARNING（需用户在微信开发者工具实机确认）**：① 从「会话」TAB 进入聊天窗口 → 返回 → 对方再发一条消息，红点应显示数字；② 在聊天窗口内收到的消息仍不计入未读；③ 返回后再次点击另一条会话，聊天窗口应显示新会话而非上一个残留会话。此三项为运行时/真机行为，本地无法自证。
- **SUGGESTION**：`onUnmounted` 与 `onUnload` 现在都会调用 `switchConversation('')`（引擎侧幂等），可择机移除 `onUnmounted` 分支以消除重复；本次按最小改动与「H5 场景仍需要它」的取舍保留，不构成偏差。

## 退出条件核对

- 验证报告已写入本文件并在 `.comet.yaml` 记录 `verification_report`
- `branch_status` 仍为 `pending`（归档阶段处理）
- 由 `comet guard conversation-unread-badge verify --apply` 推进 phase
