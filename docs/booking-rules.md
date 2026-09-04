# 预约订单规则与流程

> 本文档总结订单从下单到"已完成/已取消"的完整规则、状态流转，以及后端定时任务的职责与状态变更逻辑。
> 依据代码：`br-server/app/services/`（booking_service、course_booking_service、booking_payment_service、order_status_scheduler、schedule_status_scheduler、booking_cancellation_policy）、`br-server/app/main.py`。
> 时区约定：所有日期/时间比较统一使用 **Asia/Shanghai**。
> **状态词表（已翻转，BREAKING）**：DB `status` 真实值由旧 `pending`/`confirmed` 统一为 `pending_start`/`in_progress`，与前端展示态、`?status=` API 查询契约同名。`payment_status`（支付域，含 `pending`=待支付）与 `course_schedules.schedule_status`（排课域，含 `pending_start`/`in_progress`/`completed`）是**跨域同名值，与订单 status 无关，不随本次翻转改变**；其 `pending_start`/`in_progress` 判定与订单域复用同一批公用方法（`resolve_course_status` / `resolve_course_transition`）。

---

## 1. 核心概念

### 1.1 预约类型（booking_type）

| 类型 | 说明 |
|---|---|
| `seat` | 自习室座位预约，按 `date + start_time ~ end_time` 计时 |
| `course` | 培训课程预约，又分 `schedule_type` 两种 |

### 1.2 课程排课类型（schedule_type）

| 类型 | 说明 | 排课记录创建时机 |
|---|---|---|
| `fixed` | 固定班课 | 管理员预先创建 `course_schedules`，下单时订单直接关联现有排课（`booking.schedule_id`） |
| `custom` | 1V1 私人定制 | **下单时不创建排课**；管理员确认订单时才创建订单专属的定制排课与课时记录 |

### 1.3 订单关键字段

| 字段 | 说明 |
|---|---|
| `status` | 真实状态：`pending_start` / `pending_confirm` / `in_progress` / `completed` / `cancelled` |
| `payment_status` | 支付状态：`pending`（待支付） / `paid` / `failed`（支付域，独立于 `status`） |
| `schedule_id` | 订单级排课隔离外键（→ `course_schedules.id`），同课程多订单各关联各的排课 |
| `lesson_ids` | 订单所选课时 ID 列表 |
| `highlighted_lesson_id` | 进行中订单当前高亮的课时（定时任务推进） |
| `date` | 座位预约=预约日期；课程订单（固定/定制）=已预约第一课时日期（即开课日期，定制在管理员确认时回写） |
| `time_slots` | 课程订单上课时段（JSON，如 `[{"weekday": 5, "time_slot": "08:00-10:00"}]`）；固定班课下单时从 `course_schedules.time_slots` 复制，定制在确认时生成；管理端按“周几 HH:MM-HH:MM”格式展示 |

### 1.4 状态语义与判定口径（DB 真实值）

> 词表翻转后，`pending_start`/`in_progress` 由原「前端虚拟展示态（不落库）」升为 **DB 真实 `status` 值**，与 `?status=` API 查询契约同名统一。br-app 已移除 `displayStatus` 适配器，直接展示 `order.status`；未支付的 `pending_start` 订单显示「待支付」，该文案由 `payment_status='pending'` 承载（Q13），而非 `status`。

| `status`（DB 真实值） | 语义 | 判定 / 赋值口径 |
|---|---|---|
| `pending_start` | 待开始 | 已支付但未开始（座位：当前时间 < `date+start_time`；课程：开课日期 > 今天）；**未支付订单亦落此值**，前端据 `payment_status='pending'` 显示「待支付」 |
| `in_progress` | 进行中 | 课程：开课日期 ≤ 今天（后端仅当开课日期到达才置 `in_progress`）；座位：当前时间 ≥ 开始时刻 |
| `pending_confirm` | 待确认 | 1V1 定制下单后待管理员确认 |
| `completed` | 已完成 | 座位：当前时间 ≥ `date+end_time`；课程：今天 > 最后课时日期 |
| `cancelled` | 已取消 | 用户/管理员取消，或支付失败/超时 |

---

## 2. 下单流程与初始状态

### 2.1 自习室座位预约（`create_booking`）

1. 座位冲突检测 → 计价（优惠券抵扣）→ 扣款或发起微信支付。
2. 初始状态：
   - 微信支付：`status='pending_start'` + `payment_status='pending'`（待支付）。
   - 余额支付：`payment_status='paid'`，且
     - 当前时间 < `date+start_time` → `pending_start`（待开始）
     - 当前时间 ≥ `date+start_time` → `in_progress`（进行中）

### 2.2 课程预约（`create_course_booking`）

1. 校验课程/课时/优惠券 → 计价 → 余额检查。
2. 初始状态：
   - **1V1 定制（custom）**：`pending_confirm`（待确认），需管理员确认。
   - **固定班课（fixed）**：开课日期统一取**已预约第一课时日期**（不修改 `course_schedules`/`lesson_schedules` 记录）：`第一课时日期 > 今天` → `pending_start`（待开始）；`第一课时日期 ≤ 今天` → `in_progress`（进行中）。
