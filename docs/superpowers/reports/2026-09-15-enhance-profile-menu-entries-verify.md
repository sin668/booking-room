# Verification Report: enhance-profile-menu-entries

**Date**: 2026-09-15
**Change**: enhance-profile-menu-entries
**Workflow**: tweak (verify_mode: full，含 2 个 delta spec capability)
**Verifier**: agent (comet-verify + openspec-verify-change) + 独立只读代码审查 subagent

---

## Summary

| Dimension    | Status                                        |
|--------------|-----------------------------------------------|
| Completeness | 7/7 tasks ✓，2 capabilities / 9 scenarios 全部有实现映射 |
| Correctness  | 构建 exit 0 ✓，本次相关校验脚本 exit 0 ✓，0 CRITICAL     |
| Coherence    | design.md 决策全部落地 ✓（产物漂移已在第 1 轮修正）        |

**Final Assessment**: 无 CRITICAL / 未处置的 IMPORTANT。3 项存量观察记录在案，不阻塞归档。

---

## 验证证据（本轮实际执行）

| 命令 | 结果 |
|------|------|
| `comet check run enhance-profile-menu-entries build --local -- npm run build:mp-weixin`（cwd `br-app`） | exit 0，日志 `openspec/changes/enhance-profile-menu-entries/.comet/checks/3835fbfa-*.log` |
| `npm run test:profile-menu && npm run test:profile-links` | exit 0（两条均输出「验证通过」） |
| `comet check run enhance-profile-menu-entries verify --local -- npm run build:mp-weixin`（cwd `br-app`） | exit 0，日志 `.comet/checks/50ad7fc6-*.log`；`comet guard verify --apply` 5/5 PASS |
| 变异测试（4 组）：改跳转目标 / 删充值文案 / 解构少一个槽位 / 未读改前端推算 | 4/4 均使校验脚本失败，恢复后 exit 0 |
| `comet classic openspec -- validate enhance-profile-menu-entries` | valid |
| `comet state scale enhance-profile-menu-entries` | full（7 tasks / 2 capabilities / 10 files） |

环境事实：本机 `comet` 与 `node` 位于 `~/.reflex/.nvm/versions/node/v22.22.0/bin`，非交互 shell 不加载 `.zshrc`，需显式加入 PATH。`comet check run` 记录的证据按调用目录匹配，`check` 与 `guard` 必须在同一目录（本 change 为 `br-app`）执行，否则 guard 报「No current Runtime build evidence」。

---

## Completeness

**Task completion**：`tasks.md` 7/7 全部 `[x]`，与 `git show --stat` 的两个提交（`tweak:` 实现 + `docs:` 产物校正）一致。

**Spec coverage**

- `student-review-ui` /「My reviews entry on profile page」→ `br-app/src/pages/profile/index.vue:66-68`（meta 文案）+ `:192` `reviewSummary` + `:236` 取数。
- `message-notification-ui` /「Profile page message entry with unread count」→ `index.vue:69-75`（新行 + 跳转）+ `:195` `unreadMessageSummary` + `:237` 取数。

## Correctness — scenario 逐条

| Scenario | 结论 | 依据 |
|----------|------|------|
| Menu item rendered consistently | PASS | 结构与相邻行同为 icon 色块 + 文案 + `menu-item-meta` + `menu-arrow` |
| Menu item shows review count | PASS（静态） | 后端 `total` 由独立 `func.count` 且与 `mine` 分支共用同一 WHERE（`review_service.py:207-215`），`page_size: 1` 不影响总数；真机数值未验证 |
| Menu item hides count when no review | PASS | `> 0 ?` 守卫 + 脚本断言「0 留空」 |
| Navigate to my reviews | PASS | 跳转与 `mine=1` 参数未改动 |
| Unauthenticated tap prompts login | 存量口径 | 见「观察项 O2」 |
| Message entry navigates to notification center | PASS | `/pages/notifications/index` 已在 `pages.json:94` 注册且非 tabBar；消息页仅显式操作标已读（`pages/notifications/index.vue:261,275`），入口本身不改已读态 |
| Message entry shows unread count | PASS | 取 `total_unread`，与首页铃铛同接口同口径（`pages/index/index.vue:326`） |
| Message entry hides count when nothing unread | PASS | 同上 `> 0 ?` 守卫 |
| Unread count refreshes on page show | PASS | `onShow` → `loadProfileStats()`，`profileRequestId` 竞态保护覆盖新增两项 |

**安全/权限**：未新增鉴权面。`mine=true` 的 user_id 只取自 token（`routes/review.py:28-37` 未登录直接 401），前端不传身份参数，无越权/IDOR 风险；无硬编码密钥；未登录时整块菜单不渲染且 `onShow` 不发请求，不产生 401 噪声。

**边界**：接口失败回落 0（与页面既有 3 项统计同口径）；数量为 0 时右侧留空；`Promise.allSettled` 解构槽位与 6 个 promise 对齐（曾出现错位，已由脚本固化为断言）。

## Coherence

design.md 4 项决策（并发挂载 `loadProfileStats`、复用 `.icon.icon-bell` + 单条页面样式、复用既有接口不新增后端、0 值留空仿 `followSummary`）均已落地。第 1 轮验证发现的产物漂移（`unreadSummary` vs `unreadMessageSummary`、32rpx vs 34rpx、「单文件」表述、「两个只读 GET」表述）已按 `verify-fail` 回 build 修正并提交。

项目模式一致性：新行完全复用 `menu-item` / `menu-icon` / `menu-item-meta` / `menu-arrow` 既有类；校验脚本沿用 `br-app/scripts/verify-*.js` + `test:*` 既有约定。

---

## 观察项（存量，不在本 change 范围）

- **O1 — 仓库既有红灯**：`npm run test:refactor`（`formatBookingStatus('confirmed')` 期望「已预约」）与 `npm run test:course-schedule`（`formatCourseStartDate` 期望含「日」）在 `HEAD` 纯净副本上同样失败（已用 `git archive` 复核），与本次改动无交集；两者位于 `test:scripts` 链中，导致该链在第 3 步即中断，`test:profile-menu` 在链内实际不可达。建议单开 change 校准这两处文案断言。
- **O2 — 不可达的存量 scenario**：`student-review-ui` 的「未登录点击提示登录」场景，在「我的」页菜单整体处于 `v-if="userStore.isLoggedIn"`（`index.vue:3`）时无法触发。MODIFIED 需求按 OpenSpec 规则整条重述并保留该场景，未在归档时删除既有覆盖。若要改写应另立 change。
- **O3 — 未读汇总非纯只读**：`get_unread_summary` 会 `_get_or_create_preference_model` 并 `flush`（`notification_service.py:108,198-213`），首次访问写一行 `notification_preferences`；该写路径在首页铃铛调用时已存在，本次不新增风险，已在 proposal.md 如实记录。另：`total_unread` 只累加偏好开启的类型（`notification_service.py:121-125`），用户关闭某类推送到「我的」页时可能显示空白而消息中心仍有未读——与首页铃铛口径一致，符合 spec 要求。

---

## Verdict

PASS。可进入归档。
