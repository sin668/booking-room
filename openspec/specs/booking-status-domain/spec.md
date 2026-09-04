# booking-status-domain Specification

## Purpose
TBD - created by archiving change booking-order-lifecycle-refactor. Update Purpose after archive.
## Requirements
### Requirement: Booking status vocabulary single source of truth
系统 SHALL 在 `br-server/app/domain/booking_status.py` 定义订单状态词表的唯一权威来源 `BookingStatus(str, Enum)`，取值为 `pending_confirm`（待确认）、`pending_start`（待开始）、`in_progress`（进行中）、`completed`（已完成）、`cancelled`（已取消）。其中 `pending_start` 由旧值 `pending` 重命名而来，`in_progress` 由旧值 `confirmed` 重命名而来。

`PaymentStatus`（`pending`/`paid`/`failed`）与 `PaymentMethod`（`balance`/`wechat`）SHALL 与 `BookingStatus` 严格分域定义。`models/booking.py` 与 `schemas/booking.py` 中原有的重复枚举 SHALL 收敛为对领域层单一事实源的 re-export，保留既有导入路径不断链。

该领域模块 SHALL NOT import `models`、`schemas` 或 `services` 层。

#### Scenario: Renamed status values are the only accepted literals
- **WHEN** 代码或数据中出现订单状态字面量
- **THEN** 合法取值 SHALL 仅为 `BookingStatus` 的五个成员值
- **AND** 旧值 `pending` 与 `confirmed` SHALL NOT 再作为 `bookings.status` 的合法取值出现

#### Scenario: Duplicate enums re-export from domain layer
- **GIVEN** `models/booking.py` 与 `schemas/booking.py` 原先各自定义了订单状态与支付状态枚举
- **WHEN** 重构完成
- **THEN** 两处 SHALL 从 `app.domain.booking_status` re-export，不再持有第二份取值定义
- **AND** 既有 `from app.schemas.booking import ...` 导入路径 SHALL 继续可用

#### Scenario: Domain module has no upward dependency
- **WHEN** 检查 `app/domain/booking_status.py` 的 import 语句
- **THEN** SHALL NOT 出现对 `app.models`、`app.schemas`、`app.services` 的导入

### Requirement: Booking status decision functions
系统 SHALL 将原先散落在服务层与定时任务中的 **7 处**订单状态判定重复实现下沉为领域纯函数，由 `app/domain/booking_status.py` 与既有 `app/domain/verification_rules.py` 承载。判定函数 SHALL 接收 **naive 的业务本地时间**（`app/utils/timezone.py` 的 `booking_now()` 语义，默认时区 `settings.BOOKING_TIMEZONE`），SHALL NOT 在领域层内部读取系统时钟。

核销域的 `is_verifiable(status, payment_status)` 与 `resolve_verification_status(status, now, end_at)` SHALL 落在既有 `app/domain/verification_rules.py`，不在 `booking_status.py` 中重复定义。

#### Scenario: Status transition is computed by domain function
- **GIVEN** 定时任务需要判断一笔订单是否应从 `pending_start` 转为 `in_progress` 或 `completed`
- **WHEN** 执行判定
- **THEN** 判定 SHALL 由领域纯函数完成，服务层与调度层 SHALL NOT 各自内联同一套比较逻辑

#### Scenario: Domain functions accept naive local time
- **WHEN** 调用任一状态判定函数
- **THEN** 传入的时间参数 SHALL 为 naive 的业务本地时间
- **AND** 传入 aware datetime 时 SHALL NOT 产生 `TypeError: can't compare offset-naive and offset-aware datetimes`

#### Scenario: Boundary operators are preserved exactly
- **WHEN** 重构前后以相同输入调用状态判定
- **THEN** 课程订单的 `first_lesson_date <= today`、座位订单的 `now >= booking_start`、核销的 `now <= end_at` 三类边界运算符 SHALL 保持原有闭/开区间语义，行为零变更

#### Scenario: Verification status resolution
- **GIVEN** 一笔可核销订单，其结束时刻为 `date + end_time`
- **WHEN** 当前业务本地时间 `now <= end_at`
- **THEN** `resolve_verification_status` SHALL 返回 `in_progress`
- **AND** 当 `now > end_at` 时 SHALL 返回 `completed`

