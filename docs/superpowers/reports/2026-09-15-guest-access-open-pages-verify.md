# 验证报告：guest-access-open-pages

- 日期：2026-09-15
- Change：guest-access-open-pages（Comet tweak 预设）
- 验证模式：full（含 delta spec，按 comet-verify 分流规则显式设置）
- 审查范围输入：本次改动 diff（20 个文件，+73/-4）、tasks.md、验证命令输出

## 摘要记分卡

| 维度 | 结果 |
| --- | --- |
| 完整性（Completeness） | 11/11 任务完成；2 个 capability（guest-access ADDED、user-auth MODIFIED）均有实现 |
| 正确性（Correctness） | delta spec 全部 Requirement / Scenario 有实现证据；构建通过 |
| 一致性（Coherence） | 实现与 change design.md 决策一致；无矛盾 |

## 完整性

1. tasks.md 11/11 任务勾选 `[x]`，无未完成项。
2. `openspec validate guest-access-open-pages` 输出：`Change 'guest-access-open-pages' is valid`。
3. 改动文件与 tasks.md 一致（`git diff --stat` 20 文件，全部落在任务描述范围内，无越界改动）。

## 正确性

### Requirement 实现映射

| Requirement | 证据 |
| --- | --- |
| guest-access / 游客可浏览公开内容 | `br-app/src/utils/request.js` 移除 refresh 失败时的 `uni.reLaunch` 全局跳登录；首页 `index/index.vue` 对通知/关注接口按 `isLoggedIn()` 跳过；自习室详情 `booking/detail.vue`、课程详情 `training/course-detail.vue`、老师主页 `teacher/profile.vue` 关注状态加载按登录态跳过 |
| guest-access / 必须登录的操作主动引导登录 | 新增 `br-app/src/utils/auth.js`（`isLoggedIn` / `ensureLogin`）；订单、充值、钱包、优惠券、学习记录、通知、收藏、预约确认、选座（非浏览模式）、课程预约、评价提交、设置等 16 个页面/操作点接入守卫；关注按钮（自习室/课程/老师）点击时 `ensureLogin()` |
| guest-access / 登录成功后返回来源页面 | 复用登录页既有 `goAfterLogin()`（navigateBack 优先、否则回首页），登录页未改动 |
| user-auth / MODIFIED Deleted account authentication guard | token 刷新失败不再强制全局重定向，仅清除 token 并抛错；`request.js` 中已无任何跳登录页代码（grep 验证 0 命中） |

### Scenario 覆盖

- 游客浏览首页/详情页公开内容：构建通过 + 代码路径审查（无 401 自动跳登录路径）。
- 游客点击关注/预约等需登录操作：`ensureLogin()` toast + 跳登录页，各操作点逐一核对。
- 游客以浏览模式进入选座页：`seat-select.vue` 仅在非浏览模式执行 `ensureLogin()`。
- Token 刷新失败：`rejectPendingRequests` + 抛错，无 reLaunch。

### 构建与安全

- 构建命令：`npm run build:mp-weixin`（br-app/，exit 0），证据已通过 `comet check run guest-access-open-pages build --local -- npm run build:mp-weixin` 记录。
- verify 阶段在同一目录（br-app/）重新执行 `npm run build:mp-weixin`：exit 0，通过。
- 安全检查：无硬编码密钥、无新增不安全操作；token 处理沿用既有工具函数。

## 一致性

- 实现遵循 design.md 决策：请求层单点移除全局跳转 + `ensureLogin` 工具 + 页面级守卫，未引入全局路由拦截器，符合最小改动原则。
- 复用既有模式：登录返回逻辑复用 `goAfterLogin()`；页面守卫采用项目既有 options API / script setup 混合风格，与现有代码一致。
- bug-fixed.md 相关陷阱核查：BUG-14（`onMounted` 从 'vue' 导入，`study-record/index.vue` 核查正确）、BUG-2/BUG-4（token 刷新与用户信息加载逻辑未改动，无回归）、BUG-20（模板无新增裸 `<` `>` 字符）。
- 无 Superpowers Design Doc（tweak 预设跳过），design.md 一致性检查通过，无 delta spec 与 design doc 漂移问题。

## 问题清单

- CRITICAL：无
- WARNING：无
- SUGGESTION：无

## 最终评估

全部检查通过，无 CRITICAL / IMPORTANT / WARNING 问题。验证结论：**PASS**，可进入归档前最终确认。
