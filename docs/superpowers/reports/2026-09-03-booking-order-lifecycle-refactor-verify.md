# 验证报告：booking-order-lifecycle-refactor

- **Change**：`booking-order-lifecycle-refactor`（订单生命周期重构，BREAKING 状态词表翻转）
- **验证日期**：2026-09-03（Asia/Shanghai）
- **验证模式**：full（规模评估：57 任务 > 3、9 delta spec 能力 > 1、97 变更文件 > 8，三项均超阈值）
- **绑定分支**：`feature/20260902/booking-order-lifecycle-refactor`（isolation=current，worktree）
- **base-ref**：`6582eb0268f658b75bcd2030e959d709a21e712d`
- **结论**：**PASS — 无 CRITICAL / IMPORTANT 问题，1 项 SUGGESTION（非阻塞），可进入归档**

## 摘要记分卡

| 维度 | 状态 |
|---|---|
| Completeness（完整性） | 57/57 任务 `[x]`；PLAN 127/127 步骤 `[x]`；9 delta spec 能力全部有实现证据；`openspec validate` = valid |
| Correctness（正确性） | 核心验收「红名单集合恒等」新鲜复跑 PASS；§10 七守卫全绿；领域纯函数/时区/核销/会话有效期/前端同步逐项对齐 Scenario |
| Coherence（一致性） | 实现符合 design.md D1-D6 与 Design Doc；delta spec ↔ design doc 无行为矛盾（1 项 prose 签名 SUGGESTION） |

## 一、核心验收判据：红名单集合恒等（新鲜复跑）

本重构的定义性验收判据为**重构前后 pytest FAILED/ERROR 测试 ID 集合逐项恒等**（而非数量不增，防止「修好一个又弄坏一个」的抵消）。既有 95/96 项红灯经实测 100% 与订单生命周期无关（§15.4 独立测试债务，Q1 决策不在本 change 范围）。

```
采集命令：pytest tests/ -q --tb=no -p no:cacheprovider
本次结果：14 failed / 802 passed / 16 skipped / 81 errors（79.25s）@ 2026-09-03T18:43:35+0800
比对命令：python compare_redlist.py redlist-baseline redlist-after-verify

基线: 96 项 @ 2026-09-03T09:15:00+08:00（≤11:00 挂钟桶，敏感项红）
候选: 95 项 @ 2026-09-03T18:43:35+08:00（>11:00 挂钟桶，敏感项绿）
PASS 红名单集合恒等（归一化后 95 项）  → exit code 0
```

- 唯一挂钟敏感项 `test_booking_verification_service.py::test_issue_verification_token_for_future_booking_returns_token` 按 `BASELINE.md` 边界规则（≤11:00 红 / >11:00 绿）归一化，`compare_redlist.py` 从两集合扣除后逐项比对，`missing` 与 `added` 均为空。
- `802 passed` 较基线 `750/751` 增加，源于本重构新增的 55 个领域/时区/时段测试（`test_booking_status.py` 41 + `test_timezone.py` 6 + `test_time_slots.py` 8），全部通过。
- 证据文件：`verification/redlist-after-verify.txt`（95 项）、`verification/redlist-after-verify.ts`。

## 二、comet-verify 完整验证 7 项检查

| # | 检查项 | 结果 | 证据 |
|---|---|---|---|
| 1 | tasks.md 全部任务 `[x]` | PASS | 57 `[x]` / 0 `[ ]`；PLAN 127 步骤全 `[x]` |
| 2 | 实现符合 design.md 高层决策 D1-D6 | PASS | 见下「三、设计决策对齐」 |
| 3 | 实现符合 Design Doc（docs/superpowers/specs/） | PASS | §10 七守卫全绿（新鲜复跑，见「四」）；§2.7 无 display_status 已落实 |
| 4 | 能力规格场景全部通过 | PASS | booking-status-domain 5 Requirement 逐 Scenario 核验；admin-auth-api / study-room-booking-ui / booking-admin-ui 关键 Scenario 核验；`openspec validate` = valid |
| 5 | proposal.md 目标已满足 | PASS | 词表单一事实源、7 处判定下沉、time_slots/时区收敛、管理端会话独立、死代码清理、数据迁移、文案零变更均已落实 |
| 6 | delta spec ↔ design doc 无矛盾 | PASS（1 SUGGESTION） | Task 6.2 已核对回写 9 delta spec（提交 3250395）；仅 1 处 prose 签名描述与实现有细微差异，见「六」 |
| 7 | 关联 Design Doc 可定位 | PASS | `docs/superpowers/specs/2026-09-03-booking-order-lifecycle-refactor-design.md`（55988 字节） |

