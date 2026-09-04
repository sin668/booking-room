---
comet_change: booking-order-lifecycle-refactor
role: technical-design
canonical_spec: openspec
archived-with: 2026-09-04-booking-order-lifecycle-refactor
status: final
---

# 订单生命周期重构技术设计

## 1. 定位与边界

本文是 `openspec/changes/booking-order-lifecycle-refactor/design.md`（高层方案框架）的**深度技术细化**，不重写 proposal/spec。需求与能力范围以 OpenSpec 产物为上游事实源；验收场景以 `specs/*/spec.md` delta 为准。

设计阶段实测证据存档于 `.comet/handoff/brainstorm-summary.md`（F1–F20），本文引用其编号而不重复展开。

**本文明确推翻或修正 open 阶段的 5 处结论**，见 §12。

## 2. 领域层设计：`br-server/app/domain/booking_status.py`

### 2.1 词表定义

`app/domain/` 已存在且 4 个模块活跃（F3），本次只新增文件，不新建分层。沿用既有 `(str, Enum)` 形态（与 `models/booking.py`、`domain/booking_rules.py` 一致；不引入 `StrEnum` 造成第三种形态）。

```python
class BookingStatus(str, Enum):
    """订单状态词表 —— 全仓唯一权威定义处。"""
    PENDING_CONFIRM = "pending_confirm"   # 待确认（1V1 定制下单后等管理员确认）
    PENDING_START = "pending_start"       # 待开始（已确认但尚未到开课日期/时段开始时间）
    IN_PROGRESS = "in_progress"           # 进行中（已到开课日期/时段已开始）
    COMPLETED = "completed"               # 已完成
    CANCELLED = "cancelled"               # 已取消


class PaymentStatus(str, Enum):
    """支付状态词表 —— 与 BookingStatus 严格分域，pending 语义为「待支付」。"""
    PENDING = "pending"
    PAID = "paid"
    FAILED = "failed"


class PaymentMethod(str, Enum):
    BALANCE = "balance"
    WECHAT = "wechat"
```

**重命名映射**（BREAKING）：

| 旧值 | 新值 | 长度 |
|---|---|---|
| `pending` | `pending_start` | 13 < `String(20)` |
| `confirmed` | `in_progress` | 11 < `String(20)` |
| `pending_confirm` | 不变 | — |
| `completed` | 不变 | — |
| `cancelled` | 不变 | — |

`models/booking.py:32` 的 `default="confirmed"` 必须同步改为 `default=BookingStatus.PENDING_START`（座位下单默认走判定函数，该 default 仅作为兜底；实测 `create_booking` 与 `create_course_booking` 都显式赋 `initial_status`，default 不生效，但仍需保持词表一致以免误导）。

### 2.2 枚举双份定义收敛（Q9）

现状：`models/booking.py:11-19` 的 `PaymentMethod`/`PaymentStatus` 与 `schemas/booking.py:10-18` 的 `PaymentMethodEnum`/`PaymentStatusEnum` 是**完全相同的两份定义**。

收敛方式：**单一事实源 + re-export**，保留既有导入路径不断链。

```python
# app/domain/booking_status.py —— 唯一定义处
class PaymentStatus(str, Enum): ...

# app/models/booking.py —— 改为 re-export
from app.domain.booking_status import PaymentMethod, PaymentStatus  # noqa: F401

# app/schemas/booking.py —— 保留旧名作为别名，导入路径不断链
from app.domain.booking_status import PaymentMethod as PaymentMethodEnum  # noqa: F401
from app.domain.booking_status import PaymentStatus as PaymentStatusEnum  # noqa: F401
```

依赖方向校验：`domain` 不得 import `models` / `schemas` / `services`（现状 `domain/booking_rules.py` 已满足，只依赖标准库）。

### 2.3 时区契约（强制前置，F19 / F21）

**订单生命周期链路内实测存在 3 个同语义、不同名的「当前业务本地时间」函数**（本文初稿记为「3 个同名 `booking_now`」，已纠正：只有 2 个同名）：

| 定义 | 签名 | 返回 | 时区来源 | 调用方 |
|---|---|---|---|---|
| `booking_cancellation_policy.py:25` | `booking_now(timezone: str = DEFAULT_BOOKING_TIMEZONE)` | **naive** | 参数（可配置） | 自身 `:36` 无参；`booking_service.py:49` import + **6 处**传 `settings.BOOKING_TIMEZONE`（`:102,140,172,645,688,1164`） |
| `course_booking_service.py:49-51` | **`_now_naive()`**（不叫 `booking_now`） | **naive** | 硬编码 `CHINA_TIMEZONE` | 该模块内 **3 处**（`:520,633,670`） |
| `booking_verification_service.py:449` | `_booking_now()` | **aware** | `settings.BOOKING_TIMEZONE` | 该模块内 **2 处**（`:201,260`） |

**订单链路外另有 3 个**（按 Non-Goals 只改导入源、不改返回语义）：`coupon_service.py:45-50`（`_now()` 返 aware + `_now_for_db()` 返 naive）、`activity_service.py:153-154`（`_now()` 返 naive）、`seed_data.py:29`（`_china_now_naive()`，调用点 `:340,419`）。

**第 7 类重复 —— 模块级 `CHINA_TIMEZONE` 常量 6 处重复定义 + 1 处等价变体**：`wallet_service:119`、`course_booking_service:26`、`coupon_service:42`、`admin_coupon_service:13`、`activity_service:25` 均为 `CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")`；`seed_data.py:26` 用 `timezone(timedelta(hours=8))` 这一**等价但不同写法**的变体。而 `config.py:35 BOOKING_TIMEZONE: str = "Asia/Shanghai"` 早已是唯一配置源。

全仓 `replace(tzinfo=None)` 共 **12 处**（`wallet_service:123,572`、`course_booking_service:51`、`booking_cancellation_policy:26`、`booking_payment_service:273`、`coupon_service:50`、`seed_data:31`、`admin_coupon_service:17,33`、`activity_service:154,162`）→ **naive 是压倒性主流，`booking_verification_service` 是唯一 aware 孤岛**，且它已有 `_ensure_booking_timezone()` 归一化工具（`:453-457`，已在 `:366,390` 使用）。

领域纯函数若被两类调用点共用，会直接抛 `TypeError: can't compare offset-naive and offset-aware datetimes`。

**契约**：

- 所有领域函数的 `now` / `today` / `current_time` 参数一律为 **naive 的 `settings.BOOKING_TIMEZONE` 本地时间**。
- 时区转换只在服务层入口做一次，领域层不做 `tzinfo` 处理。
- 模块 docstring 显式声明该契约，delta spec 同步记录（`booking-status-domain` 第 3 条 Requirement）。

**订单链路内 3 个实现收敛为一个（Q11）**：新建 `app/utils/timezone.py`，采用被调用最多的 `booking_cancellation_policy.py:25` 的带参签名（6 处调用）：

```python
# app/utils/timezone.py
CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")   # 单一事实源，6 处重复定义改为 re-export


def booking_now(timezone: str | None = None) -> datetime:
    """返回 naive 的业务本地时间（默认 settings.BOOKING_TIMEZONE = Asia/Shanghai）。"""
    return datetime.now(ZoneInfo(timezone or settings.BOOKING_TIMEZONE)).replace(tzinfo=None)


def ensure_booking_timezone(value: datetime) -> datetime:
    """aware 归一化工具，从 booking_verification_service:453 提升。"""
```

订单链路内 3 个旧定义均改为 import；链路外 3 个函数与 5 处链路外 `CHINA_TIMEZONE` 常量按 Non-Goals 只将常量改为从 `utils/timezone.py` 导入，**不改其返回语义**（避免范围膨胀）。`booking_verification_service` 作为 aware 孤岛，**内部 aware 比较与 `_ensure_booking_timezone` 用法保持不变**，仅在调用领域函数时用 `.replace(tzinfo=None)` 降级一次（Q11 选项：孤岛只在边界降级）。

