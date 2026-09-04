## Why

订单状态词表当前没有单一事实源：`bookings.status` 是裸 `String(20)` 列，无枚举类、无 DB 约束，`"pending"` / `"confirmed"` 字面量散落在 br-server 19 个源文件（74 处）与 24 个测试文件（151 处），以及 br-admin（**6 处 3 文件**）、br-app（19 处 4 文件，其中订单域 12 处）。由此产生三类持续付出代价的问题：

1. **命名与业务语义不符**：`pending` 实际含义是"待开始"、`confirmed` 实际含义是"进行中"，前端不得不额外维护一套"虚拟状态"（`pending_start` / `in_progress`）做映射，`booking_service` 中 `status.in_(["pending", "pending_confirm"])` 这类"真实状态拼虚拟语义"的表达式反复出现。br-app 内部已新旧词表混用：`BOOKING_TABS` 已用 `pending_start`/`in_progress` 作查询参数，而 `BOOKING_STATUS_LABELS` 仍保留旧词表键，且把支付域语义（`pending: '待支付'`）挂在订单状态词表上。
2. **分层与重复代码**：下单 → 支付 → 确认 → 定时推进 → 完成/取消的状态判定逻辑在 `booking_service`、`course_booking_service`、`booking_payment_service`、`order_status_scheduler`、`booking_verification_service` 中各自实现（实测后端 **7 处**判定点、前端 **4 份**派生实现；`time_slots` 解析与"周几 HH:MM-HH:MM"格式化在三端各写一份；"当前业务本地时间"函数全仓 5 个定义、`CHINA_TIMEZONE` 常量 6 处重复），违反项目既定的 Clean Architecture 分层与 DDD 约定。
3. **管理端会话过短**：`admin_auth_service` 直接复用 C 端 `ACCESS_TOKEN_EXPIRE_MINUTES=15`，br-admin 登录 15 分钟即失效需重新登录。

同时，全量测试当前基线为 **14 failed / 751 passed / 16 skipped / 81 errors**（114.44s）。这 95 项红灯经实测归组后 **100% 与订单生命周期无关**（历史模型迁移遗留、RBAC/钱包/优惠券/核销域），按用户决策**不在本 change 范围**；本 change 的验收判据是重构前后**红名单集合恒等**（逐项比对，而非仅数量不增，防止"修好一个又弄坏一个"的抵消）。

## What Changes

