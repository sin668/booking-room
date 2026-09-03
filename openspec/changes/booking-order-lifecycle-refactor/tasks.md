# Tasks

> 本清单为 open 阶段骨架，已按 design 阶段实测结论同步；build 阶段由 `writing-plans` 细化为可逐步验证的实施计划并补充每项的验证命令。
> 证据引用：F## = `brainstorm-summary.md` 实测事实编号；§# = Design Doc 章节。

## 1. 现状审查与基线（重构前置，不改行为）

- [x] 1.1 绘制订单生命周期现状图：下单 → 支付 → 管理员确认 → 定时推进 → 完成/取消，标注每个状态判定的实现位置（**已完成**：后端 7 处 + 前端 4 份，见 §4.1/§4.2）
- [x] 1.2 审查 `order_status_scheduler` / `schedule_status_scheduler` / `booking_payment_service.reconcile_pending_payments` 三个定时任务的职责边界与重复逻辑（**已完成**：职责分离保持不变，见 §5.1）
- [x] 1.3 清单化重复代码：开课日期比较、`time_slots` 解析与格式化、状态 → 展示文案映射（**已完成**：`time_slots` 拆为数据契约层/展示文案层，见 §3.2；时区重复 5 个函数 + 6 处常量，见 §2.3）
- [x] 1.4 清单化失效无用代码，逐项给出保留/删除结论与依据（**已完成**：15 项清单，见 §6）
- [x] 1.5 记录测试基线：`14 failed / 751 passed / 16 skipped / 81 errors`（114.44s），按 **11 个文件归组** 95 项既有红灯（**已完成**：实测 100% 与订单生命周期无关，见 F2）

## 2. 订单状态词表单一事实源

- [ ] 2.1 新建 `app/domain/booking_status.py`（Q7 方案 A，沿用既有 `PaymentStatus(str, Enum)` 模式），显式区分 `bookings.status` 与 `payment_status`，`payment_status.pending` 不参与重命名
- [ ] 2.2 收敛重复枚举为**单一事实源 + re-export**（Q9）：`models/booking.py` 改为 re-export，`schemas/booking.py` 保留旧名作别名，导入路径不断链
- [ ] 2.3 **不**新增 `display_status` 派生字段（推翻 open 阶段 D2）：重命名后展示状态 ≡ 落库状态，在 §2.7 与 delta spec 中记录依据
- [ ] 2.4 br-admin、br-app 各自收敛状态常量与派生逻辑到单一模块，与后端词表对齐

## 3. 时区与 `time_slots` 公用方法（强制前置）

- [ ] 3.1 新建 `app/utils/timezone.py`（br-server 当前无 utils 层）：唯一 `booking_now(timezone=None)` 返 **naive** 本地时间 + `ensure_booking_timezone()` + `CHINA_TIMEZONE` 常量单一事实源（Q11）
- [ ] 3.2 订单链路内 3 个旧定义（`booking_cancellation_policy.booking_now`、`course_booking_service._now_naive`、`booking_verification_service._booking_now`）改为 import；链路外 3 个函数与 5 处常量只改导入源、不改返回语义
- [ ] 3.3 `booking_verification_service` 的 aware 孤岛**只在其模块边界降级**（`.replace(tzinfo=None)`），内部 aware 比较与 `_ensure_booking_timezone` 用法不变
- [ ] 3.4 新建 `app/utils/time_slots.py`（Q8）承载 3 种历史格式的解析与**数据契约**重建；三端展示文案各自保留（§3.2）
- [ ] 3.5 `course_booking_service.py:481` 函数内 `import json` 提到模块顶部

## 4. 死代码清理与误导命名重命名（Q4 / Q10）