> 落位修正：本文初稿曾计划把 `booking_now()` 放进 `app/utils/time_slots.py`，并注明「若发现第三个时区工具再拆」。实测已发现链路内第 3 个同语义实现（F21），故直接新建 `app/utils/timezone.py`，`time_slots.py` 只承载 time_slots 数据契约（§3.1）。

### 2.4 领域纯函数清单

全部为无副作用纯函数，不依赖 `AsyncSession`，可脱离数据库单测。按职责分置两个既有/新建领域模块。

#### 2.4.1 `app/domain/booking_status.py`（新建，8 个）

| 函数 | 签名 | 收敛的重复点 |
|---|---|---|
| `resolve_seat_status` | `(*, now: datetime, booking_date: date, start_time: time) -> BookingStatus` | `booking_service.py:286-288`、`:762-764`、`booking_payment_service.py:293-299` |
| `resolve_course_status` | `(*, today: date, first_lesson_date: date \| None) -> BookingStatus` | `course_booking_service.py:420-436`、`booking_service.py:1244`、`booking_payment_service.py:288-292` |
| `resolve_seat_transition` | `(*, status, now, booking_date, start_time, end_time) -> SeatTransition` | `order_status_scheduler.py:79-98` |
| `resolve_course_transition` | `(*, status, today, first_lesson_date, last_lesson_date) -> CourseTransition` | `order_status_scheduler.py:164-177` |
| `is_cancellable` | `(*, status, payment_status) -> bool` | `booking_service.py:654` 内联判定（改调 `booking_rules.can_cancel_paid_booking` 的前置部分） |
| `is_unpaid_cancellable` | `(*, status, payment_status) -> bool` | `booking_service.py:644` |
| `is_payable` | `(*, status, payment_status) -> bool` | `booking_service.py:744` |
| `is_full_refund_cancellation` | `(*, booking_type, status) -> bool` | `booking_service.py:1158-1161` 的 `is_course_pending_start` |

另需一个筛选条件构造器（非纯函数，接收 SQLAlchemy 列）：

```python
def build_status_filter_conditions(status_column, payment_status_column, status: str | None) -> list:
    """按 Q5 决策保持现行派生口径，行为零变更。"""
```

转移结果用轻量 dataclass 承载，避免用 tuple 索引造成调用点不可读：

```python
@dataclass(frozen=True, slots=True)
class SeatTransition:
    new_status: BookingStatus | None   # None 表示不变
    stat_key: str | None               # "seat_started" / "seat_completed" / None
```

#### 2.4.2 `app/domain/verification_rules.py`（既有模块，新增 2 个，Q12）

核销是订单生命周期的终点环节，其状态判定同样重复 4 处（§4 #7）。`verification_rules.py` 已承载 token 签发/解码且覆盖率 100%，**复用该既有领域模块，不新建文件**；`booking_status.py` 只管词表。

| 函数 | 签名 | 收敛的重复点 |
|---|---|---|
| `is_verifiable` | `(*, status, payment_status) -> bool` | `booking_verification_service.py:189-192`（`can_verify`）、`:255-258`（拒绝判定）、`:275-281`（条件 UPDATE）、`:353-356`（第二处查询） |
| `resolve_verification_status` | `(*, now: datetime, end_at: datetime) -> BookingStatus` | `booking_verification_service.py:264` `new_status = "confirmed" if now <= end_at else "completed"` |

`is_verifiable` 的真实语义（实测，**不是**「仅 `in_progress` 可核销」）：

```python
def is_verifiable(*, status: BookingStatus, payment_status: PaymentStatus) -> bool:
    if status == BookingStatus.IN_PROGRESS:
        return True
    return status == BookingStatus.PENDING_START and payment_status == PaymentStatus.PAID
```

`:267` 的幂等保护（`status == "confirmed" and new_status == "confirmed"` → 抛「预约已核销」）保留原语义：「窗口内已核销」是隐式幂等标记，重构后为 `IN_PROGRESS` + 窗口内。

### 2.5 边界语义（实测已隐式一致，故为等价替换）

第 2 段设计逐处实测确认，6 个判定点的边界语义**已经一致**，抽取是等价替换而非行为变更：

| 判定 | 边界 | 出处 |
|---|---|---|
| 课程下单/确认/支付 | `first_lesson_date <= today` → `IN_PROGRESS`；`> today` → `PENDING_START` | `booking_payment_service.py:291`、`booking_service.py:1244`、`course_booking_service.py:433` |
| 课程定时推进 | `today > last_lesson_date` → `COMPLETED` | `order_status_scheduler.py:171` |
| 座位下单/支付 | `now < booking_start` → `PENDING_START`；`now >= booking_start` → `IN_PROGRESS` | `booking_service.py:288`、`:764`、`booking_payment_service.py:298` |
| 座位定时推进 | `now >= booking_start` → `IN_PROGRESS`；`now >= booking_end` → `COMPLETED` | `order_status_scheduler.py:87,92` |
| `None` 兜底 | 4 处全部落 `IN_PROGRESS`（`confirmed`） | `booking_payment_service.py:290,299`、`course_booking_service.py:436` |

**`None` 兜底必须原样保留为 `IN_PROGRESS`**，不得"顺手改成更安全的 `PENDING_START`"——那是行为变更，会改变定时任务与支付回调的落库结果。

### 2.6 筛选口径（Q5：行为零变更）

C 端 `list_bookings` 的派生口径保持现状，仅把字面量换成枚举：

| 查询参数 | 展开条件 |
|---|---|
| `?status=pending_start` | `status IN (PENDING_START, PENDING_CONFIRM) AND payment_status = PAID` |
| `?status=in_progress` | `status = IN_PROGRESS AND payment_status = PAID`，课程订单附加 `CourseSchedule.start_date <= today` 二次过滤，座位订单不过滤 |
| 其它值 | `status = <值>` 纯列匹配 |

**跨端同名参数语义不一致**（F11，既有缺陷，按 Q5 保持）：管理端 `admin_list_bookings`（`booking_service.py:843-858`）是纯列匹配 `Booking.status == status`，不支持派生口径。重命名后 `?status=pending_start` 在 C 端与管理端语义不同。此不一致必须在 delta spec 与 `docs/booking-rules.md` 显式记录为**已知行为**，不得统一。

### 2.7 推翻 D2：不新增 `display_status`

open 阶段 D2 主张「后端新增 `display_status` 只读派生字段」。逐条推导 br-app `orders/index.vue:444-470` 的 `displayStatus()`：

| 派生分支 | 重命名后 |
|---|---|
| `status === 'pending_confirm'` → `'pending_confirm'` | 恒等 |
| `status === 'pending' && payment_status === 'paid'` → `'pending_start'` | `status` 本身已是 `'pending_start'`，恒等 |
| `status === 'confirmed' && booking_type === 'course'` → `'in_progress'` | `status` 本身已是 `'in_progress'`，恒等 |
| `status === 'confirmed' && 座位 && now >= bookingStart` → `'in_progress'` | 后端只在 `now >= bookingStart` 时才置 `IN_PROGRESS`（§2.5），恒等 |

四个分支全部退化为恒等映射 → `display_status ≡ status`。新增该字段是**为恒等函数增加 API 表面积**，违反 YAGNI。

**改为**：删除前端 `displayStatus()`，`statusLabel()` 去掉 `confirmed → '进行中'` 特例，直接消费 `status`。

> 该分支的 `payment_status === 'paid'` 条件在重命名后失效需注意：旧 `pending` 同时表示「待支付」与「待开始」，靠 `payment_status` 区分；新词表下 `pending_start` 只表示「待开始」，未支付订单仍是 `pending_start` 但 `payment_status='pending'`。前端若需区分「待支付」应改用 `payment_status`，而非 `status`。br-app `constants/booking.js` 的 `BOOKING_STATUS_LABELS` 把 `pending` 标为「待支付」正是这一混淆的产物，见 §9.2。

