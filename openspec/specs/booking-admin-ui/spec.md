# booking-admin-ui Specification

## Purpose

定义 br-admin 管理端预约订单列表页面的交互行为，包括列表展示、筛选、操作按钮、取消流程与订单详情弹窗。
## Requirements
### Requirement: Booking list page
br-admin SHALL 提供订单列表页面（路由 `/booking/list`），展示所有用户的预约订单。页面包含搜索区域（按状态筛选、按自习室筛选、按日期范围筛选）和数据表格。表格列包含：订单 ID、用户昵称、预约类型、自习室名称、座位编号、预约日期、时段、金额、状态（带颜色标签）、创建时间、操作（查看/确认/取消）。课程预约订单的"时段"列展示 `time_slots` 格式化结果（如"周三 10:00-12:00、周六 12:00-14:00"），自习室订单展示 `start_time~end_time`。

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
- **WHEN** 管理员选择状态筛选为"已确认"
- **THEN** 表格仅显示 `status` 为 "confirmed" 的订单

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
br-admin 列表页 SHALL 使用颜色标签区分订单状态。已确认（confirmed）显示绿色，已取消（cancelled）显示红色。

#### Scenario: Confirmed booking tag
- **WHEN** 订单状态为 "confirmed"
- **THEN** 状态列显示绿色标签，文字为"已确认"

#### Scenario: Cancelled booking tag
- **WHEN** 订单状态为 "cancelled"
- **THEN** 状态列显示红色标签，文字为"已取消"

### Requirement: Booking cancel action
br-admin 列表页 SHALL 仅对**课程预约类型**（`booking_type='course'`）且状态为"待开始"（`pending`/`pending_confirm`）的订单显示"取消"按钮。自习室预约类型订单不显示取消按钮。取消前弹出确认对话框。取消成功后刷新列表。

#### Scenario: Cancel confirmed booking
- **WHEN** 管理员查看课程预约"已确认"（`confirmed`）订单的操作列
- **THEN** 不显示取消按钮（管理端取消仅支持待开始订单）

#### Scenario: Cancel cancelled booking
- **WHEN** 管理员点击"已取消"订单的操作列
- **THEN** 不显示取消按钮

#### Scenario: Cancel pending course booking
- **WHEN** 管理员点击课程预约"待开始"订单的取消按钮并确认
- **THEN** 调用取消接口，订单状态变为"已取消"，全额退款并删除订单专属排课记录，列表刷新，显示成功提示

#### Scenario: Seat booking has no cancel button
- **WHEN** 订单为自习室预约类型（任意状态）
- **THEN** 操作列不显示"取消"按钮

#### Scenario: Cancel confirmation dialog
- **WHEN** 管理员点击取消按钮
- **THEN** 弹出确认对话框，提示取消后将全额退款并删除对应排课与课时记录

### Requirement: Admin navigation menu entry
br-admin SHALL 在侧边栏导航菜单中新增"订单管理"菜单项，图标为文件图标，包含子菜单"订单列表"。

#### Scenario: Menu visibility
- **WHEN** 管理员登录后台
- **THEN** 侧边栏显示"订单管理"菜单项，展开后包含"订单列表"子项

### Requirement: Booking detail modal
br-admin 列表页"查看"操作 SHALL 打开订单详情弹窗，弹窗通过详情接口拉取数据并分类展示订单与关联表信息：订单基本信息（编号、类型、状态、日期、时段、排课类型、时间）、用户信息（昵称、手机号）、自习室与座位信息（自习室订单）、课程与排课信息（课程订单：课程名称、分类、授课老师、开课/结课日期、排课状态）、课时安排列表、价格与支付信息（原价、优惠、实付、优惠券、支付方式、支付状态、支付时间）、取消与退款信息（取消时间、退款金额、退款流水）。

#### Scenario: View seat booking detail
- **WHEN** 管理员点击自习室订单的"查看"按钮
- **THEN** 弹窗展示订单基本信息、用户信息、自习室与座位信息、价格与支付信息；课程相关区块不展示

#### Scenario: View course booking detail
- **WHEN** 管理员点击课程订单的"查看"按钮
- **THEN** 弹窗展示订单基本信息、用户信息、课程与排课信息、课时安排列表、价格与支付信息

#### Scenario: View cancelled booking detail
- **WHEN** 管理员点击已取消且已退款订单的"查看"按钮
- **THEN** 弹窗"取消与退款"区块展示取消时间、退款金额与退款流水信息