- **BREAKING** `bookings.status` 取值全局重命名：`pending` → `pending_start`（待开始）、`confirmed` → `in_progress`（进行中）。`pending_confirm` / `completed` / `cancelled` 保持不变。
- **BREAKING** `payment_status` 的 `pending` **不在重命名范围内**（语义为"待支付"，与订单状态无关），必须在实现中显式区分，避免误改。
- **BREAKING** 对外 API 契约变更：订单创建响应、`GET /api/v1/bookings?status=`、`GET /api/v1/admin/bookings?status=` 的 `status` 取值与筛选参数同步变更；br-admin、br-app 必须与后端同批次发布。
- 新增订单状态词表单一事实源（后端枚举 + 前端常量）。重命名后展示状态与落库状态为**恒等映射**（逐分支核验 br-app `displayStatus()` 的 4 个分支返回值全部等于 `order.status`），因此**不新增 `display_status` 派生字段**，而是删除前端派生实现、直接消费 `status`；C 端 `?status=pending_start` / `?status=in_progress` 的**派生筛选口径保持现行不变**（行为零变更），其中 `pending_start` 仍包含 `pending_confirm` 订单这一既有不一致只记录不修复。
- 按 Clean Architecture 分层重构订单生命周期：状态判定与流转规则下沉为领域层公用方法，服务层与定时任务只做编排；消除 `booking_service` / `course_booking_service` / `booking_payment_service` / `order_status_scheduler` / `booking_verification_service` 间重复的开课日期比较与状态推导逻辑（后端 7 处 + 前端 4 份）。
- 抽取跨端公用方法：`time_slots` JSON 解析（**数据契约层**统一，展示文案层三端各自保留）、订单状态判定与展示文案映射，后端与两个前端各自收敛到单一工具模块；新建 `app/utils/timezone.py` 收敛 5 个"当前业务本地时间"函数中订单链路内的 3 个与 6 处重复的 `CHINA_TIMEZONE` 常量。
- 清理失效无用代码（无消费方的一律删除）：`booking_cleanup_service.cleanup_unpaid_bookings`（命名伪装成已接入定时任务，实际零生产引用）、`application/booking_use_cases.py`（4 个透传别名）、br-app `orders/index.vue` 内 3 个零消费方常量 `TABS`/`STATUS_MAP`/`ZONE_MAP`、`BOOKING_STATUS_LABELS.confirmed` 死键；误导命名 `_cleanup_unpaid_bookings_job` → 支付对账语义名、`app.state.booking_cleanup_scheduler` → `app.state.scheduler`。
- 「待支付」语义从订单状态词表剥离到支付域：`BOOKING_STATUS_LABELS.pending = '待支付'` 删除，新增 `PAYMENT_STATUS_LABELS`，br-app `statusLabel()` 增加 `payment_status === 'pending'` → 「待支付」前置分支，**保证用户可见文案零变更**。
- 管理端会话有效期独立配置：新增管理端专属令牌有效期配置项（≥ 3 天，实际取 7 天），不再复用 C 端 15 分钟值；`admin-auth-api` 响应的 `expires_in` 随之变更；br-admin `store/modules/user.ts` 的硬编码 7 天改读 `expires_in`。
- 生产数据迁移：`bookings` 表既有行按新词表 UPDATE 回填（`status` 无 DB enum/CHECK 约束，新值最长 15 字符 < `String(20)`，属纯数据迁移，无 DDL 风险）。迁移 WHERE 必须显式限定 `status` 列，避免波及同名的 `payment_status`。
- 测试治理：以**红名单集合恒等**为验收判据（不新增失败项，也不治理既有 95 项红灯）；更新 24 个测试文件 151 处状态字面量；补齐订单生命周期单元 + 集成测试（状态派生、流转判定、取消策略、定时推进、时区工具、`time_slots` 解析）。**覆盖率不设门槛**（原 > 80% 指标由用户显式撤回）。
- 更新 `docs/booking-rules.md`，使状态词表、状态流转图、定时任务口径与重构后实现一致。

## Capabilities

### New Capabilities

- `booking-status-domain`: 订单状态词表的单一事实源与领域判定函数——状态枚举取值、领域纯函数（`resolve_seat_status` / `resolve_course_status` / `is_cancellable` / `is_verifiable` 等）、时区工具单一事实源、`payment_status` 与 `status` 的语义边界、与 6 类跨域同名值的分离、跨端筛选语义保持。当前该行为散落在实现与前端常量中、无任何 spec 归属；重命名后展示状态与落库状态**恒等**，`pending_start` 同时是真实状态名与旧虚拟状态名，必须显式定义以免歧义。

### Modified Capabilities

- `booking-admin-api`: 管理端订单列表 `?status=` 筛选取值、取消策略前置状态（`confirmed` → `in_progress`、`pending` → `pending_start`）变更。
- `booking-admin-ui`: 管理端列表状态筛选项、颜色标签映射、取消按钮可见性判据引用的状态取值变更。
- `study-room-booking-api`: 座位预约创建响应的 `status` 值、`GET /bookings?status=` 筛选、用户取消前置状态变更。实测取消前置为 `status IN ('in_progress','pending_start') AND payment_status='paid' AND not has_booking_started`（主 spec 原写"仅 `confirmed` 且已支付"为错误断言）；自动完成判定用 `end_time` 而非 `start_time`（主 spec 原写"开始时间点"为错误断言）。
- `study-room-booking-ui`: 座位订单"待开始 / 进行中"Tab 与状态标签的判定口径变更（原依赖 `confirmed` + 时段开始时间比较，重命名后直接消费 `status`）；"待支付"标签改由 `payment_status` 派生。
- `course-booking-api`: 课程预约初始状态三分支（`pending_confirm` / `pending_start` / `in_progress`）与取消前置状态取值变更。
- `course-booking-ui`: C 端课程订单状态标签与"待开始"展示口径变更；与座位订单共用单一映射表。
- `booking-verification-api`: 核销前置条件由 "`confirmed` booking" 变更为 "`in_progress` booking **或** `pending_start` 且已支付的 booking"（实测两者均可核销，主 spec 原描述不完整）。
- `admin-auth-api`: 登录响应 `expires_in` 由 15 分钟（900 秒）变更为 ≥ 3 天（实际取 7 天），管理端会话有效期独立于 C 端。