### Requirement: Booking timezone utility single source of truth
系统 SHALL 在 `br-server/app/utils/timezone.py` 提供唯一的 `booking_now(timezone: str | None = None) -> datetime`，返回 **naive** 的业务本地时间，默认时区取 `settings.BOOKING_TIMEZONE`。订单链路内原有 **3 处同语义但仅 2 处同名**的实现 SHALL 收敛到该函数：`booking_cancellation_policy.booking_now`（naive）、`course_booking_service._now_naive`（naive，**不叫 `booking_now`**）、`booking_verification_service._booking_now`（**aware**）。

模块级 `CHINA_TIMEZONE` 常量 SHALL 收敛到 `app/utils/timezone.py` 作为单一事实源。原有 **6 处重复定义**（`wallet_service`、`course_booking_service`、`coupon_service`、`admin_coupon_service`、`activity_service` 等）与 `seed_data.py` 的 `timezone(timedelta(hours=8))` 等价变体 SHALL 改为引用该单一事实源。

链路外的 3 处同语义函数（`coupon_service._now`/`_now_for_db`、`activity_service._now`、`seed_data._china_now_naive`）SHALL 只改导入源，SHALL NOT 改变其返回语义。

`ensure_booking_timezone(value)` SHALL 承接 aware 归一化。`booking_verification_service` 原有的 aware 时间语义 SHALL 只在该模块边界降级为 naive，SHALL NOT 向领域层外溢 aware datetime。

#### Scenario: booking_now returns naive local time
- **WHEN** 调用 `booking_now()` 不带参数
- **THEN** 返回值 SHALL 为 naive datetime（`tzinfo is None`）
- **AND** 其墙上时间 SHALL 等于 `settings.BOOKING_TIMEZONE`（默认 `Asia/Shanghai`）的当前本地时间

#### Scenario: Explicit timezone argument is honored
- **WHEN** 调用 `booking_now("Asia/Shanghai")`
- **THEN** 返回值 SHALL 与不带参数调用在同一时刻等价
- **AND** 原有 6 处显式传入 `settings.BOOKING_TIMEZONE` 的调用点 SHALL 保持可用

#### Scenario: No duplicate timezone implementations remain
- **WHEN** 重构完成后检索全仓 `def booking_now`、`def _booking_now` 与 `def _now_naive`
- **THEN** 订单链路内 SHALL 只在 `app/utils/timezone.py` 存在一处定义
- **AND** 模块级 `CHINA_TIMEZONE = ZoneInfo("Asia/Shanghai")` SHALL 只在 `app/utils/timezone.py` 存在一处定义

### Requirement: Booking status domain separation from same-named values
系统 SHALL 保持订单状态域与其它业务域的同名字面量严格分离。以下 **6 类**取值与 `BookingStatus` **不等价**，重命名 SHALL NOT 触及：

- `payment_status = 'pending'` 语义为「待支付」，与 `status = 'pending_start'`（待开始）无关
- `lesson_schedules.schedule_status = 'in_progress'` 属排课域
- `course_schedules.schedule_status = 'in_progress'` 属排课域
- `wallet_transactions.status = 'pending'` 属钱包域（br-admin 中对应 `WALLET_STATUS_TAGS.pending`，label 为「待处理」）
- br-app `utils/accountSecurity.js` 的 `status === 'pending'` 语义为「审核中」，属账号安全审核域
- br-app `pages/wallet/transactions.vue` 的 `pending` 判定属钱包交易域

#### Scenario: Payment status pending is untouched
- **WHEN** 订单状态重命名完成
- **THEN** `payment_status` 的取值 SHALL 仍为 `pending`/`paid`/`failed`
- **AND** 数据迁移 SQL 的 WHERE 子句 SHALL 显式限定 `status` 列，SHALL NOT 触及 `payment_status`

#### Scenario: Schedule status in_progress is untouched
- **WHEN** 订单状态重命名完成
- **THEN** `lesson_schedules.schedule_status` 与 `course_schedules.schedule_status` 的 `in_progress` 取值 SHALL 保持不变

#### Scenario: Wallet status pending is untouched
- **WHEN** br-admin 前端状态常量重命名完成
- **THEN** `WALLET_STATUS_TAGS.pending`（label「待处理」）SHALL 保持不变
- **AND** `BOOKING_STATUS_TAGS` 中的 `pending` → `pending_start`、`confirmed` → `in_progress` SHALL 被修正