## 3. `time_slots` 公用方法设计

### 3.1 br-server：新建 `app/utils/time_slots.py`

`app/utils/` 不存在（F4），本次新建包（含 `__init__.py`）。

**范围严格限定为订单生命周期链路**（防止范围膨胀）：

| 函数 | 收敛的重复点 |
|---|---|
| `parse_time_slots(raw: str \| None) -> list[TimeSlot]` | `booking_service.py:1277-1289` 的 `json.loads` + 容错 |
| `build_time_slots_from_date(*, booking_date: date, time_slot: str) -> str` | `course_booking_service.py:479-486`（连带消除 `:481` 函数内 `import json`） |
| `rebuild_from_time_range(*, booking_date: date \| None, start_time, end_time) -> str` | `booking_service.py:1270-1291` 的重建分支 |

`TimeSlot` 为 frozen dataclass：`weekday: int`（1-7）、`start: str`、`end: str`。

时区工具**不在本模块**，落位 `app/utils/timezone.py`（§2.3）。`app/utils/` 下本次共新建 3 个文件：`__init__.py`、`timezone.py`、`time_slots.py`。

**明确不迁移**（Non-Goals 硬边界）：

- `admin_course_service._find_next_slot_after`（`:740-820`）：实测为私有方法、只被 `:625` 排课延期调用，不在订单链路上。
- `admin_teacher_service` / `training_service` / `schemas/admin_course.py` 的 `time_slots` 处理：属老师排课域。

### 3.2 数据契约层 vs 展示文案层（修正 D3，F15）

open 阶段 D3 写「三端共享同一格式契约」，措辞掩盖了关键区分。实测三端：

| 端 | 职责 | 输出 |
|---|---|---|
| br-server | **不产生展示文案**，只构造/解析/重建 JSON | JSON 字符串 |
| br-admin `builders.ts:25,40-67` | `WEEKDAY_NAMES` **0-based**（`weekday-1` 索引），`formatTimeSlots` 兼容 3 种历史格式 | `周三 10:00-12:00、周六 12:00-14:00`（顿号分隔，含完整时段） |
| br-app `formatters.js:75,77-92,100-133` | `COURSE_WEEKDAY_NAMES` **1-based 首位空串**（`[weekday]` 直接索引），`normalizeScheduleSlot` + `formatCourseSchedule` | `每周三 14:00，周四 15:00上课`（只取 start，含「工作日 14:00上课」5 天同时段合并特例） |

两个前端的数组索引约定与输出文案**都不同**。文案差异是产品设计差异（管理端要完整时段核对，C 端要口语化），统一它等于改变 UI 文案，属行为变更。

**因此 D3 拆为两层**：

- **数据契约层（必须统一，写进 delta spec 与 `docs/booking-rules.md`）**：标准格式 `[{"weekday": int 1-7, "time_slot": "HH:MM-HH:MM"}]`；另兼容两种历史格式 `["HH:MM-HH:MM"]`（纯字符串数组，缺省周几）与 `{"weekday": N, "start": "HH:MM", "end": "HH:MM"}`（拆分）；解析失败静默容错返回空/null，由调用方回退展示。
- **展示文案层（保持各自现状，不统一）**：br-admin 保留 `builders.ts:formatTimeSlots`（已是该端单一实现，无需再抽），br-app 扩展既有 `utils/formatters.js`。

## 4. 状态判定重复点收敛映射

### 4.1 后端 7 处

**7 处**重复点（open 阶段估计 4-5 处，本文初稿列 6 处，实测补齐第 7 处）：

| # | 位置 | 现状 | 收敛为 |
|---|---|---|---|
| 1 | `booking_service.py:284-290` | 座位下单 `initial_status` 双分支 | `resolve_seat_status()` |
| 2 | `booking_service.py:762-765` | 余额支付待支付订单 | `resolve_seat_status()` |
| 3 | `booking_service.py:1230-1244` | `admin_confirm_booking` 定制订单确认 | `resolve_course_status()` |
| 4 | `booking_payment_service.py:275-299` | `_determine_course_booking_status`（**open 阶段 design.md 误写为 `_resolve_status_after_payment`**） | `resolve_course_status()` + `resolve_seat_status()` 分派 |
| 5 | `course_booking_service.py:420-436` | 固定班课下单三分支 | `resolve_course_status()`；`custom` 分支保留 `PENDING_CONFIRM` |
| 6 | `order_status_scheduler.py:79-98` / `:164-177` | 座位分钟级、课程天级推进 | `resolve_seat_transition()` / `resolve_course_transition()` |
| 7 | `booking_verification_service.py:189-192,255-258,264,275-281,353-356` | 核销可核销复合判定 4 处 + 窗口内/外状态判定 1 处 | `is_verifiable()` + `resolve_verification_status()`（落 `domain/verification_rules.py`，§2.4.2） |

第 7 处另贡献**第 4 个双 `pending` 同现点**（`:191`、`:256`、`:278`、`:355`），使双 `pending` 同现点总数从 3 处增至 **7 处**。

另：`booking_service.py:654` 的内联 `if booking.status not in ("confirmed", "pending")` 与 `domain/booking_rules.py:40` `can_cancel_paid_booking` 的同款判定并存 → 改为复用 `is_cancellable()`，消除两份同判定。

`booking_service.py:1158-1161` 的 `is_course_pending_start` → `is_full_refund_cancellation()`。该判定与 br-admin `views/booking/list/index.vue:72,139` 是**同一规则的前后端两份实现**；语言不同无法共享代码，语义契约写入 delta spec 并在 `docs/booking-rules.md` 对照记录。

### 4.2 前端 4 份（本文初稿未列，实测补齐，F26）

| # | 位置 | 现状 | 收敛为 |
|---|---|---|---|
| 8 | `br-app/pages/orders/index.vue:444-459` `displayStatus()` | 4 个分支，逐分支核验**返回值全部等于 `order.status`**（恒等） | **删除**，模板直接引用 `order.status` |
| 9 | `br-app/pages/orders/index.vue:331-333` `isOrderStarted()` | `status === 'in_progress' \|\| (status === 'confirmed' && started === true)` | `order.status === 'in_progress'` |
| 10 | `br-app/pages/orders/index.vue:335-338` `isOrderPendingStart()` | 3 个分支混用 `confirmed`/`pending`/`pending_confirm` + `payment_status` | 对 `order.status` 的直接判定 |
| 11 | `br-app/pages/verify-booking/index.vue:150-164` `statusText` | 内联与后端 `:264` **相同的时间窗口判定** | 复用领域 `resolve_verification_status()` 语义 |

第 8 项是§2.7「不新增 `display_status`」的直接依据：既然重命名后 `displayStatus(order) ≡ order.status`，后端再新增一个与之恒等的只读字段就是纯冗余。

第 9 项的 `status === 'in_progress'` 分支在重命名前**永不成立**（后端不返回该值），`started === true` 仅对课程订单有值 —— 该函数实际只对课程订单生效，座位订单恒返回 `false`。

## 5. 定时任务重构

### 5.1 三个 job 职责分离保持不变

`app/main.py:194-216` 实测注册三个 job：

| job | 触发 | 实际职责 |
|---|---|---|
| `_cleanup_unpaid_bookings_job` | interval `BOOKING_CLEANUP_INTERVAL_SECONDS` | **微信支付对账**（`reconcile_pending_payments`），命名误导 |
| `_order_status_check_job` | interval，`id=order_status_check` | 订单状态推进 |
| `_schedule_status_check_job` | cron Asia/Shanghai，`id=schedule_status_check` | 排课状态推进 |

不合并：支付对账是 IO 密集 + 外部依赖，状态推进是纯本地比较，失败模式与频率不同，合并会放大故障面。`docs/booking-rules.md` 已记录职责分离为既有架构决策。

### 5.2 `course_started` 计数修正（Q6）

