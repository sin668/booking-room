## 1. 服务端落库与接口

- [x] 1.1 `im_messages` 新增 `cloud_custom_data`(Text) / `is_revoked`(Boolean 默认 false) / `revoke_time`(BigInteger) 三列，补模型字段与 alembic 迁移
- [x] 1.2 `save_send_msg_callback` 落库 `CloudCustomData`；`parse_message` 保持既有语义不变
- [x] 1.3 新增 `apply_msg_withdraw(session, payload)`：按 `MsgKey` 标记撤回，缺字段直接返回 0，重复投递幂等；在回调路由分发 `C2C.CallbackAfterMsgWithDraw`
- [x] 1.4 `GET /api/v1/chat/messages` 排序改为 `msg_time desc, msg_seq desc, id desc`，返回 `elements`(MsgBody)、`cloud_custom_data`、`is_revoked`、`msg_seq`、`im_from_account`、`im_to_account`、`media_url`/`oss_url`、`is_read`
- [x] 1.5 扩展 `tests/test_im_callback_sync.py`：撤回回调标记/幂等/缺字段、CloudCustomData 落库、历史接口返回重建字段

## 2. 客户端重建与翻页

- [x] 2.1 新增 `br-app/src/utils/im-history.js`：`buildImHistoryMessages(rows, ctx)` 按渲染契约把数据库记录重建为 SDK 结构消息（未知元素类型跳过，媒体地址 oss_url 优先）
- [x] 2.2 `br-app/src/utils/im.js` 删除 `loadChatMediaMap` / `applyChatMediaUrls` 及其缓存状态，新增 `fetchImHistoryPage(conversationID, before)` 拉取更早一页并返回 `{messages, hasMore}`
- [x] 2.3 `message-list/index.vue` 去掉 `applyChatMediaUrls` 引用与调用；`getHistoryMessageList` 在 `isCompleted` 为真时走数据库翻页并用 `TUIChatService.updateMessageList(msgs, 'unshift')` 注入；「查看更多」显示条件改为 `!isCompleted || dbHasMore`，会话切换时重置 `dbHasMore`
- [x] 2.4 删除 `scripts/verify-chat-media-map.js`，新增 `scripts/verify-im-history.js`（媒体地址覆盖逻辑已彻底移除、重建字段齐全、注入走 unshift 且不触发已读）与 `scripts/verify-im-history-merge.mjs`（引擎 unshift 去重/前插/不 setMessageRead 的行为校验），更新 `package.json` 脚本并接入 `test:scripts`

## 3. 验证与文档

- [x] 3.1 br-server 测试跑绿（`pytest tests/test_im_callback_sync.py` + 全量测试），alembic 迁移在本地库 upgrade 通过
- [x] 3.2 br-app `npm run build:mp-weixin` 通过，产物中确认已无 `applyChatMediaUrls`、含数据库翻页调用
- [x] 3.3 `br-app/bug-fixed.md` 增补一节：7 天漫游窗口、为什么不能整体换成数据库、重建字段契约与已知边界