## Impact

**影响模块范围**

| 层 | 模块 | 影响 |
|---|---|---|
| br-server 领域/模型 | `app/models/booking.py`、新增 `app/domain/booking_status.py`、既有 `app/domain/booking_rules.py` 与 `verification_rules.py` | `status` 词表单一事实源；新增枚举与领域纯函数 |
| br-server 工具 | 新增 `app/utils/timezone.py`、`app/utils/time_slots.py`（**br-server 当前无 utils 层**） | 时区与 `time_slots` 数据契约单一事实源 |
| br-server 服务 | `booking_service.py`、`course_booking_service.py`、`booking_payment_service.py`、`order_status_scheduler.py`、`schedule_status_scheduler.py`、`booking_cancellation_policy.py`、`booking_verification_service.py`、`study_record_service.py`、`admin_booking_service` | 状态判定下沉、重复逻辑消除、定时任务重构、aware/naive 收敛 |
| br-server 认证 | `app/core/config.py`、`app/services/admin_auth_service.py` | 管理端令牌有效期独立配置（根因：`admin_auth_service.py:41` 复用 `ACCESS_TOKEN_EXPIRE_MINUTES`） |
| br-server API/Schema | `app/api/routes/booking.py`、`admin_booking.py`、`app/schemas/booking.py` | `status` 查询参数与响应取值 |
| br-server 迁移 | `alembic/versions/`（当前 head `f6a7b8c9d0e1`） | 新增数据迁移，回填既有 `bookings.status` |
| br-admin | `src/views/booking/list/`（`index.vue:72,139`、`builders.ts`）、`src/views/business/shared/options.ts:41,42,55,56`、`src/store/modules/user.ts:69,95` | **6 处 3 文件**：状态筛选、标签、取消按钮、会话有效期 |
| br-app | `src/constants/booking.js`、`src/pages/orders/index.vue`、`src/pages/verify-booking/index.vue`、`src/utils/formatters.js` | 19 处 4 文件（订单域 12 处）：删除派生与死代码、Tab 过滤、标签文案、「待支付」改支付域派生 |
| 文档 | `docs/booking-rules.md`、`docs/api.md`、`bug-fixed.md` | 状态词表与流转口径同步 |
| 测试 | br-server `tests/` 24 文件 151 处 + 新增 `test_booking_status.py`/`test_timezone.py`/`test_time_slots.py` | 状态取值更新、领域纯函数与时区工具覆盖；**验收判据为红名单集合恒等**（不治理既有 95 项红灯，覆盖率不设门槛） |

**依赖与发布**：后端、br-admin、br-app 必须同批次发布（**严格同批次硬切，无读侧双接受兼容层**）。发布顺序为「**先停服并彻底杀掉残留旧进程 → 再执行数据迁移 → 再部署后端 → 最后发布两个前端**」。残留旧进程会按旧词表写入状态，导致新旧值混存；因此停服必须**先于**迁移。

**回滚方案**

1. **代码回滚**：本次改动在独立分支 `feature/20260902/booking-order-lifecycle-refactor` 与独立 worktree 中完成，回滚即不合并该分支；已合并则 `git revert` 对应提交，三端同批次回退。
2. **数据回滚**：数据迁移必须成对提供 `downgrade()`，把 `pending_start` → `pending`、`in_progress` → `confirmed` 反向 UPDATE；迁移前备份 `bookings` 表（至少备份 `id, status` 两列快照）。
3. **兼容窗口（已决策不采用）**：经 design 阶段确认采用**严格同批次硬切**，不引入读侧双接受兼容层。若实际发布中无法三端同批次，应先回滚已发布端而非临时加兼容分支（兼容层会遗留新旧词表并存的技术债务，且与"消除失效代码"目标相反）。
4. **管理端会话回滚**：会话有效期为独立配置项，回滚即把配置值改回原值，无数据影响。
5. **回滚验证**：回滚后运行订单生命周期相关测试与 `alembic downgrade` 离线渲染（`--sql`）确认可执行。