现状缺陷（F5）：`_update_highlight`（`:187-211`）的 `elif is_new_start: stats["course_started"] += 1` **永不可达**——`highlighted_lesson_id` 创建时从不赋值故为 `None`，`is_new_start=True` 时 `None != target_lesson.lesson_id` 必为真，必进 `if` 分支。

消费方实测存在（F9）：`main.py:113-114,121-122` 的 `_order_status_check_job` 读取它参与 `total_changes` 求和并写入日志格式串「课程: 开始 %d / 高亮更新 %d / 完成 %d」（受 `SCHEDULER_LOG_ENABLED` 控制）。

**修正方式**：把计数职责从 `_update_highlight` 移出，由 `_process_course_booking` 在 `PENDING_START → IN_PROGRESS` 转移成功时显式自增。`main.py` 的日志格式串**不动**。

```python
transition = resolve_course_transition(
    status=booking.status, today=today,
    first_lesson_date=first_lesson_date,
    last_lesson_date=last_lesson_date,
)
if transition.new_status is not None:
    booking.status = transition.new_status
    stats[transition.stat_key] += 1        # course_started / course_completed
if transition.new_status == BookingStatus.IN_PROGRESS or transition.highlight_only:
    _update_highlight(booking, lessons, today, stats)   # 只管高亮，不再管 started
```

座位侧同构：

```python
transition = resolve_seat_transition(
    status=booking.status, now=now, booking_date=booking.date,
    start_time=booking.start_time, end_time=booking.end_time,
)
if transition.new_status is not None:
    booking.status = transition.new_status
    stats[transition.stat_key] += 1        # seat_started / seat_completed
```

`stats` 的 6 个键名（`total_scanned` / `seat_started` / `seat_completed` / `course_started` / `course_highlight_updated` / `course_completed`）**保持不变**，否则 `main.py` 日志与既有断言会连带破裂。

### 5.3 注释矛盾：改注释不改实现

`order_status_scheduler.py:168` 注释「高亮当前课时（第一个 `lesson_date >= today` 的课时）」与 `_update_highlight:191` docstring 及实现「最后一个 `lesson_date <= today` 的课时」矛盾。

实现是正确口径（长期记忆亦确认），**改 `:168` 注释对齐实现**，不改实现。

### 5.4 保留课时查询双路径

`order_status_scheduler.py:119-145` 存在两条查询路径：优先 `schedule_id` 精确匹配，旧订单回退 `course_id + lesson_ids + schedule_type`。

这**看着像重复代码但必须保留**：`schedule_id` 是后加字段（迁移 `e5f6a7b8c9d0`），历史订单该列为 `NULL`；且不能按 `course_id` 查 `lesson_schedules` 服务单订单（会命中同课程其它排课的课时）。长期记忆记录过此教训。

### 5.5 时区统一

`order_status_scheduler.py:28-30` 现状：

```python
now = datetime.now(ZoneInfo("Asia/Shanghai"))   # aware
today = now.date()
current_time = now.time()
```

`:79` 又 `now = datetime.combine(today, current_time)` 降级为 naive。重构后统一在入口调用 `booking_now()` 取 naive 本地时间，`:79` 的降级拼装可删除。

## 6. 死代码与误导命名清理（Q4 / Q10）

| # | 对象 | 处置 | 依据 |
|---|---|---|---|
| 1 | `app/application/booking_use_cases.py`（7 行，4 个 `staticmethod` 透传别名） | 删除 | 生产零引用，仅 `tests/test_booking_use_cases.py:1,4` 且只断言 `callable()` |
| 2 | `tests/test_booking_use_cases.py` | 删除 | 随 #1 |
| 3 | `app/application/`（含 `__init__.py`） | 删除空目录 | #1 后无其它文件 |
| 4 | `app/services/booking_cleanup_service.py` | 删除 | 生产零引用，仅 `tests/test_booking_cleanup.py` 4 个测试（覆盖率 100% 但无消费方） |
| 5 | `tests/test_booking_cleanup.py` | 删除 | 随 #4 |
| 6 | `main.py:69` `_cleanup_unpaid_bookings_job` | 重命名 → `_payment_reconciliation_job` | F10：实际调用 `reconcile_pending_payments()`，日志写「[微信支付对账定时任务]」，与名字完全不符 |
| 7 | `_booking_payment_reconciliation_loop` 内调用点 | 同步改名 | 随 #6 |
| 8 | `app.state.booking_cleanup_scheduler` | 重命名 → `app.state.scheduler` | 承载全部 3 个 job，非仅 cleanup |
| 9 | `course_booking_service.py:481` 函数内 `import json` | 提到模块顶部 | 代码异味；随 §3.1 迁移自然消除 |
| 10 | `booking_service.py:654` 内联取消判定 | 改调 `is_cancellable()` | 与 `booking_rules.py:40` 两份同判定 |
| 11 | `br-app/pages/orders/index.vue:267` `const TABS` | 删除 | 零消费方（`:293` 实际用导入的 `BOOKING_TABS`），且使用旧词表 `confirmed`（F24） |
| 12 | `br-app/pages/orders/index.vue:274` `const STATUS_MAP` | 删除 | 零消费方；`STATUS_MAP.pending='待确认'` 与 `BOOKING_STATUS_LABELS.pending='待支付'` **互相矛盾**，随死代码一并消灭（F24） |
| 13 | `br-app/pages/orders/index.vue:281` `const ZONE_MAP` | 删除 | 零消费方（实际用导入的 `SEAT_ZONE_LABELS`）（F24） |
| 14 | `br-app/constants/booking.js` `BOOKING_STATUS_LABELS.confirmed = '已预约'` | 删除 | **死键**：`displayStatus()` 总把 `confirmed` 转为 `in_progress`，从不会流入 `formatBookingStatus()`（F25） |
| 15 | `br-app/constants/booking.js` `BOOKING_STATUS_LABELS.pending = '待支付'` | 删除 + **语义迁移**到 `PAYMENT_STATUS_LABELS` | 支付域语义挂在订单状态词表上（F23）；必须配套 Q13 的 `statusLabel()` 前置分支，否则用户可见文案倒退 |

#11-13 的零消费方结论用 for 循环 grep 逐个实测（各只有定义处 1 次命中），非推测。

**`BOOKING_CLEANUP_INTERVAL_SECONDS` 保留原名**：改名会破坏已部署环境的环境变量兼容性，收益低于风险。仅在 `docs/booking-rules.md` 与 `.env.example` 注明它实际控制的是**支付对账频率**。

删除 #4 是行为决策而非纯清理：该服务实现「15 分钟未支付自动取消 + 恢复优惠券」，删除意味着**明确不引入**该行为。未支付订单的收敛由既有 `reconcile_pending_payments`（微信支付对账）承担。用户在 Q4 已确认「无消费方的一律删除」。

## 7. 管理端会话有效期（需求④）

### 7.1 完整失效链路（F16）

```
admin_auth_service.py:41   exp = now + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES=15)
  → 15 分钟后 verify_access_token 抛 HTTP 401
  → br-admin/src/utils/http/alova/index.ts:104   if (response.status === 401)
  → :25   await userStore.logout()  → storage.remove(ACCESS_TOKEN)
  → router/guards.ts:35   const token = storage.get(ACCESS_TOKEN)  → 读不到
  → 跳转登录页
```

前端**不是瓶颈**：`store/modules/user.ts:69` `const ex = 7 * 24 * 60 * 60` 已存 7 天，`utils/Storage.ts:32,49` 证实 7 天内不丢弃。`admin_auth.py:30` 返回的 `expires_in = 900` **前端根本没读**——这是既有的前后端契约不一致。

`ACCESS_TOKEN_EXPIRE_MINUTES=15` 被 C 端与管理端共用 4 处：`admin_auth.py:30`、`admin_auth_service.py:41`（管理端）、`auth_service.py:45,227`、`jwt_service.py:30`（C 端）。管理端**无 refresh 链路**（`REFRESH_TOKEN_EXPIRE_DAYS` 只被 C 端 `jwt_service.py:48,102` 与 `routes/auth.py:29` 引用）。

