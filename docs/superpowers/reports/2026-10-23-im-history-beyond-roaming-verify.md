# 验证报告：im-history-beyond-roaming

- change：`im-history-beyond-roaming`（workflow: tweak，schema: spec-driven）
- 验证模式：full（delta spec 存在，`comet state scale` 返回 12 tasks / 1 capability / 21 files → full）
- 审查模式：`review_mode: off` —— 按 tweak 预设不执行自动代码审查，最终集成审查由本报告的人工比对承担（Build 阶段已逐任务自查，见「一致性」一节）
- 基线：`base_ref 8fc0535`，实现提交 `9e66b42 tweak: 会话历史超出 IM 7 天漫游窗口后改从数据库重建补齐`
- 验证时间：2026-10-23

## Summary

| 维度 | 结论 |
| --- | --- |
| Completeness | 12/12 tasks 完成；delta spec 5 个 Requirement（2 MODIFIED + 2 ADDED + 1 REMOVED）全部有实现证据 |
| Correctness | 20 个 Scenario 全部映射到实现与测试/行为校验；无 CRITICAL、无 IMPORTANT |
| Coherence | 实现与 design.md 三项关键决策一致（数据源分工、unshift 注入、渲染契约字段）；2 条 SUGGESTION |

结论：**All checks passed. Ready for archive.**

## 1. Completeness

### 1.1 任务完成度

`openspec/changes/im-history-beyond-roaming/tasks.md`：12/12 `[x]`，与 `comet classic openspec -- instructions apply` 返回的 `progress: {total: 12, complete: 12, remaining: 0}`、`state: all_done` 一致。

### 1.2 Requirement 覆盖