#### Scenario: br-app non-booking pending values are untouched
- **WHEN** br-app 状态常量与订单页重命名完成
- **THEN** `utils/accountSecurity.js` 的 `status === 'pending'`（审核中）SHALL 保持不变
- **AND** `pages/wallet/transactions.vue` 的 `pending` 判定 SHALL 保持不变
- **AND** 订单域以外的 `pending` 字面量 SHALL NOT 被全局替换波及

#### Scenario: Verifiability depends on both status and payment status
- **GIVEN** 一笔订单 `status = 'pending_start'`
- **WHEN** 判定其是否可核销
- **THEN** 仅当 `payment_status = 'paid'` 时可核销
- **AND** 当 `payment_status = 'pending'`（待支付）时不可核销
- **AND** `status = 'in_progress'` 时无需检查 `payment_status` 即可核销

### Requirement: Booking status filter semantics preserved across ends
C 端与管理端的同名状态筛选参数 SHALL 保持各自现行口径，本次重构 SHALL NOT 顺手统一：

- C 端 `GET /api/v1/bookings/?status=pending_start` 为**派生筛选**：`status IN ('pending_start','pending_confirm') AND payment_status='paid'`
- C 端 `?status=in_progress` 为**派生筛选**：`status='in_progress' AND payment_status='paid'`，课程订单附加 `start_date <= today`，座位订单不做二次过滤
- 管理端 `GET /api/v1/admin/bookings/?status=<value>` 为**纯列匹配**：`status = <value>`

#### Scenario: Client-side pending_start filter is derived
- **WHEN** C 端以 `?status=pending_start` 请求订单列表
- **THEN** 返回结果 SHALL 包含 `status='pending_start'` 与 `status='pending_confirm'` 且均已支付的订单
- **AND** 该口径 SHALL 与重构前完全一致

#### Scenario: Client-side in_progress filter is derived
- **WHEN** C 端以 `?status=in_progress` 请求订单列表
- **THEN** 返回结果 SHALL 为 `status='in_progress' AND payment_status='paid'`
- **AND** 课程订单 SHALL 附加 `start_date <= today` 条件，座位订单 SHALL NOT 做二次过滤

#### Scenario: Admin-side status filter is a plain column match
- **WHEN** 管理端以 `?status=in_progress` 请求订单列表
- **THEN** 返回结果 SHALL 为 `status = 'in_progress'` 的纯列匹配，SHALL NOT 附加 `payment_status` 或日期派生条件

#### Scenario: Cross-end semantic divergence is documented, not unified
- **GIVEN** C 端与管理端对同名 `status` 参数的口径不同
- **WHEN** 本次重构完成
- **THEN** 该差异 SHALL 在 `docs/booking-rules.md` 中显式记录为已知行为
- **AND** SHALL NOT 通过修改任一端的行为来消除差异

#### Scenario: Display status is no longer derived on the client
- **GIVEN** 重命名后展示状态与落库状态为恒等映射
- **WHEN** br-app 渲染订单状态标签
- **THEN** 前端 SHALL 直接消费后端 `status` 字段
- **AND** 原 `displayStatus()` 与 `statusLabel()` 中 `confirmed → 进行中` 的派生特例 SHALL 被删除
- **AND** 后端 SHALL NOT 新增 `display_status` 只读派生字段

#### Scenario: Unpaid label derives from payment status, not booking status
- **GIVEN** `BOOKING_STATUS_LABELS.pending = '待支付'` 把支付域语义挂在订单状态词表上，该键 SHALL 被删除
- **WHEN** br-app 渲染一笔 `payment_status = 'pending'` 的座位订单标签
- **THEN** `statusLabel()` SHALL 以 `payment_status` 派生的**前置分支**返回「待支付」
- **AND** 用户可见文案 SHALL 与重构前完全一致（零变更）
- **AND** 新增的 `PAYMENT_STATUS_LABELS` SHALL 承载该文案，`BOOKING_STATUS_LABELS` SHALL NOT 再保留支付域键
- **AND** 具体 UI 验收场景见 `study-room-booking-ui` delta spec

#### Scenario: Pending-start tab label mismatch is preserved
- **GIVEN** br-app「待开始」Tab 按派生口径会返回 `pending_confirm` 订单
- **WHEN** 该订单渲染状态标签
- **THEN** 标签 SHALL 仍显示「待确认」（现行既有不一致行为）
- **AND** 本次重构 SHALL NOT 改变该行为