### 7.2 方案

| # | 改动 | 位置 |
|---|---|---|
| 1 | 新增 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS: int = 7` | `app/core/config.py` |
| 2 | `exp` 改用 `timedelta(days=config.ADMIN_ACCESS_TOKEN_EXPIRE_DAYS)` | `admin_auth_service.py:41` |
| 3 | `expires_in = settings.ADMIN_ACCESS_TOKEN_EXPIRE_DAYS * 86400` | `api/routes/admin_auth.py:30` |
| 4 | 硬编码 `7 * 24 * 60 * 60` 改为读后端 `result.expires_in`（带兜底） | br-admin `store/modules/user.ts:69`、`:95` |
| 5 | `.env.example` 补新配置项说明 | `br-server/.env.example` |

**取 7 天而非 3 天**：满足用户「至少三天以上」，且与前端现状 `7*24*60*60` 对齐，避免改后端后前端存储时长成为新的隐性上限。管理端无 refresh 链路，不存在 access > refresh 的语义倒挂。

`ADMIN_` 前缀与既有 `ADMIN_TOKEN` / `ADMIN_DEFAULT_USERNAME` / `ADMIN_DEFAULT_PASSWORD` / `ADMIN_DEFAULT_EMAIL` 命名约定一致。

**`ACCESS_TOKEN_EXPIRE_MINUTES=15` 保持不变**，C 端 br-app 与 `jwt_service` 零影响。直接调大它会把 C 端 access token 一并拉长到 7 天，移动端令牌长期有效会放大设备丢失风险，属不可接受的连带影响。

第 4 项是需求②「单一事实源」原则在会话有效期上的应用：有效期由后端单点定义，前端不再持有第二份常量。

## 8. 数据迁移与发布顺序

### 8.1 迁移脚本

当前 head `f6a7b8c9d0e1`（实测 `alembic heads`，共 46 个迁移文件）。新迁移文件名沿用既有 `YYYY_MM_DD_HHMM-<revision>_<slug>.py` 约定。

```python
revision = '<new>'
down_revision = 'f6a7b8c9d0e1'


def upgrade() -> None:
    # 显式限定 status 列，绝不触碰 payment_status（其 pending 语义为「待支付」）
    op.execute("UPDATE bookings SET status='pending_start' WHERE status='pending'")
    op.execute("UPDATE bookings SET status='in_progress'  WHERE status='confirmed'")


def downgrade() -> None:
    op.execute("UPDATE bookings SET status='pending'   WHERE status='pending_start'")
    op.execute("UPDATE bookings SET status='confirmed' WHERE status='in_progress'")
```

- **幂等**：WHERE 只命中旧值，重跑无副作用，可在新旧值混存后重跑收敛。
- **方言中立**：纯 SQL UPDATE 在 PostgreSQL（生产 `postgresql+asyncpg`）与 SQLite（测试 `sqlite+aiosqlite:///:memory:`）均可执行。
- **零 DDL**：`status` 为裸 `String(20)`，无 enum/CHECK 约束，新值最长 13 字符（F7）。

### 8.2 发布顺序：停服优先于迁移（修正 open 阶段 Migration Plan，F17）

open 阶段写「备份 → `alembic upgrade` → 部署后端并杀旧进程」。但 `bug-fixed.md` 记录过真实事故：*「数据还原后约一个调度周期（5 分钟内）订单即被旧进程再次改写为 confirmed」*，而 `ORDER_STATUS_CHECK_INTERVAL_SECONDS` 默认正是 **300 秒**，完全吻合。

若先迁移再停旧进程，旧后端会在迁移后继续按旧词表写入 `pending`/`confirmed`，制造新旧值混存。

**修正后的顺序（不可调换）**：

1. 备份 `bookings`（`id, status, payment_status, booking_type, schedule_id, highlighted_lesson_id` 快照）
2. **停止全部后端进程**，`ps` 核对确认无残留
3. `alembic upgrade head`
4. 启动新后端，**再次 `ps` 核对只有一个进程**
5. 发布 br-admin（`pnpm run build`）、br-app（`npm run build:h5`）
6. 验证：新建座位/课程订单、管理员确认定制订单、等一个调度周期看定时推进、取消退款各走一遍；抽查 `SELECT DISTINCT status FROM bookings` 无旧值残留

### 8.3 回滚

1. 三端 `git revert`；分支 `feature/20260902/booking-order-lifecycle-refactor` 未合并则直接不合并
2. `alembic downgrade -1`：反向 UPDATE
3. 管理端会话有效期是独立配置，改回配置值即可，无数据影响
4. 回滚后运行订单生命周期测试，并用 `alembic downgrade --sql` 离线渲染确认脚本可执行

### 8.4 迁移验证缺口

**测试跑 SQLite 且用 `create_all` 不跑 alembic**（`tests/conftest.py:34`）→ 数据迁移**零自动化覆盖**。

必须人工验证：`alembic upgrade f6a7b8c9d0e1:<new> --sql` 与 `alembic downgrade <new>:f6a7b8c9d0e1 --sql` 离线渲染，核对生成的 SQL 只触及 `status` 列；`alembic heads` 确认单一 head。

## 9. 三端改造清单

### 9.1 br-server

| 位置 | 改动 |
|---|---|
| `app/domain/booking_status.py` | 新建（§2） |
| `app/utils/timezone.py` + `time_slots.py` + `__init__.py` | 新建（§2.3、§3.1） |
| `app/models/booking.py` | 枚举改 re-export；`:32` default 改枚举引用 |
| `app/schemas/booking.py` | 枚举改别名 re-export，保留 `PaymentMethodEnum`/`PaymentStatusEnum` 导入路径 |
| `app/domain/booking_rules.py:40,51` | 硬编码 `("confirmed", "pending")` 与 `== "confirmed"` 改枚举引用 |
| `app/services/booking_service.py` | 6 处判定改调领域函数；`:351-365` 筛选条件改枚举；`:531`、`:1303` 的 `schedule_status` **不动** |
| `app/services/booking_payment_service.py` | `_determine_course_booking_status` 改为分派领域函数；`:160,187-188` 双 pending 改枚举 |
| `app/services/course_booking_service.py` | `:420-436` 改调领域函数；`:479-486` 改用 `build_time_slots_from_date`；`:51` `booking_now` 改 import |
| `app/services/order_status_scheduler.py` | §5 全部改造 |
| `app/services/booking_verification_service.py` | `:189-192,255-258,275-281,353-356` 复合判定改调 `is_verifiable()`；`:264` 改调 `resolve_verification_status()`；`:449` `_booking_now` 改为 import `app/utils/timezone.py`（内部 aware 用法保留，调领域函数时边界降级） |
| `app/domain/verification_rules.py` | 新增 `is_verifiable()`、`resolve_verification_status()`（§2.4.2） |
| `app/services/booking_cancellation_policy.py` | `:25` `booking_now` 改为 re-export `app/utils/timezone.py`（保留导入路径不断链） |
| `app/main.py` | §6 #6/#7/#8 重命名；`:113-122` 日志格式串**不动** |
| `app/api/routes/*` | `status` 查询参数取值与响应 |
| `alembic/versions/` | 新增数据迁移 |
| `app/core/config.py` | 新增 `ADMIN_ACCESS_TOKEN_EXPIRE_DAYS` |

### 9.2 br-app

**实测命中 19 处分布 4 文件，其中订单域 12 处、域外 7 处**（F27）。域外不改：`utils/accountSecurity.js:7`（审核域）、`pages/wallet/transactions.vue:279,290,333`（钱包域）。

另实测：`BOOKING_TABS` **已使用新词表**（`pending_start`/`in_progress` 作为查询参数），与 `BOOKING_STATUS_LABELS` 的旧词表键并存 —— br-app 内部已存在新旧词表混用，本重构是**收敛**而非引入。

