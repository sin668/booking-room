# 验证报告 — im-message-callback-sync

- 日期：2026-10-22
- workflow：tweak（preset）｜phase：verify｜verify_mode：full｜review_mode：off
- 绑定分支：`main`（isolation：current，未建分支/worktree，按用户要求）
- 基线：`base_ref=49d24da`，实现提交 `9153c5c`、`210016e` + 本轮修复提交
- 产物：`openspec/changes/im-message-callback-sync/{proposal.md,design.md,tasks.md,specs/im-message-sync/spec.md}`

## Summary

| 维度 | 结论 |
| --- | --- |
| Completeness | 19/19 任务勾选；4 条 ADDED Requirements 全部有实现落点 |
| Correctness | 17/17 Scenario 有代码路径 + 测试覆盖（前端 3 条以代码走查 + 构建验证） |
| Coherence | 与 design.md 取舍一致；delta spec 与 design doc 无未记录矛盾 |

**最终结论：PASS（0 CRITICAL / 0 IMPORTANT 未闭环）**

## 1. 任务完成度

`grep -c '^\- \[ \]'` = 0，`^\- \[x\]` = 19（含第 5 节 5 条验证阶段修复任务）。改动文件与 tasks 描述一一对应：
br-server `app/core/{im,config}.py`、`app/models/im_message.py` + alembic 迁移、`app/services/{im_callback_service,im_media_service}.py`、`app/api/routes/{im_callback,chat}.py`、`app/main.py`、`tests/test_im_callback_sync.py`；br-app `src/api/chat.js`、`src/utils/im.js`、`TUIKit/components/TUIChat/message-list/index.vue`。

## 2. 需求 → 实现映射

| Requirement | 实现落点 | 关键场景证据 |
| --- | --- | --- |
| 单聊消息服务端回调落库 | `br-server/app/api/routes/im_callback.py`（校验→分发→立即返回→BackgroundTasks）、`app/services/im_callback_service.py`、`app/core/im.py::verify_callback_sign` | `TestCallbackRoute`、`TestSignVerification` |
| 会话媒体转存对象存储 | `app/services/im_media_service.py`（httpx 流式限长 + `get_storage_adapter()` 复用） | `TestMediaTransfer`、`TestMediaDownloadLimit` |
| 已读状态服务端回调回写 | `im_callback_service.py::apply_msg_report` | `TestMsgReport`（含重复上报幂等） |
| 会话历史消息查询接口 | `app/api/routes/chat.py::get_chat_messages`（`get_current_user_id` 鉴权、peer 归一、limit/before） | `TestChatHistoryAPI`（越权/未登录/归一） |
| 会话窗口优先使用数据库消息数据 | `br-app/src/utils/im.js::loadChatMediaMap`/`applyChatMediaUrls` + `message-list/index.vue` | 代码走查 + `npm run build:mp-weixin` |

## 3. 检查与证据（真实执行结果）

| 检查 | 命令 | 结果 |
| --- | --- | --- |
| 定向单测 | `/opt/miniconda3/envs/booking-room/bin/python -m pytest tests/test_im_callback_sync.py -q`（cwd=br-server） | **27 passed** |
| 全量回归 | `python -m pytest -q`（cwd=br-server） | 14 failed / 1050 passed / 16 skipped；14 项失败全部命中 `git diff --name-only` 之外的既有基线文件，IM/chat/回调相关文件零失败 |
| 小程序构建 | `cd br-app && npm run build:mp-weixin` | **exit 0**，无新增报错 |
| 安全扫描 | 新增代码 grep 密钥/凭据、`UPLOAD_SCOPES` 差异 | 无硬编码密钥；未扩大上传 scope 白名单；Token 只从 `settings` 读取 |

## 4. 集成代码审查（唯一一次，覆盖最终 diff）

`tweak` preset 的 `review_mode: off` 只意味着不排自动审查队列；本轮仍完成了独立审查者对全量 diff 的审查，结果为 **FAIL**，发现并闭环如下（详见 `design.md` 的「验证阶段修复」）：

- CRITICAL ×1：`IM_CALLBACK_TOKEN` 为空时放行未签名回调（`SdkAppid` 是 `/api/v1/chat/user-sig` 下发的公开值）→ 可伪造写库并借 `fetch_and_upload` 形成 SSRF、结果经历史接口回显。修复为**默认拒绝**，并补「缺 Token」「伪造签名」回归用例。
- IMPORTANT ×3：① 媒体转存夹在消息 commit 之前且只捕获 `httpx.HTTPError`（`InvalidURL` 不属于该族）导致消息随转存异常回滚 → 改为先 commit、捕获 `Exception`；② 10MB 上限在 `response.content` 全量入内存后校验，形同虚设 → 改 `client.stream` + 边读边限长（`MediaTooLarge`）；③ 前端 `msg_key -> oss_url` 映射永久缓存且跨会话错配 → 改为按新消息/失败刷新 + 2s 最短间隔 + 会话不回写。
- WARNING/SUGGESTION：回调体非对象 500、`peer` 大小写与连字符未归一、`is_read` 与迁移 `server_default` 不一致、匹配键缺元素类型 → 已全部修复；「只覆盖 `imageInfoArray[0]`」「不做 `IntegrityError` 吞异常」「测试复用 `db_session`」为**已接受偏差**，理由与影响记录在 `design.md`。

`verify_failures=1`（首次验证因上述 CRITICAL/IMPORTANT 回 build），修复后回归通过。

## 5. delta spec 与 design doc 一致性

无未记录矛盾：默认拒绝鉴权、先 commit 后转存、流式限长、映射按需刷新、peer 归一均已同步写入 delta spec 的 MUST/MUST NOT 条款与 design.md。两处已知文档漂移已记录并接受（不回 build 改写，属 Verify 阶段只读约束）：

- `tasks.md` 1.2 仍写「空时跳过 Sign 校验」，其语义被同文件 5.1 覆盖（默认拒绝）。
- `design.md` 第 1 节首条仍描述「配置了 Token 才校验」，同文件「运维」与「验证阶段修复」明确了默认拒绝的最终行为。

## 6. 交付后端到端验收仍需人工完成（不在本次代码验证范围）

1. 远端执行 `alembic upgrade head` 创建 `im_messages`。
2. 腾讯云 IM 控制台配置回调 URL + Token，启用「发单聊消息之后回调」「单聊消息已读上报后回调」。
3. `.env` **必须**配置 `IM_CALLBACK_TOKEN`，否则回调一律不落库（默认拒绝）。
4. 小程序 `uploadFile/downloadFile` 域名白名单补充 OSS 域名。
5. 真机/开发者工具验证图片语音实际渲染为 OSS 地址（代码与构建已验证，运行态需设备确认）。
