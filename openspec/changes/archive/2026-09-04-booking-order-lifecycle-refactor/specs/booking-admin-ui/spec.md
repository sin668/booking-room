## MODIFIED Requirements

### Requirement: Booking list page
br-admin SHALL 提供订单列表页面（路由 `/booking/list`），展示所有用户的预约订单。页面包含搜索区域（按状态筛选、按自习室筛选、按日期范围筛选）和数据表格。表格列包含：订单 ID、用户昵称、预约类型、自习室名称、座位编号、预约日期、时段、金额、状态（带颜色标签）、创建时间、操作（查看/确认/取消）。课程预约订单的"时段"列展示 `time_slots` 格式化结果（如"周三 10:00-12:00、周六 12:00-14:00"），自习室订单展示 `start_time~end_time`。

状态筛选项 SHALL 使用重命名后的词表取值（`pending_confirm`/`pending_start`/`in_progress`/`completed`/`cancelled`）。

`time_slots` 的**数据契约**（JSON 结构与 `weekday` 取值 1-7）SHALL 与后端统一，由 `app/utils/time_slots.py` 保证；**展示文案**属前端职责，br-admin 保持其现有实现（0-based 的 `WEEKDAY_NAMES[weekday - 1]` 查表、顿号「、」连接、兼容三种历史格式），SHALL NOT 为统一文案而改变现有输出。排课域组件（如 `TeacherScheduleModal.vue`）不在本次抽取范围。

#### Scenario: Display booking list with pagination
- **WHEN** 管理员访问 `/booking/list`
- **THEN** 页面显示订单分页列表，每页默认 10 条，按创建时间降序排列，包含所有状态的订单

#### Scenario: Course booking time slot column
- **WHEN** 课程预约订单的 `time_slots` 为 `[{"weekday":3,"time_slot":"10:00-12:00"},{"weekday":6,"time_slot":"12:00-14:00"}]`
- **THEN** "时段"列显示"周三 10:00-12:00、周六 12:00-14:00"

#### Scenario: Seat booking time slot column
- **WHEN** 自习室预约订单开始时间为 09:00、结束时间为 12:00
- **THEN** "时段"列显示"09:00~12:00"

#### Scenario: Filter by status
- **WHEN** 管理员选择状态筛选为"进行中"
- **THEN** 表格仅显示 `status` 为 "in_progress" 的订单
- **AND** 请求参数为 `?status=in_progress`

#### Scenario: Filter by pending-start status
- **WHEN** 管理员选择状态筛选为"待开始"
- **THEN** 表格仅显示 `status` 字面为 "pending_start" 的订单
- **AND** 管理端为纯列匹配，SHALL NOT 包含 `pending_confirm` 订单

#### Scenario: Filter by study room
- **WHEN** 管理员选择自习室筛选为"安静自习室"
- **THEN** 表格仅显示该自习室关联的订单

#### Scenario: Filter by date range
- **WHEN** 管理员选择日期范围为 2026-05-01 至 2026-05-07
- **THEN** 表格仅显示预约日期在该范围内的订单

#### Scenario: Combined filters
- **WHEN** 管理员同时设置状态筛选和自习室筛选后点击搜索
- **THEN** 表格仅显示同时满足所有筛选条件的订单

### Requirement: Booking status display
br-admin 列表页 SHALL 使用颜色标签区分订单状态，标签配置由 `views/business/shared/options.ts` 的 `BOOKING_STATUS_TAGS` 单一常量提供，键名 SHALL 使用重命名后的词表取值。标签映射 SHALL 为：`pending_confirm` →「待确认」warning、`pending_start` →「待开始」default、`in_progress` →「进行中」success（绿色）、`completed` →「已完成」info、`cancelled` →「已取消」error（红色）。

`BOOKING_STATUS_OPTIONS`（筛选下拉项）与 `BOOKING_STATUS_TAGS`（标签配置）SHALL 同步使用新词表，两处共 6 个取值命中点 SHALL 全部修正。