| 位置 | 改动 |
|---|---|
| `constants/booking.js` | `BOOKING_STATUS_LABELS` 删除 `pending: '待支付'` 与 `confirmed: '已预约'` 两个旧词表键（后者为**死键**，F25；前者承载支付域语义，F23），保留 `pending_start: '待开始'`、`in_progress: '进行中'`、`pending_confirm: '待确认'`、`completed`、`cancelled`；**新增 `PAYMENT_STATUS_LABELS`** 承载「待支付」语义，消除同键双义 |
| `pages/orders/index.vue:444-459` | 删除 `displayStatus()`（逐分支核验：4 个分支返回值**全部等于 `order.status`**，恒等成立，F26 第 1 项）；模板与按钮判定直接引用 `order.status` |
| `pages/orders/index.vue:461-467` `statusLabel()` | ① 去掉 `ds === 'confirmed' → '进行中'` 特例分支（重命名后为死分支）；② **按 Q13 新增前置分支**：`order.payment_status === 'pending'` → 返回 `PAYMENT_STATUS_LABELS.pending`（「待支付」），保证用户可见文案零变更（F23） |
| `pages/orders/index.vue:209,216,223` | 取消按钮 `v-if` 复合条件中的 `displayStatus(order)` 改用 `order.status`；`:223` 改为 `!(isCourseBooking(order) && order.status === 'pending_start')` |
| `pages/orders/index.vue:331-333` `isOrderStarted()` | 第 2 份派生实现。`order.status === 'in_progress' \|\| (order.status === 'confirmed' && order.started === true)` 收敛为 `order.status === 'in_progress'`；原第一分支在重命名前**永不成立**（后端不返回该值），`order.started` 仅对课程订单有值（座位为 `null`，`schemas/booking.py:100`） |
| `pages/orders/index.vue:335-338` `isOrderPendingStart()` | 第 3 份派生实现。3 个分支混用 `confirmed`/`pending`/`pending_confirm` + `payment_status`，收敛为对 `order.status` 的直接判定，SHALL NOT 保留旧词表字面量比较 |
| `pages/orders/index.vue:267,274,281` | **删除 3 个零消费方死代码常量** `TABS` / `STATUS_MAP` / `ZONE_MAP`（for 循环 grep 实测各只有定义处 1 次命中；页面 `:293` 实际用导入的 `BOOKING_TABS` 与 `SEAT_ZONE_LABELS`）。附带消灭 `STATUS_MAP.pending='待确认'` 与 `BOOKING_STATUS_LABELS.pending='待支付'` 的**互相矛盾文案**（F24，按 Q4） |
| `pages/verify-booking/index.vue:150-164` | 第 4 份派生实现 `statusText`。`:152,153` 的订单域字面量改新词表；其内联的 `now > endDate → '已核销'` 与后端 `booking_verification_service.py:264` 是**同一时间窗口判定**，收敛为复用领域 `resolve_verification_status()` 语义（Q12/F26 第 4 项） |
| `pages/orders/index.vue:1159-1178` | CSS 类 `.dot-pending_start` / `.badge-in_progress` 已存在，核对旧值类名是否需清理 |
| `utils/formatters.js` | `formatBookingStatus()` 保持单一查表入口，只随 `BOOKING_STATUS_LABELS` 键集变化 |
| `pages/course-booking/*.vue`、`booking/seat-select.vue`、`study-record/index.vue` | 状态字面量替换；`time_slots` 展示文案**保持不变**（§3.2） |

`:223` 的改动需验证与既有规范等价：长期记忆「课程待开始订单取消入口端差异」记录*仅管理端可取消课程待开始订单*，且「待确认订单的 UI 展示与取消交互规范」记录*取消按钮不依赖后端 `can_cancel`，显式用 `order.status === 'pending_confirm'`*。实测 `:223` 已是 `(order.can_cancel === true || order.status === 'pending_confirm')` 形态，与该规范一致；`displayStatus(order) === 'pending_start'` 在重命名后等价于 `order.status === 'pending_start'`（因 `displayStatus` 对 `pending_confirm` 返回 `pending_confirm`，不会返回 `pending_start`）。

> **Q13 与本文初稿的差异**：初稿仅写「新增 `PAYMENT_STATUS_LABELS` 消除同键双义」，未识别到删除 `pending` 键会造成**未支付订单标签从「待支付」退化为「待开始」**的用户可见语义倒退（F23）。Q13 补上 `statusLabel()` 的 `payment_status` 前置分支后，才能同时满足「剥离支付域语义」与 Q5「行为零变更」。delta spec 已在 `study-room-booking-ui` 与 `course-booking-ui` 中落地该场景。

### 9.3 br-admin

**6 处 3 文件**（F14，open 阶段统计的 4 处 2 文件漏掉了 tag 映射）：

| 位置 | 改动 |
|---|---|
| `views/business/shared/options.ts:41` | `{label:'待开始', value:'pending'}` → `value:'pending_start'` |
| `options.ts:42` | `{label:'进行中', value:'confirmed'}` → `value:'in_progress'` |
| `options.ts:55` | `BOOKING_STATUS_TAGS` 键 `pending` → `pending_start` |
| `options.ts:56` | 键 `confirmed` → `in_progress` |
| `views/booking/list/index.vue:72` | `handleCancel` 的 `isCoursePendingStart` 判定 |
| `views/booking/list/index.vue:139` | 取消按钮可见性判定 |
| `store/modules/user.ts:69,95` | 硬编码 7 天改读 `expires_in`（§7.2 #4） |

`options.ts:86` 的 `WALLET_STATUS_TAGS.pending`（label「待处理」）**不在重命名范围**（F18 第 4 类）。

`views/booking/list/builders.ts:formatTimeSlots` 保留现状（§3.2）。

## 10. 跨域同名陷阱与 grep 守卫

**6 类**同名值不得被重命名波及（F18，本文初稿只列 4 类）：

| # | 陷阱 | 位置 | 语义 |
|---|---|---|---|
| 1 | `payment_status = 'pending'` | `booking_service.py:644,744`、`booking_payment_service.py:160,188`、`schemas`、前端按钮判定 | 待支付 |
| 2 | `lesson_schedules.schedule_status = 'in_progress'` | `booking_service.py:531` | 课时进行中（排课域） |
| 3 | `course_schedules.schedule_status = 'in_progress'` | `booking_service.py:1303`、`schedule_status_scheduler.py` | 排课进行中（排课域） |
| 4 | `WALLET_STATUS_TAGS.pending` | `br-admin/options.ts:86` | 钱包交易待处理 |
| 5 | `status === 'pending'` | `br-app/src/utils/accountSecurity.js:7` | 管理员**审核中** |
| 6 | `status` / `pending` | `br-app/src/pages/wallet/transactions.vue:279,290,333` | **钱包交易**域 |

替换完成后必须全绿的守卫：

```bash
# 1. payment_status 词表未被波及
grep -rn 'payment_status' br-server/app --include='*.py' | grep -c 'pending\|paid\|failed'
# 2. schedule_status 的 in_progress 未被改动
grep -rn 'schedule_status.*in_progress' br-server/app --include='*.py'
# 3. WALLET_STATUS_TAGS.pending 未被改动
grep -n 'pending' br-admin/src/views/business/shared/options.ts
# 4. br-server app/ 内不再有裸订单状态字面量（除迁移与枚举定义）
grep -rn '"pending"\|"confirmed"' br-server/app --include='*.py' \
  | grep -v 'alembic\|booking_status.py\|payment_status\|schedule_status'
# 5. br-app 审核域与钱包域未被改动
grep -n "'pending'" br-app/src/utils/accountSecurity.js
grep -n 'pending' br-app/src/pages/wallet/transactions.vue
# 6. br-app 订单页不再存在 4 个已删除标识符（F24/F26）
grep -n 'displayStatus\|const TABS\|STATUS_MAP\|ZONE_MAP' br-app/src/pages/orders/index.vue
# 7. 时区实现已收敛（链路内只剩 utils/timezone.py 一处定义）
grep -rn 'def booking_now\|def _booking_now\|def _now_naive' br-server/app --include='*.py'
```

