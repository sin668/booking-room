# 验证报告：conversation-peer-profile

- 日期：2026-10-10
- 工作流：Comet Classic / tweak（`build_mode: direct`、`review_mode: off`、`verify_mode: full`）
- 基线：`de6be2a`；提交：`46b5eca`（实现）、`45f04cb`（变更产物）
- 结论：**PASS**（无 CRITICAL / IMPORTANT；1 项 WARNING 为「需真机/模拟器确认」，1 项 SUGGESTION 已记录）

## 一、需求与验收对象

用户诉求：消息通知页「会话」TAB 中，发送者看不到接收者头像（接收者在本系统是有头像的）；接收者侧应显示发送者头像与昵称；双方都要以红点数字显示未读条数并在对方回复后及时刷新。

根因（已用依赖源码证实）：`chat-uikit-engine-lite` 的会话模型
`getAvatar()` 读取 `this.userProfile.avatar`，`getShowName()` 读取 `remark || userProfile.nick || userProfile.userID`
（证据：`br-app/node_modules/@tencentcloud/chat-uikit-engine-lite/index.js` 偏移 25068 / 25601）。
本系统只在 `br-server/app/api/routes/chat.py:16` 签发 UserSig，从未把昵称/头像写入腾讯云 IM 用户画像，
所以 `userProfile` 只有 `userID`（平台 `username`）且 `avatar` 为空 —— 页面渲染无缺陷，缺的是数据源。

## 二、full 验证 7 项检查

| # | 检查项 | 结果 | 证据 |
| --- | --- | --- | --- |
| 1 | tasks.md 全部完成 | PASS | 7/7 `- [x]`；`comet guard build` 的「tasks.md all tasks checked」已 PASS |
| 2 | 改动文件与 tasks 描述一致 | PASS | `git diff --stat de6be2a...HEAD`：仅 `br-app/src/utils/im.js`、`br-app/src/store/modules/user.js`、新增 `br-app/scripts/verify-im-peer-profile.js`、`br-app/package.json` + 本 change 产物，与任务 1.1–3.2 一一对应 |
| 3 | 编译通过 | PASS | Runtime build 证据 `openspec/changes/conversation-peer-profile/.comet/checks/d847f7e7-*.log`（`npm run build:mp-weixin`，cwd `br-app`，exit 0）；产物含 `dist/build/mp-weixin/utils/im.js`、`store/modules/user.js` 中的 `setIMProfile`/`updateMyProfile` 引用，未被 tree-shaking 剔除 |
| 4 | 相关测试通过 | PASS | `test:im-peer-profile`（新增自检）通过；回归 `test:conversation-tab`、`test:profile-menu` 通过 |
| 5 | 无明显安全问题 | PASS | 无新增密钥/凭据；仅把用户自设的昵称与已有头像 URL 写入 IM 画像；`updateMyProfile` 失败只 `console.warn`，不影响 IM 就绪；payload 过滤空字段，避免清空画像 |
| 6 | 最终集成代码审查 | 已执行（Agent 内联）| `review_mode: off` 关闭自动独立审查，故由 Verify 对最终 diff 做一次集成审查：确认 `ensureIM` 与 `setIMProfile` 双向时序（IM 先就绪→store 触发立即推送；IM 后就绪→`ensureIM` 末尾 `pushIMProfile()` 补推，`initPromise` 失败路径不置 `imInitialized`，下次重试）；确认 `utils/im.js` 不 import store，无循环依赖；确认会话行渲染未改动。无正确性/安全/边界问题 |
| 7 | 核心场景、失败与边界场景 | PASS（静态/自检）+ 1 项待真机确认 | 见下表 |

## 三、delta spec 场景覆盖

Requirement: Conversation peer profile

| 场景 | 验证方式 | 结果 |
| --- | --- | --- |
| Sender sees receiver avatar | 接收者客户端在 IM 登录后写入画像（`App.vue:17` autoLogin→`ensureIM()`；`fetchUserInfo()`→`setIMProfile`），会话行读取 `getAvatar()`；自检断言链路存在 | PASS（代码级）；头像实际显示需模拟器确认 |
| Receiver sees sender nickname and avatar | `getShowName()` 在 `nick` 有值时优先于 `userID`，故昵称不再回显账号名 | PASS（代码级）；同上待模拟器确认 |
| Profile change propagates | `updateProfile()` 成功后调用 `setIMProfile`，`imInitialized` 为真时立即 `updateMyProfile` | PASS（自检断言 + 代码路径） |
| Peer without avatar falls back | 模板保留 `v-if="item.avatar"` 与 `conv-avatar-fallback` 首字母占位；payload 不含空 `avatar` 不会覆盖 | PASS（自检断言） |

未读红点及时性（用户第二项诉求）：`TUIStore.watch(StoreName.CONV, { conversationList })` 在 SDK 收到新消息/画像变更时重排会话列表（依赖源码偏移 41498 `onConversationListUpdated` → `TUIStore.update(CONV,'conversationList', filtered)`），小程序退后台断连由页面 `onShow` → `getConversationList()` 兜底。两项均有自检断言，本次**未新增代码**（上一 change 已实现），行为仍待模拟器确认。

## 四、tweak full 验证附加检查

- 检查项 2（design.md 决策遵循）：决策 1（客户端 `TUIUserService.updateMyProfile`，不新增后端接口）、决策 2（setter 落在 `utils/im.js`、store 喂数据、禁反向 import）、决策 3（只带非空字段）、决策 4（不改页面）均已实现。
- 检查项 3/7（`docs/superpowers/specs/` 技术 Design Doc）：tweak 预设不产出独立 Design Doc，跳过，以 change 目录 `design.md` 为设计依据。
- 检查项 5（proposal 目标）：达成；范围未外溢（未改后端、未改页面模板、未新增依赖）。
- 检查项 6（delta spec 与 design doc 矛盾）：无矛盾，故不触发 Spec 漂移决策点。

## 五、问题清单

- CRITICAL：无。
- IMPORTANT：无。
- WARNING（待用户确认，非代码缺陷）：腾讯云 IM 画像写入的生效需要在微信开发者工具用两个账号互发验证：
  1. A 给 B 发消息后，B 打开「会话」TAB 是否显示 A 的头像与昵称；
  2. B 回复后，A 侧同一会话行红点数字是否即时 +1，进入聊天页返回后是否清零；
  3. 若对方头像仍为空，先确认该用户自本次版本上线后完成过一次 IM 登录（画像由其自身客户端写入）。
- SUGGESTION：`fetchUserInfo()` 在部分页面（profile/settings/membership）会被多次调用，因此每次都会向 IM 重推一次相同画像。当前写法正确但有冗余网络调用；如后续观察到画像接口限流，可在 `pushIMProfile()` 增加「与上次成功推送内容相同则跳过」的去重（约 3 行）。本次按最小改动原则未加。

## 六、证据登记

- build：`comet check run conversation-peer-profile build --local -- npm run build:mp-weixin`（cwd `br-app`）
- verify：`comet check run conversation-peer-profile verify --local -- node scripts/verify-im-peer-profile.js`（cwd `br-app`，`.comet/check-policy.json` 将输入收窄到本次 4 个交付文件，规避仓库符号链接全量扫描）