3. 字段回写：固定班课下单时把第一课时日期写入 `booking.date`，并复制排课的 `time_slots` 到 `booking.time_slots`。
4. 排课关联：固定班课下单时即写入 `booking.schedule_id`；定制订单此时 `schedule_id` 为空。
5. 支付：余额支付立即扣款并写 `wallet_transactions`（type=`consume`）；微信支付创建预支付单，`next_payment_check_at = 1 分钟后`。

### 2.3 支付完成后的状态

- **微信支付回调 / 主动查询成功**：`payment_status='paid'`；课程订单按 `booking.date`（即开课日期）判断：`≤ 今天 → in_progress`，否则 `pending_start`；定制订单保持 `pending_confirm`（开课口径在管理员确认时才生效）；座位订单按预约时段开始时间判断。
- **支付失败（对账确认）**：`status='cancelled'` + `payment_status='failed'`。

### 2.4 管理员确认定制订单（`admin_confirm_booking`）

仅针对 `pending_confirm` 订单：

1. 创建定制专属排课：`course_schedules`（`schedule_type='custom'`）+ `lesson_schedules`（取模循环分配 + 周次偏移算法计算每课时日期），并回写 `booking.schedule_id`。
2. 把**第一课时日期**回写为 `booking.date`（预约日期）与 `course_schedules.start_date`（开课日期）。
3. 比较开课日期与今天（复用公用方法 `resolve_course_status`）：`开课日期 ≤ 今天 → in_progress`，否则 `pending_start`。
4. 该判定结果**同时写入订单 `booking.status` 与定制排课 `course_schedules.schedule_status`**（后者经 `AdminCourseService._compute_schedule_status`，内部同样复用 `resolve_course_status`）——使「排课管理」列表与「预约列表」的待开始/进行中口径完全一致。

---

## 3. 状态流转总览

### 3.1 自习室座位订单

```
下单(微信)          支付成功            到点开始             时段结束
pending_start ────► pending_start ────► in_progress ───────► completed
   │                   │
   │ 支付失败/超时      │ 用户/管理员取消（按阶梯退改政策）
   ▼                   ▼
cancelled          cancelled
```

### 3.2 课程订单 — 固定班课

```
下单: start_date>今天 → pending_start ──(定时任务: today≥开课日)──► in_progress ──(today>最后课时日)──► completed
下单: start_date≤今天 → in_progress
pending_start / in_progress ──(用户取消按政策 / 管理员取消待开始全额退)──► cancelled
```

### 3.3 课程订单 — 1V1 定制

```
下单 → pending_confirm ──(管理员确认)──► pending_start(未开课) 或 in_progress(已开课)，同时创建定制排课
之后与固定班课一致：定时任务推进 → completed
pending_confirm / pending_start ──(取消)──► cancelled（待开始全额退款，删除订单专属 custom 排课）
```

---

## 4. 取消规则

### 4.1 用户取消已确认订单（阶梯退改政策，`booking_cancellation_policy`）

按距开始时间剩余时长计算违约金（`ROUND_HALF_UP`）：

| 剩余时间 | policy | 违约金比例 |
|---|---|---|
| > 48 小时 | `over_48h` | 0%（全额退） |
| 24 ~ 48 小时 | `24h_48h` | 10% |
| 2 ~ 24 小时 | `2h_24h` | 20% |
| ≤ 2 小时 | `within_2h` | 50% |
| 已开始（剩余 ≤ 0） | `started` | 不可取消（100%） |

退款金额 = 实付 − 违约金，退回钱包并写 `booking_refund` 流水，恢复使用的优惠券。

### 4.2 用户取消待开始课程订单（`cancel_course_booking`）

待开始（`pending_start` + 已支付）取消：全额退款、恢复优惠券、写退款流水。

### 4.3 管理员取消（`admin_cancel_booking`）

- `in_progress` 订单：走与用户取消相同的阶梯政策。
- **待开始订单**（`pending_confirm` / 课程 `pending_start`）：已支付时**全额退款不扣手续费**、恢复优惠券、写 `booking_refund` 流水。
- 课程待开始订单的排课清理（`_cleanup_course_booking_schedule`），按序早退：
  1. 排课 `schedule_type='fixed'`（固定班课）→ **一律保留**（课程共享资源，即使无其他订单引用）；
  2. 排课被其他非取消订单共享 → 保留；
  3. 仅 `schedule_type='custom'` 且无共享引用 → 先清空所有关联订单的 `schedule_id`，再删除 `lesson_schedules` 与 `course_schedules`。
- 已取消订单再次取消 → 400 "该预约已取消"。

### 4.4 取消入口的端差异

| 订单形态 | br-admin 预约列表 | br-app 订单页 |
|---|---|---|
| 未支付订单 | — | 显示"去支付/取消" |
| 自习室订单（任意状态） | 不显示取消按钮 | 按后端 `can_cancel` 显示 |
| 课程"待确认"（`pending_confirm`） | 显示（全额退款） | 显示（全额退款） |
| 课程"待开始"（`pending_start` + paid） | 显示（全额退款 + 清理 custom 排课） | **不显示取消按钮** |
| 课程"进行中"（`in_progress`） | 不显示 | 按后端 `can_cancel` 显示 |