## 三、设计决策对齐（D1-D6，新鲜核验）

- **D1 领域层单一事实源**：`app/domain/booking_status.py` 定义 `BookingStatus(str, Enum)` 五成员（`pending_confirm`/`pending_start`/`in_progress`/`completed`/`cancelled`）+ `PaymentStatus`（`pending`/`paid`/`failed`）严格分域；10 个领域纯函数（`resolve_seat_status`/`resolve_course_status`/`resolve_seat_transition`/`resolve_course_transition`/`is_cancellable`/`is_unpaid_cancellable`/`is_payable`/`is_full_refund_cancellation`/`build_status_filter_conditions`）。领域层无 models/schemas/services 上行依赖（grep = NONE）。`models/booking.py:8`、`schemas/booking.py:8-9` 从领域层 re-export（`# noqa: F401`），旧导入路径不断链。
- **D2（已推翻）不新增 display_status**：全仓生产代码无 `display_status` 字段；br-app `displayStatus()` 已删除（§10 G6 = EMPTY）；模板直接消费 `order.status`。
- **D3 time_slots 两层拆分**：新建 `app/utils/time_slots.py`（数据契约层）；三端展示文案各自保留。
- **D4 定时任务编排/判定分离**：`order_status_scheduler` 状态判定改调领域纯函数；`course_started` 统计与注释矛盾已修（Phase 3）。
- **D5 管理端会话独立配置**：`config.py:32 ADMIN_ACCESS_TOKEN_EXPIRE_DAYS=7`；`config.py:16 ACCESS_TOKEN_EXPIRE_MINUTES=15`（C 端未动）；`admin_auth_service.py:41 exp=now+timedelta(days=ADMIN_ACCESS_TOKEN_EXPIRE_DAYS)`；`admin_auth.py:30 expires_in=ADMIN_ACCESS_TOKEN_EXPIRE_DAYS*86400=604800`；br-admin `user.ts:72 result.expires_in ?? DEFAULT_SESSION_TTL_SECONDS`（读后端单一源 + 防御兜底）。
- **D6 时区收敛 + 执行顺序**：新建 `app/utils/timezone.py`，`booking_now()` 单一 naive 源 + `CHINA_TIMEZONE` 单一源（`:13`，6 处重复已收敛）；`_now_naive` 已删；`booking_verification_service._booking_now`（aware 孤岛）按 Q11 决策在模块边界降级、保留不改造。

## 四、§10 跨域同名陷阱七守卫（新鲜复跑，全绿）

| 守卫 | 命令意图 | 期望 | 实测 | 判定 |
|---|---|---|---|---|
| G1 | payment_status 词表未波及 | >0 | 34 | GREEN |
| G2 | schedule_status='in_progress' 排课域未改 | 有匹配 | 15（7 文件，全排课域） | GREEN |
| G3 | WALLET_STATUS_TAGS.pending 未改 | 有匹配 | 5 | GREEN |
| G4 | br-server 无裸订单状态字面量 | 0 订单域 | 10（**实测全部为 `WalletTransaction.status=="pending"` 钱包/充值域**，零订单状态字面量） | GREEN（意图） |
| G5a | br-app 审核域 accountSecurity.js 'pending' 未改 | 1 | 1 | GREEN |
| G5b | br-app 钱包域 transactions.vue pending 未改 | 6 | 6 | GREEN |
| G6 | br-app 订单页 4 个已删除标识符 | 0 | EMPTY（displayStatus/const TABS/STATUS_MAP/ZONE_MAP 全删） | GREEN |
| G7 | 时区实现收敛 | 单一 naive 源 | 2（`timezone.py:16 booking_now` 单一 naive 源 + `booking_verification_service.py:451 _booking_now` aware 孤岛，Q11 文档化保留；`_now_naive` 已删=收敛 3→2） | GREEN（含文档化例外） |

- **G4 说明**：守卫#4 意图为「br-server app/ 内不再有裸**订单状态**字面量」。实测 10 处命中经逐条核验全部为钱包/充值域 `WalletTransaction.status=="pending"`（`models/wallet.py`、`admin_wallet.py`、`wallet_rules.py`、`wallet_service.py`、`user_security_service.py`），属 6 类跨域同名值合法保留，**订单状态裸字面量命中数为 0**，意图 GREEN。
- **G7 说明**：两处定义均为文档化合法状态——收敛后的单一 naive 源 + Q11 明确保留的核销域 aware 孤岛（只在模块边界降级，不改造其内部 aware 比较）。