## 11. 测试策略与验收判据

### 11.1 基线与核心判据

验收基线（实测）：`14 failed / 751 passed / 16 skipped / 81 errors`，覆盖率 73%（9680 stmts / 2581 missed）。

95 项既有红灯经按文件与根因双维度归组，**100% 与订单生命周期无关**（F2）：72 项 `TypeError: 'teacher_id' is an invalid keyword argument for Course`、10 项 `'price'`、8 项 `list_available_coupons_for_booking() takes 2 positional arguments but 6 were given`、3 项 `AssertionError: 缺少列`、2 项 `KeyError`/`IndexError`/`409`。根因是 `Course` 模型历史重构（`teacher_id`/`price`/`schedule` 迁至 `course_schedules`）与优惠券服务签名重构后测试侧未同步。

按 Q1 决策，本 change **不治理**这些红灯。

**核心判据 —— 红名单集合恒等，而非数量不增**：

```bash
pytest tests/ -q --tb=no   # 提取 FAILED/ERROR 的测试 ID 集合
```

重构后集合必须与基线集合**完全相同**（95 项逐项比对，按 11 个文件归组）。只看数量会漏掉「修好一个又弄坏一个」的抵消。

**覆盖率不设门槛**（Q2：用户显式撤回原需求⑤的 >80%）；73% 仅作参考数据记录。

### 11.2 新增测试

| 文件 | 覆盖 |
|---|---|
| `tests/test_booking_status.py` | §2.4 全部 8 个纯函数：每个判定分支、`None` 兜底落 `IN_PROGRESS`、边界运算符（课程 `<= today`、座位 `now >= booking_start`、完成 `today > last_lesson_date`）、`build_status_filter_conditions` 的派生口径含 `pending_confirm` |
| `tests/test_time_slots.py` | §3.1 全部函数：3 种历史格式、解析失败静默容错、`rebuild_from_time_range` 分支、`booking_now()` 为 naive Asia/Shanghai |
| `tests/test_order_status_scheduler*.py` | 新增断言 `course_started` 在 `pending_start → in_progress` 转移时自增（§5.2 缺陷的回归测试）；课时查询双路径（`schedule_id` 命中与回退）各一例 |
| `tests/test_admin_auth*.py` | 管理端令牌 `exp` 与响应 `expires_in` ≥ 3 天；C 端 `ACCESS_TOKEN_EXPIRE_MINUTES` 仍为 15 分钟（配置隔离验证） |
| 既有 24 个测试文件 151 处 | 状态字面量更新至新词表 |
| 删除 | `tests/test_booking_use_cases.py`、`tests/test_booking_cleanup.py`（§6） |

### 11.3 每步验收

§13 的 6 步执行顺序中，每步完成后都跑一次全量 `pytest` 并比对红名单集合。第 2 步「枚举值仍为旧字面量」是关键设计：让**结构重构**与**取值变更**分离，任一步出红都能立刻定位是分层问题还是词表问题。

前端构建：br-admin `pnpm run build`（worktree 中 `node_modules` 缺失，需先 `pnpm install`）、br-app `npm run build:h5`。

## 12. 对 open 阶段 design.md 的修正记录

| 项 | 原表述 | 修正 | 依据 |
|---|---|---|---|
| D1 | 「新增领域层模块（新建 `app/domain/` 目录）」 | `app/domain/` **已存在**且 4 个模块活跃，只是新增文件 | F3 |
| D2 | 「后端新增 `display_status` 只读派生字段」 | **推翻**：重命名后 `display_status ≡ status` 恒等，不新增字段，改为删除前端派生 | §2.7 |
| D3 | 「三端共享同一格式契约」 | 拆为两层：数据契约统一 / 展示文案不统一；排课域不迁移 | F15、§3.2 |
| Migration Plan | 「备份 → 迁移 → 部署后端并杀旧进程」 | **停服优先于迁移** | F17、§8.2 |
| 方法名 | `_resolve_status_after_payment` | 实为 `_determine_course_booking_status`（`booking_payment_service.py:275`） | §4 #4 |
| br-admin 命中数 | 4 处 2 文件 | **6 处 3 文件** | F14、§9.3 |
| 现状「状态判定分散在 4 个服务」 | 4 个服务 | 实测 **7 处判定点**（含 `admin_confirm_booking`、固定班课下单三分支、核销域） | §4 |
| 现状「双 `pending` 同现点」 | 未列举 | 实测 **7 处**（含核销域 4 处） | §4 |
| §2.3 时区契约（本文初稿） | 「`booking_now()` 从 `course_booking_service.py:51` 提升到 `time_slots.py`」 | 实测订单链路内有 **3 个同语义实现**（其中第 2 个叫 `_now_naive`，**不叫** `booking_now`；全仓 5 个定义只有 2 个同名），改为新建 `app/utils/timezone.py` 统一收敛 + `CHINA_TIMEZONE` 常量单一事实源（实测 6 处重复定义 + 1 处等价变体），孤岛只在边界降级（Q11） | F19、F21、§2.3 |
| 核销域范围 | 未纳入判定抽取 | 纳入，复用既有 `domain/verification_rules.py`（Q12） | §2.4.2 |
| Goals「覆盖率 > 80%」 | 列为目标 | 撤回（Q2 用户决策） | §11.1 |
| Risks「按 D6 先治理既有红灯」 | 列为前置 | 撤回，改为红名单集合恒等判据（Q1 用户决策） | §11.1 |

### 12.1 对**主 spec** 错误断言的修正记录（写 delta spec 时实测发现，均修正 spec 而非改实现）

| # | 主 spec 断言 | 实测事实 | 证据 |
|---|---|---|---|
| F | 「余额支付创建预约 → `status='confirmed'`」 | 余额支付也做**时间条件判定**：未来时段 → `pending`（重命名后 `PENDING_START`），已开始时段 → `confirmed`（`IN_PROGRESS`） | `booking_service.py:283-292` |
| G | 「仅 `confirmed` 且 `paid` 可取消」 | 允许 **两个**状态：`status not in ("confirmed", "pending")` 才拒；领域层 `can_cancel_paid_booking` 同语义 | `booking_service.py:654`、`domain/booking_rules.py:32-46` |
| H | 「自动完成在**开始时间点**」、「取消已开始预约 → 状态变 `completed`」 | `should_mark_booking_completed` 用 **`end_time`**（而 `has_booking_started` 用 `start_time`，两个边界不同）；「已开始未结束」窗口内取消被拒时状态**保持 `IN_PROGRESS`** | `domain/booking_rules.py:49-54`、`booking_service.py:665-668` |

另实测到主 spec **未记录**的 2 处实现细节，已写入 `study-room-booking-api` delta spec：

- `_sync_user_booking_completions` 查询限定 `Booking.booking_type != "course"`（`booking_service.py:124-131`）—— 自动完成**仅适用于座位预约**
- `in_progress` 筛选对课程订单做**后置过滤**（`:369-393`，先查全部再按 `CourseSchedule.start_date <= today` 筛选），与 Q5 已记录的派生口径互补

### 12.2 对**本文初稿**的事实纠正（写 delta spec 期间自查发现）