---

## 5. 定时任务

系统启动时在 `main.py` lifespan 注册 3 个任务（APScheduler，无 APScheduler 时退化为 asyncio 循环）。

### 5.1 微信支付对账任务

- **频率**：`BOOKING_CLEANUP_INTERVAL_SECONDS` 间隔。
- **逻辑**（`BookingPaymentService.reconcile_pending_payments`）：扫描 `status='pending_start' + payment_status='pending' + payment_provider='wechat'` 且 `next_payment_check_at ≤ now` 的订单，向微信查单：
  - `SUCCESS` → 金额核对一致后 `payment_status='paid'`，课程订单按开课日期定 `pending_start/in_progress`。
  - 失败态或重试次数耗尽 → `status='cancelled' + payment_status='failed'`。
  - 其余 → `payment_check_count +1`，按指数退避顺延 `next_payment_check_at`。
- 备注：代码库中另有 `cleanup_unpaid_bookings`（15 分钟未支付自动取消）服务，**目前仅被测试引用，未接入定时任务**。

### 5.2 订单状态定时任务（`order_status_scheduler`）

- **频率**：`ORDER_STATUS_CHECK_INTERVAL_SECONDS` 间隔。
- **扫描范围**：`payment_status='paid'` 且 `status IN ('pending_start','in_progress')` 的 `seat`/`course` 订单。

**自习室订单**（比较精度：分钟级）：

| 当前状态 | 条件 | 变更为 |
|---|---|---|
| `pending_start` | 当前时间 ≥ `date + start_time` | `in_progress`（进行中） |
| `in_progress` | 当前时间 ≥ `date + end_time` | `completed`（已完成） |

**课程订单**（比较精度：天级）：

课时查询优先按 `booking.schedule_id` 精确匹配；旧订单无 `schedule_id` 时回退按 `course_id + lesson_ids`（并按 `schedule_type` 过滤）。

开课日期口径：定制订单与固定班课一致，统一取第一课时日期 `first_lesson.lesson_date`。

| 当前状态 | 条件 | 变更为 |
|---|---|---|
| `pending_start` | `today ≥ 开课日期` | `in_progress`，并高亮当前课时（最后一个 `lesson_date ≤ today` 的课时；均未开始则高亮第一课时） |
| `in_progress` | `today > 最后课时日期` | `completed`，清空 `highlighted_lesson_id` |
| `in_progress` | 仍在课时周期内 | 仅推进 `highlighted_lesson_id` |

无课时记录的订单跳过不处理。

### 5.3 排课状态定时任务（`schedule_status_scheduler`）

- **频率**：每天一次，`SCHEDULE_STATUS_CHECK_TIME`（默认 00:00，Asia/Shanghai）。
- **扫描范围**：`course_schedules.schedule_status IN ('pending_start','in_progress')` 的排课。
- **逻辑**：复用订单域公用方法 `resolve_course_transition`（与 `order_status_scheduler`、预约确认同源）推进状态——排课 `start_date` 对应「第一课时日期」、`end_date` 对应「结课日期」：

| 当前状态 | 条件 | 变更为 |
|---|---|---|
| `pending_start` | `今天 ≥ start_date`（开课日期） | `in_progress`（进行中） |
| `in_progress` | `今天 > end_date`（结课日期） | `completed`（已完成） |

- 两步推进语义与订单域一致：`pending_start` 且已超结课日期时先转 `in_progress`，下一次扫描再转 `completed`（正常运行时调度器每天扫描，`pending_start` 只在开课当天转 `in_progress`，此时未超结课）。
- **固定班课（`fixed`）恒为 `in_progress`/`completed`**：`_effective_start_date` 对 fixed 返回 `None`，`resolve_course_status(None)` 恒为 `in_progress`，保证 C 端「仅 fixed + in_progress 可预约/展示」不被未开课课程破坏；仅**定制排课（`custom`）**会出现 `pending_start`（历史数据由迁移 `b4e7a1c9d3f6` 回填）。
- 只改排课记录状态，不改订单状态。
- 注意：`schedule_status` 属**排课域**，与订单 `status` 同名但不同义，是跨域同名值，不受订单词表翻转影响。

---

## 6. 已知展示口径

- br-app 订单页状态标签：直接展示 `order.status`（词表统一后已移除 `displayStatus` 适配）；未支付的 `pending_start` 订单显示「待支付」（Q13，由 `payment_status` 承载）；课程订单按 `status` 展示（待开始/待确认/进行中/已完成/已取消）。
- br-admin 预约列表："时段"列——课程订单展示 `time_slots` 格式化（如"周三 10:00-12:00、周六 12:00-14:00"），自习室订单展示 `start_time~end_time`。
- 订单详情（管理端）：聚合用户、课程、老师、排课、课时安排、优惠券、退款流水等关联表信息。