- [ ] 4.1 删除 `app/services/booking_cleanup_service.py` + `tests/test_booking_cleanup.py`（零生产引用；删除即**明确不引入**「15 分钟未支付自动取消」行为）
- [ ] 4.2 删除 `app/application/booking_use_cases.py` + `tests/test_booking_use_cases.py` + 空目录 `app/application/`
- [ ] 4.3 重命名 `main.py:69` `_cleanup_unpaid_bookings_job` → `_payment_reconciliation_job`，同步改 `_booking_payment_reconciliation_loop` 内调用点
- [ ] 4.4 重命名 `app.state.booking_cleanup_scheduler` → `app.state.scheduler`（承载全部 3 个 job）
- [ ] 4.5 `booking_service.py:654` 内联取消判定改调领域 `is_cancellable()`（与 `booking_rules.py:40` 消除两份同判定）
- [ ] 4.6 删除 br-app `pages/orders/index.vue` 内 3 个零消费方常量 `TABS`(`:267`) / `STATUS_MAP`(`:274`) / `ZONE_MAP`(`:281`)（F24）
- [ ] 4.7 删除 br-app `displayStatus()`(`:444-459`) 与 `statusLabel()` 内 `ds === 'confirmed'` 特例分支，模板直接引用 `order.status`（F26）
- [ ] 4.8 收敛 br-app `isOrderStarted()`(`:331-333`) 与 `isOrderPendingStart()`(`:335-338`) 为对 `order.status` 的直接判定
- [ ] 4.9 收敛 br-app `pages/verify-booking/index.vue:150-164` `statusText`，复用领域 `resolve_verification_status()` 语义（Q12）
- [ ] 4.10 `BOOKING_CLEANUP_INTERVAL_SECONDS` **保留原名**（环境变量兼容性），仅在 `docs/booking-rules.md` 与 `.env.example` 注明它实际控制支付对账频率
- [ ] 4.11 确认无悬空引用（构建通过 + grep 无残留标识符）

## 5. 状态全局重命名（BREAKING）

- [ ] 5.1 新增 alembic 数据迁移：`bookings.status` 既有行 `pending` → `pending_start`、`confirmed` → `in_progress`，并提供成对 `downgrade()`；WHERE **显式限定 `status` 列**，不波及 `payment_status`
- [ ] 5.2 后端服务层、API 路由、Schema、定时任务全部改用枚举，替换 74 处字面量（**枚举值切换必须在领域层重构之后**，见 §13 执行顺序）
- [ ] 5.3 br-admin（**6 处 3 文件**：`options.ts:41,42,55,56`、`booking/list/index.vue:72,139`）、br-app（19 处 4 文件，订单域 12 处）状态取值与筛选参数同步更新
- [ ] 5.4 br-app `constants/booking.js`：删除 `BOOKING_STATUS_LABELS` 的 `pending`（支付域语义）与 `confirmed`（死键）两个旧键，**新增 `PAYMENT_STATUS_LABELS`**
- [ ] 5.5 br-app `statusLabel()` 增加 `payment_status === 'pending'` → 「待支付」**前置分支**（Q13），保证用户可见文案零变更
- [ ] 5.6 验证 alembic 单一 head 且 `upgrade`/`downgrade` 离线渲染（`--sql`）均可执行，人工核对生成 SQL 只触及 `status` 列

## 6. Clean Architecture 分层重构与领域纯函数

- [ ] 6.1 在 `domain/booking_status.py` 实现 8 个领域纯函数（§2.4.1），服务层与定时任务只做编排
- [ ] 6.2 在既有 `domain/verification_rules.py` 新增 `is_verifiable()` / `resolve_verification_status()`（Q12），覆盖核销域第 7 处判定点
- [ ] 6.3 消除后端 7 处重复判定（§4.1 映射表逐项）
- [ ] 6.4 修 `course_started` 计数器为正确自增（Q6，保留 `main.py` 日志）
- [ ] 6.5 `:168` 注释矛盾：改注释不改实现（§5.3）
- [ ] 6.6 保留课时查询双路径（§5.4）
- [ ] 6.7 重构后行为等价性验证：**红名单集合恒等**，无行为漂移