| 项 | 初稿表述 | 纠正后 | 依据 |
|---|---|---|---|
| 时区函数 | 「3 个**同名**不同实现的 `booking_now`」 | 5 个同语义定义，**只有 2 个同名**；订单链路内 3 个（`booking_now` / `_now_naive` / `_booking_now`） | F19 |
| 常量重复 | 未记录 | 模块级 `CHINA_TIMEZONE` **6 处重复定义 + 1 处等价变体**（`seed_data.py:26` 用 `timezone(timedelta(hours=8))`） | F19 |
| Requirement 数 | 「17 条」 | **18 条** MODIFIED（算术纠正）+ 5 条 ADDED = 23 条 | F20 |
| 陷阱类数 | 4 类 | **6 类**（新增审核域 `accountSecurity.js:7`、钱包域 `wallet/transactions.vue`） | F18、F27 |
| 未支付标签 | 仅「新增 `PAYMENT_STATUS_LABELS` 消除同键双义」 | 识别出删键会造成**标签退化**，补 `statusLabel()` 的 `payment_status` 前置分支（Q13） | F23 |
| br-app 派生实现 | 只列 `displayStatus()` | 实测 **4 份**（`displayStatus` / `isOrderStarted` / `isOrderPendingStart` / `verify-booking statusText`） | F26 |
| br-app 死代码 | 未记录 | `orders/index.vue` 内 **3 个零消费方常量** `TABS`/`STATUS_MAP`/`ZONE_MAP`，含互相矛盾文案 | F24 |
| 死键 | 未记录 | `BOOKING_STATUS_LABELS.confirmed='已预约'` **从未被命中** | F25 |

## 13. 执行顺序

| 步 | 内容 | 验收 |
|---|---|---|
| 1 | 死代码清理 + 误导命名重命名（§6）+ `import json` 提顶 | 红名单集合恒等 |
| 2 | 新建 `domain/booking_status.py`（**枚举值仍为旧字面量**）+ `utils/time_slots.py`，服务层改为调用纯函数 | 红名单集合恒等（纯重构，零行为变更） |
| 3 | 修 `course_started` 自增 + `:168` 注释 + 时区 aware/naive 统一 | 红名单集合恒等 + 新增断言通过 |
| 4 | 枚举值切换为新词表 + 三端全部改用枚举/常量 | 红名单集合恒等 + §10 grep 守卫全绿 |
| 5 | alembic 数据迁移 + 管理端会话有效期 + 前端 `expires_in` 读取 | 离线渲染 SQL 核对 + 两端构建通过 |
| 6 | 更新 `docs/booking-rules.md`、`docs/api.md`、`bug-fixed.md` + delta spec 回写 | 文档与实现一致 |

## 14. 边界条件清单

| 边界 | 期望行为 |
|---|---|
| `booking.date` 为 `None`（课程） | `resolve_course_status` 返回 `IN_PROGRESS`（保留现状兜底，不得改为 `PENDING_START`） |
| `booking.date`/`start_time` 为 `None`（座位） | `resolve_seat_status` 返回 `IN_PROGRESS`（同上） |
| `start_time` 为字符串而非 `time` | 沿用 `booking_payment_service.py:294-295` 的 `datetime.strptime(start_t, "%H:%M").time()` 兼容分支 |
| 课程 `first_lesson_date == today` | `IN_PROGRESS`（`<=` 含等号） |
| 课程 `today == last_lesson_date` | **不**完成（完成条件是 `today > last_lesson_date`，严格大于） |
| 座位 `now == booking_start` | `IN_PROGRESS`（`>=` 含等号） |
| 座位 `now == booking_end` | `COMPLETED`（`>=` 含等号） |
| `time_slots` 为 `None`/空串/非法 JSON | `parse_time_slots` 返回空列表，不抛异常 |
| `time_slots` 为纯字符串数组（历史格式） | 解析成功，`weekday` 缺省为 `None` |
| `time_slots` 为 `{weekday, start, end}` 拆分格式 | 解析成功 |
| `status` 查询参数为 `None` | 不加状态筛选条件 |
| 定制订单（`booking_type='custom'`） | `initial_status = PENDING_CONFIRM`，`schedule_id` 留空，不走 `resolve_course_status` |
| 未支付订单（`payment_status='pending'`） | `status` 仍为 `PENDING_START`；前端需区分「待支付」应读 `payment_status`，不读 `status`（§2.7 注）。**按 Q13，`statusLabel()` 必须有 `payment_status === 'pending'` → 「待支付」前置分支**，否则删除 `BOOKING_STATUS_LABELS.pending` 键会造成标签从「待支付」退化为「待开始」（F23） |
| 余额支付创建**未来**时段座位预约 | `status = PENDING_START`（**非** `IN_PROGRESS`）；`booking_service.py:288` 对余额支付同样做时间条件判定（发现 F） |
| 余额支付创建**已开始**时段座位预约 | `status = IN_PROGRESS` |
| 微信支付创建座位预约 | 无条件 `status = PENDING_START`（`:290-292`），不做时间判定 |
| 取消时 `status = PENDING_START` 且 `payment_status = PAID` | **可取消**（`booking_service.py:654` 与 `domain/booking_rules.py:40` 均允许 `confirmed`/`pending` 两个状态，主 spec「仅 confirmed」为错误断言，发现 G） |
| 取消被拒：处于「已开始但**未结束**」窗口 | `status` **保持 `IN_PROGRESS`**（`should_mark_booking_completed` 用 `end_time` 而非 `start_time`，`:665-668`，发现 H） |
| 取消被拒：已过 `end_time` | `_sync_booking_completion` 将 `status` 置为 `COMPLETED` |
| 自动完成扫描遇到课程预约 | **不适用**：`_sync_user_booking_completions` 查询限定 `booking_type != "course"`（`:124-131`） |
| `in_progress` 筛选遇到课程订单 | 做**后置过滤**：先查全部再按 `CourseSchedule.start_date <= today` 筛选（`:369-393`），座位订单不做二次过滤 |
| `order.started` 字段为 `null`（座位订单） | 前端 SHALL NOT 依赖该字段判定状态（`schemas/booking.py:100`，仅课程订单在 `:578-579` 赋值）；`isOrderStarted()` 的 `started === true` 分支对座位永不成立（F26） |
| 管理端令牌 `exp` 跨夏令时/时区 | JWT `exp` 用 UTC（`datetime.now(UTC)`，现状不变），与业务时区 Asia/Shanghai 解耦 |
| 核销时 `now == end_at` | `resolve_verification_status` 返回 `IN_PROGRESS`（`<=` 含等号，保留 `:264` 现状） |
| 核销时 `now > end_at` | 返回 `COMPLETED` |
| 已是 `IN_PROGRESS` 且窗口内重复核销 | 抛「预约已核销」（`:267` 幂等保护，语义原样保留） |
| 核销条件 UPDATE 命中 0 行（并发） | 刷新后 `status == COMPLETED` → 「已核销」；否则 → 「状态不可核销」（`:285-289`） |
| `PENDING_START` 且 `payment_status != PAID` 请求核销 | 拒绝，「暂无可核销预约」/「预约状态不可核销」 |
| `booking_verification_service` 调用领域函数 | 边界处 `.replace(tzinfo=None)` 降级一次；模块内部 aware 比较与 `_ensure_booking_timezone` 用法不变 |

## 15. 遗留事项

1. **长期记忆需更新**：记忆「订单虚拟状态 pending_start 的过滤模式与实现规范」称 `in_progress` = `status='confirmed' AND started=true`（课程）/ `now >= date+end_time`（座位）。实测为 `status='confirmed' AND payment_status='paid'` + 课程附加 `CourseSchedule.start_date <= today`、座位**不做**二次过滤。重构完成后更新该记忆。
2. **记忆「Admin 预约列表时段列格式化规范与兼容性处理」的第 3 种格式描述不精确**：记忆写 `[{start, end}]`（无星期），实测代码兼容的是 `["HH:MM-HH:MM"]` 纯字符串数组与 `{weekday, start, end}` 拆分格式。以实测代码为准。
3. **跨端同名参数语义不一致（F11）为已知遗留缺陷**，本次按 Q5 保持行为零变更，只记录不修复。若后续要统一，需独立 change。
4. **95 项既有红灯（F2）为独立测试债务**，按 Q1 不在本 change 范围，建议另开 change 治理。