同文件内的 `WALLET_STATUS_TAGS.pending`（label「待处理」）属钱包域，SHALL NOT 被本次重命名触及。

#### Scenario: Confirmed booking tag
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）；旧状态值 `confirmed` 已重命名为 `in_progress`，文案由“已确认”改为“进行中”。
- **WHEN** 订单状态为 "in_progress"
- **THEN** 状态列显示绿色（success）标签，文字为"进行中"

#### Scenario: Pending-start booking tag
- **WHEN** 订单状态为 "pending_start"
- **THEN** 状态列显示 default 类型标签，文字为"待开始"

#### Scenario: Pending-confirm booking tag
- **WHEN** 订单状态为 "pending_confirm"
- **THEN** 状态列显示 warning 类型标签，文字为"待确认"

#### Scenario: Completed booking tag
- **WHEN** 订单状态为 "completed"
- **THEN** 状态列显示 info 类型标签，文字为"已完成"

#### Scenario: Cancelled booking tag
- **WHEN** 订单状态为 "cancelled"
- **THEN** 状态列显示红色（error）标签，文字为"已取消"

#### Scenario: Old status literals no longer resolve to a tag
- **WHEN** 重构完成后检查 `BOOKING_STATUS_TAGS` 与 `BOOKING_STATUS_OPTIONS`
- **THEN** SHALL NOT 存在键名或取值为 `pending`、`confirmed` 的订单状态项
- **AND** `WALLET_STATUS_TAGS.pending` SHALL 保持不变

### Requirement: Booking cancel action
br-admin 列表页 SHALL 仅对**课程预约类型**（`booking_type='course'`）且状态为"待开始"（`pending_start`/`pending_confirm`）的订单显示"取消"按钮。自习室预约类型订单不显示取消按钮。取消前弹出确认对话框。取消成功后刷新列表。

「课程预约且处于待开始」这一判定在 br-admin 中存在**两处**语义相同的内联实现（操作列渲染判定与取消确认文案判定）。重构 SHALL 将其收敛为单一共享判定函数，两处 SHALL NOT 各自维护字面量比较。

#### Scenario: Cancel confirmed booking
> 标题沿用主 spec 原名；旧状态值 `confirmed` 已重命名为 `in_progress`。
- **WHEN** 管理员查看课程预约"进行中"（`in_progress`）订单的操作列
- **THEN** 不显示取消按钮（管理端取消仅支持待开始订单）

#### Scenario: Cancel cancelled booking
- **WHEN** 管理员点击"已取消"订单的操作列
- **THEN** 不显示取消按钮

#### Scenario: Cancel pending course booking
> 标题沿用主 spec 原名；“pending”指旧订单状态值，已重命名为 `pending_start`。
- **WHEN** 管理员点击课程预约"待开始"（`pending_start`）订单的取消按钮并确认
- **THEN** 调用取消接口，订单状态变为"已取消"，全额退款并删除订单专属的定制（custom）排课记录，固定班课（fixed）排课保留，列表刷新，显示成功提示

#### Scenario: Cancel pending-confirm course booking
- **WHEN** 管理员点击课程预约"待确认"（`pending_confirm`）订单的取消按钮并确认
- **THEN** 该订单同样展示取消按钮，取消后全额退款并删除订单专属定制排课

#### Scenario: Seat booking has no cancel button
- **WHEN** 订单为自习室预约类型（任意状态）
- **THEN** 操作列不显示"取消"按钮

#### Scenario: Cancel confirmation dialog
- **WHEN** 管理员点击取消按钮
- **THEN** 弹出确认对话框，提示取消后将全额退款并删除对应排课与课时记录
- **AND** 对话框文案分支 SHALL 由与操作列渲染相同的共享判定函数决定

#### Scenario: Duplicated eligibility check is consolidated
- **WHEN** 重构完成后检索 br-admin 中「课程预约 + 待开始」的判定实现
- **THEN** SHALL 只存在一处共享判定函数
- **AND** 该函数 SHALL 使用新词表取值 `pending_start` / `pending_confirm`