## 五、能力规格 Scenario 抽样核验

- **booking-status-domain（新能力）**：5 个 Requirement 逐 Scenario 核验通过——词表单一事实源（5 成员 + 分域 + re-export + 无上行依赖）、判定函数下沉（naive 时间入参 + 边界运算符 `first_lesson_date<=today`/`now>=booking_start`/`now<=end_at` 保持）、时区单一源、6 类跨域分离（G1-G5b）、跨端筛选语义保持（`build_status_filter_conditions`：`in_progress`→`status='in_progress' AND paid`；`pending_start`→`IN('pending_start','pending_confirm') AND paid`；C 端课程附加 `start_date<=today`、座位不二次过滤；管理端纯列匹配）。
- **study-room-booking-ui / Q13**：br-app `isOrderStarted()` 收敛为 `order.status === 'in_progress'`；`isOrderPendingStart()` 3 分支全用新词表（`in_progress`/`pending_start`/`pending_confirm`），无旧字面量，保留「pending_start Tab 含 pending_confirm」既有不一致（只记录不修复）；`statusLabel()` 增 `payment_status==='pending'` → `PAYMENT_STATUS_LABELS.pending`「待支付」前置分支，`BOOKING_STATUS_LABELS` 删除 `pending`/`confirmed` 键，用户可见文案零变更。
- **admin-auth-api**：`expires_in` 由 900 秒（15 分钟）变更为 604800 秒（7 天），管理端会话独立于 C 端；spec line 6 已明确 `expires_in` 为唯一权威源、前端缺失时（如 `/me`）可退防御性默认值（Task 6.2 提交 3250395）。

## 六、问题清单（按优先级）

### CRITICAL（必须修复）
- 无。

### IMPORTANT / WARNING（应修复）
- 无。

### SUGGESTION（可选，非阻塞）
1. **delta spec prose 函数签名与实现的细微差异**：`booking-status-domain/spec.md:28` 的 Requirement prose 将核销函数描述为 `resolve_verification_status(status, now, end_at)`，实际实现为 `resolve_verification_status(*, now, end_at)`（`verification_rules.py:112`，纯时间判定不需要 `status` 参数）。
   - **影响**：无。该 Requirement 的 normative 主张（函数落 `verification_rules.py`、不在 `booking_status.py` 重复定义）已满足；对应 Scenario「Verification status resolution」（`now<=end_at`→`in_progress`，`now>end_at`→`completed`）由实现逐字满足。差异仅在描述性签名多列了一个未使用的 `status`。
   - **建议**：归档后（或另开文档 change）将 spec line 28 的签名描述订正为 `resolve_verification_status(now, end_at)`。按 comet-verify 规则，verify 阶段不修改 delta spec，故仅记录不改动。

## 七、构建与验证证据记录

- **build check**（comet 记录，exit=0）：`cd br-server && python -m pytest tests/test_booking_status.py tests/test_timezone.py tests/test_time_slots.py -q` → 55 passed（新增领域/时区/时段测试全绿）。
- **verify check**（comet 记录，exit=0）：`bash verification/redlist.sh redlist-after-verify && python compare_redlist.py redlist-baseline redlist-after-verify` → PASS 红名单集合恒等（归一化后 95 项）。
- **代码字节恒等**：`git diff cef7066..HEAD` 的 `br-server/app`+`tests`+`alembic`、`br-admin/src`、`br-app/src` 均为 EMPTY（Phase 5 验收后仅文档/状态变更），故 br-admin `pnpm run build`（Task 5.3）、br-app `npm run build:h5`（Task 4.3）的既有构建证据对当前代码仍然有效。
- **alembic 迁移**：`2026_09_03_1706-a33171f2c2fb_rename_booking_status.py`（双向离线渲染核对、单一 head，Task 5.1 提交 1b03133）。

## 八、最终评估

**所有检查通过。无 CRITICAL / IMPORTANT 问题；1 项 SUGGESTION 为 delta spec prose 签名描述细微差异，normative 行为完全满足，非阻塞。红名单集合恒等（核心验收）新鲜复跑 PASS，§10 七守卫全绿，9 delta spec 与实现一致。change 已就绪，可进入归档（archive）阶段。**

> 下一步：`comet guard booking-order-lifecycle-refactor verify --apply` 推进 phase→archive；归档阶段先执行归档前最终确认阻塞点，再合并 delta spec → main spec、标注 Design Doc、精确提交归档改动，最后由 `/comet-archive` 处理分支收尾（finishing-a-development-branch）。
