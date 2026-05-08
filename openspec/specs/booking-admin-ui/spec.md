## ADDED Requirements

### Requirement: Booking list page
br-admin SHALL 提供订单列表页面（路由 `/booking/list`），展示所有用户的预约订单。页面包含搜索区域（按状态筛选、按自习室筛选、按日期范围筛选）和数据表格。表格列包含：订单 ID、用户 ID、自习室名称、座位编号、预约日期、时段、金额、状态（带颜色标签）、创建时间、操作（查看详情/取消）。

#### Scenario: Display booking list with pagination
- **WHEN** 管理员访问 `/booking/list`
- **THEN** 页面显示订单分页列表，每页默认 10 条，按创建时间降序排列，包含所有状态的订单

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
br-admin 列表页 SHALL 提供取消操作，仅对"已确认"状态的订单显示取消按钮。取消前弹出确认对话框。取消成功后刷新列表。

#### Scenario: Cancel confirmed booking
- **WHEN** 管理员点击"已确认"订单的取消按钮并确认
- **THEN** 订单状态变为"已取消"，列表刷新，显示成功提示

#### Scenario: Cancel cancelled booking
- **WHEN** 管理员点击"已取消"订单的操作列
- **THEN** 不显示取消按钮

#### Scenario: Cancel confirmation dialog
- **WHEN** 管理员点击取消按钮
- **THEN** 弹出确认对话框，提示"确定要取消该订单吗？取消后不可恢复"

### Requirement: Admin navigation menu entry
br-admin SHALL 在侧边栏导航菜单中新增"订单管理"菜单项，图标为文件图标，包含子菜单"订单列表"。

#### Scenario: Menu visibility
- **WHEN** 管理员登录后台
- **THEN** 侧边栏显示"订单管理"菜单项，展开后包含"订单列表"子项