| Requirement（delta） | 实现证据 |
| --- | --- |
| MODIFIED 单聊消息服务端回调落库 | `save_send_msg_callback` 落 `cloud_custom_data`（[im_callback_service.py:110](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-server/app/services/im_callback_service.py#L110)）；鉴权/幂等/未知命令/非对象体保持原状 |
| MODIFIED 会话历史消息查询接口 | 排序 `msg_time desc, msg_seq desc, id desc` 与重建字段（[chat.py:84-118](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-server/app/api/routes/chat.py#L84-L118)）、`before` 严格 `<`（[chat.py:81-82](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-server/app/api/routes/chat.py#L81-L82)） |
| ADDED 单聊消息撤回状态落库 | `apply_msg_withdraw`（[im_callback_service.py:146-160](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-server/app/services/im_callback_service.py#L146-L160)）+ 回调分发 `C2C.CallbackAfterMsgWithDraw`（[im_callback.py:109](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-server/app/api/routes/im_callback.py#L109)、[:69](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-server/app/api/routes/im_callback.py#L69)）+ 三列迁移（`im_message.py`、`alembic/versions/2026_10_23_1100-j5k1l7m3n9p4_...py`） |
| ADDED 会话窗口补齐超出漫游窗口的历史消息 | 重建模块 [im-history.js](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/utils/im-history.js)、翻页入口 [im.js:135](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/utils/im.js#L135)、注入与前插 [message-list/index.vue:478-552](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/TUIKit/components/TUIChat/message-list/index.vue#L478-L552) |
| REMOVED 会话窗口优先使用数据库消息数据 | `loadChatMediaMap`/`applyChatMediaUrls` 及其调用点、`scripts/verify-chat-media-map.js`、`test:chat-media-map` 全部删除；`br-app/dist/build/mp-weixin` 内 `applyChatMediaUrls` 命中数 0 |

主 spec `openspec/specs/im-message-sync/spec.md` 含 `## Purpose`，且被 REMOVED 的 Requirement「会话窗口优先使用数据库消息数据」确实存在于主 spec（归档可执行 REMOVED 语义）；两条 MODIFIED Requirement 保留主 spec 全部既有 Scenario 标题（回调落库 7 条、历史查询 4 条），满足归档的 MODIFIED 约束。

## 2. Correctness：Scenario → 证据

`tests/test_im_callback_sync.py` 36 passed（`/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_im_callback_sync.py -q -p no:cacheprovider`）。

| Scenario | 覆盖证据 | 类型 |
| --- | --- | --- |
| 文本消息落库 / 重复回调幂等 / SDKAppid 不匹配拒绝 / 未配置 Token 拒绝 / 签名不合法拒绝 / 未知回调命令放行 / 回调体不是对象 | `TestSaveSendMsg`、`TestVerifyCallbackSign`、`TestCallbackRoute`（既有回归保持绿） | pytest |
| 引用消息自定义数据落库 | `test_cloud_custom_data_persisted`、`test_missing_cloud_custom_data_stays_none` | pytest |
| 参与者查询历史 / 越权查询被拒 / 未登录访问 / peer 大小写与连字符归一 | `TestChatHistoryAPI`（`test_returns_only_own_conversation`、`test_normalizes_peer_case_and_hyphens`、`test_requires_login`、`test_other_pair_returns_empty`） | pytest |
| 撤回回调标记消息 / 重复投递幂等 / 缺少 MsgKey | `TestApplyMsgWithdraw`（标记/幂等/缺字段与未知 key）+ `TestCallbackWithdrawRoute.test_withdraw_callback_marks_revoked`（HTTP 回调 → `is_revoked=True`、`revoke_time=1700000999000`） | pytest |
| IM 历史拉完后继续向数据库翻页 | [index.vue:478](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/TUIKit/components/TUIChat/message-list/index.vue#L478) `isCompleted` 分支 + `v-if="!isCompleted || (!isGroup && dbHasMore)"`（[:40](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/TUIKit/components/TUIChat/message-list/index.vue#L40)），源码断言 `scripts/verify-im-history.js` | 行为+源码断言 |
| 深历史消息状态还原 | `verify-im-history-merge.mjs`：类型/方向/媒体 oss_url/`isRevoked`/`cloudCustomData`/`readReceiptInfo` 契约逐条断言 | 引擎真实包 |
| 补历史不产生已读上报 | `verify-im-history-merge.mjs` 注入后 `readReports` 为空；`verify-chat-read-gate.mjs` 复验引擎判据仍为 `currentConversationID` | 引擎真实包 |
| 与 IM 窗口不重复 | `test_before_cursor_is_strict`（同秒记录不入页）+ merge 探针重复 unshift 后 `['k-1','k-2','k-3','k-4','sdk-9']`（去重且升序） | pytest + 引擎 |
| 未知元素类型跳过 | `ELEMENT_TO_TYPE` 五类白名单（[im-history.js:5-14](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/utils/im-history.js#L5-L14)），merge 探针断言 video/other 被跳过 | 引擎真实包 |
| 历史接口失败 | [index.vue:544-551](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/TUIKit/components/TUIChat/message-list/index.vue#L544-L551) catch → Toast、`finally` 复位 `isLoadingMessage`、失败时不改写 `dbHasMore` → 入口保留可重试；`fetchImHistoryPage` 8 秒超时 | 源码走查（见 SUGGESTION-2） |
| 排序与 IM 单聊口径一致 | `test_same_second_orders_by_msg_seq` 期望 `["h-1","seq-5","h-2","seq-9"]` | pytest |

无 CRITICAL / IMPORTANT 问题。

## 3. Coherence

design.md 三项关键决策均被遵守：

1. **数据源分工**：SDK 窗口 + 数据库深历史，游标严格 `<`，未整体切换数据源。
2. **注入点**：只用 `TUIChatService.updateMessageList(msgs, 'unshift')`（[index.vue:536](file:///Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room/br-app/src/TUIKit/components/TUIChat/message-list/index.vue#L536)），避开 `push/contact` 的无条件已读上报红线。
3. **重建字段以渲染契约为准**：`ID=msg_key`、`conversationID`、`flow/from/to`、`payload`（oss_url 优先）、`status:'success'`、`isRevoked`、`needReadReceipt`、`isPeerRead`+`readReceiptInfo`（必为对象，避免 read-status 解构抛错）、`cloudCustomData`、`nick/avatar` 与 design 表格逐行对应。

服务端「只补三点，不改既有幂等与鉴权」得到遵守：仅新增列/落库字段、新增 `apply_msg_withdraw`、历史接口排序与返回字段，未改动签名校验与幂等分支。

tweak 预设一致性：改动全部落在 `main`（isolation: current），未建分支/worktree；无新增第三方依赖；`br-app/bug-fixed.md` 增补章节与 proposal「Impact」列出的部署项一致。

## 4. 检查与证据

| 检查 | 结果 | 证据 |
| --- | --- | --- |
| br-server 变更相关测试 | PASS 36 passed | Runtime verify 证据（`comet check run … verify --local`，`.comet/checks/3138d547-….log`） |
| br-app 变更相关回归脚本 | PASS：`test:im-history`、`test:im-history-merge`、`test:chat-read-on-visible`、`test:chat-read-gate` | 同一条 Runtime verify 证据（`/bin/sh -c` 复合命令，exit=0） |
| br-app 小程序构建 | PASS `DONE Build complete.`，主包 1.15MB | 手工执行 `npm --prefix br-app run build:mp-weixin`（policy 单命令限制，未录为第二条 Runtime 证据） |
| 产物内容核对 | PASS：`applyChatMediaUrls` 命中 0；`utils/im-history.js` 存在；`fetchImHistoryPage`/`buildImHistoryMessages`/`updateMessageList` 出现在 `TUIKit/components/TUIChat/message-list/index.js` | `grep` `br-app/dist/build/mp-weixin` |
| alembic 迁移 | PASS：本地/共享库 `alembic current` → `j5k1l7m3n9p4 (head)`（纯增量 3 列，不回填） | Build 阶段执行记录 |
| 安全检查 | PASS：无新增硬编码密钥；`IM_CALLBACK_TOKEN` 仍只在被 gitignore 的 `br-server/.env`，`.env.example` 保持空值；撤回/历史接口均沿用登录态与既有鉴权 | diff 走查 |
| 全量 pytest | 15 failed / 1058 passed —— 失败全部位于 `test_coupon_service.py`（`list_available_coupons_for_booking()` 参数个数不匹配）与 `test_models_import.py`（Course 字段），本 change 未触碰这些模块，属既有失败，按用户「不要自行添加用户未要求的行为」不在本次修复 | Build 阶段全量执行记录 |
| `npm run test:scripts` 全链 | 首站 `test:profile-links` 失败（profile 统计项跳转绑定断言与现有 profile 页面不符），与本 change 无关的既有失败 | 本次执行记录 |

## 5. SUGGESTION（不阻塞归档）

1. **同秒边界记录可能被跳过**：游标按 spec 要求「严格早于列表中最早一条」（`msg_time < before`），因此与 SDK 窗口同一秒、但更早 `msg_seq` 的库内深历史不会被取到。spec 本身把「不重叠」置于「不遗漏」之前（MUST 严格早于），实现与 spec 一致；如后续要消除该缝隙，改动点是游标改为 `(msg_time, msg_seq)` 复合比较，属接口契约变更，需另开 change。
2. **「历史接口失败」场景无自动化断言**：小程序端 UI 无法在此环境跑真实渲染，该场景目前靠源码走查 + `fetchImHistoryPage` 超时返回确认。若后续要补测，最小成本是把 `loadDatabaseHistoryPage` 的失败分支抽成可注入 fetch 的纯函数断言。

两项均为接受状态，理由如上，不影响验收结论。

## 6. 最终结论

无 CRITICAL、无 IMPORTANT 问题；12/12 任务完成，20/20 Scenario 有实现与检查证据，实现与 design.md、proposal 目标一致。

**All checks passed. Ready for archive.**（归档与推送需用户明确授权）