## 7. br-admin 登录有效期 ≥ 3 天

- [ ] 7.1 新增管理端专属令牌有效期配置项（≥ 3 天，实际取 7 天），`admin_auth_service.py:41` 不再复用 C 端 `ACCESS_TOKEN_EXPIRE_MINUTES=15`
- [ ] 7.2 br-admin `store/modules/user.ts:69,95` 硬编码 7 天改读响应 `expires_in`
- [ ] 7.3 确认 C 端 br-app 令牌有效期不受影响（配置隔离，仍为 15 分钟）
- [ ] 7.4 更新 `.env.example` 与相关配置说明
- [ ] 7.5 补充测试：管理端令牌 `exp` 与响应 `expires_in` ≥ 3 天；C 端 `ACCESS_TOKEN_EXPIRE_MINUTES` 仍为 15 分钟

## 8. 测试（验收判据：红名单集合恒等）

- [ ] 8.1 更新 24 个测试文件中 151 处状态字面量至新词表
- [ ] 8.2 新增 `tests/test_booking_status.py`：领域纯函数全部分支（含核销域）、`None` 兜底、边界运算符（课程 `<= today`、座位 `now >= booking_start`、核销 `now <= end_at`、完成 `end_time`）、`build_status_filter_conditions` 派生口径含 `pending_confirm`
- [ ] 8.3 新增 `tests/test_timezone.py`：`booking_now()` 返 naive 且为 Asia/Shanghai 本地时间、显式传参生效、`ensure_booking_timezone()` 对 naive/aware 两种输入的归一化
- [ ] 8.4 新增 `tests/test_time_slots.py`：3 种历史格式、解析失败容错、重建分支
- [ ] 8.5 既有 `tests/test_order_status_scheduler*.py` 新增断言：`course_started` 在 `pending_start → in_progress` 转移时自增
- [ ] 8.6 补齐 API 集成测试（下单/支付/确认/取消/列表筛选，覆盖新状态取值契约）
- [ ] 8.7 **验收：全量 `pytest tests/ -q --tb=no` 的 FAILED/ERROR 测试 ID 集合与基线 95 项集合完全相同**（逐项比对，非仅数量不增）
- [ ] 8.8 运行 §10 的 **7 条 grep 守卫**全绿（6 类跨域陷阱 + 4 个已删标识符 + 时区实现收敛）
- [ ] 8.9 前端构建：br-admin `pnpm install && pnpm run build`、br-app `npm run build:h5`

> **已删除的 open 阶段任务**：原 6.1「修复 95 项既有红灯」（Q1 用户决策：不在本 change 范围，建议另开 change）、原 6.5「全量测试通过且覆盖率 > 80%」（Q2 用户显式撤回该指标）。覆盖率基线 73% 仅作参考数据记录，不作验收门槛。

## 9. Spec 与文档同步

- [x] 9.1 创建 9 个 delta spec（**已完成**：5 条 ADDED + 18 条 MODIFIED = 23 条 Requirement、162 个 Scenario、1073 行），修复 open 阶段 `specs/` 目录缺失导致的 `openspec validate` FAIL
- [ ] 9.2 更新 `docs/booking-rules.md`：状态词表、展示状态恒等口径、三张状态流转图、定时任务表格、跨端同名参数语义不一致（F11）与「待开始 Tab 标签错配」（F12）作为**已知行为**显式记录
- [ ] 9.3 更新 `docs/api.md` 中受影响的 `status` 取值与筛选参数
- [ ] 9.4 在 `bug-fixed.md` 记录本次重构过程中发现并修复的问题（含 F28 的 3 处主 spec 错误断言，按用户要求避免重犯同类问题）
- [ ] 9.5 更新已过时的长期记忆：「订单虚拟状态 pending_start 的过滤模式」与「Admin 预约列表时段列格式化规范」（§15 遗留事项 1/2）
