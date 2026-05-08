## Requirements

### Requirement: Seat list page by room
br-admin SHALL 提供座位管理页面（路由 `/room/list/:id/seats`），展示指定自习室的所有座位。页面顶部显示当前自习室名称和基本信息。包含筛选区域（按分区 zone 筛选、按状态 status 筛选）和数据表格。表格列包含：座位编号、分区（带颜色标签）、位置、楼层、每小时价格、状态（带颜色标签）、行列位置、操作（编辑/删除/切换状态）。

#### Scenario: Display seat list
- **WHEN** 管理员从门店列表点击"管理座位"进入 `/room/list/1/seats`
- **THEN** 页面显示该自习室的所有座位，顶部显示自习室名称

#### Scenario: Filter by zone
- **WHEN** 管理员选择分区筛选为"安静区"
- **THEN** 表格仅显示 `zone` 为 "quiet" 的座位

#### Scenario: Filter by status
- **WHEN** 管理员选择状态筛选为"维护中"
- **THEN** 表格仅显示 `status` 为 "maintenance" 的座位

#### Scenario: Back to room list
- **WHEN** 管理员点击返回按钮
- **THEN** 跳转回 `/room/list`

### Requirement: Create single seat form
br-admin SHALL 提供新建座位表单（弹窗 Modal 方式）。表单字段包含：座位编号（必填，如 "A-01"）、分区（下拉选择 quiet/keyboard/vip，必填）、位置（下拉选择 靠窗/中间/独立，可选）、楼层（数字输入，默认 3）、每小时价格（数字输入，必填）、行号（数字输入）、列号（数字输入）。提交成功后关闭弹窗并刷新列表。

#### Scenario: Successful creation
- **WHEN** 管理员填写座位信息并提交
- **THEN** 座位创建成功，弹窗关闭，列表刷新，显示成功提示

#### Scenario: Duplicate seat number
- **WHEN** 管理员输入的座位编号在该房间已存在
- **THEN** 显示错误提示"该房间已存在相同编号的座位"

### Requirement: Bulk generate seats form
br-admin SHALL 提供批量生成座位功能（弹窗 Modal 方式）。表单允许添加多个分区配置，每个配置包含：分区类型（下拉选择）、行数（数字输入）、列数（数字输入）、编号前缀（文本输入，如 "A"）、起始编号（数字输入，默认 1）、每小时价格（数字输入）、楼层（数字输入）。预览区域显示将生成的座位数量。提交成功后关闭弹窗并刷新列表。

#### Scenario: Successful bulk generation
- **WHEN** 管理员配置一个分区（安静区，4行5列，前缀A，价格6元）并提交
- **THEN** 生成 20 个座位，弹窗关闭，列表刷新，显示"成功生成 20 个座位"

#### Scenario: Multiple zones configuration
- **WHEN** 管理员配置 3 个分区（安静区 20 座、键盘区 15 座、VIP区 5 座）
- **THEN** 预览显示"共生成 40 个座位"，提交后生成对应数量

#### Scenario: Bulk generation with conflict
- **WHEN** 管理员提交批量生成，部分座位编号已存在
- **THEN** 显示错误提示，列出冲突编号，无座位被创建

### Requirement: Edit seat form
br-admin SHALL 提供编辑座位表单（弹窗 Modal 方式），复用新建表单组件，预填充现有数据。不允许修改所属房间。

#### Scenario: Successful update
- **WHEN** 管理员修改座位信息并提交
- **THEN** 更新成功，弹窗关闭，列表刷新

### Requirement: Seat status toggle
br-admin 座位列表 SHALL 提供状态切换操作。"可用"座位可切换为"维护中"，"维护中"座位可切换为"可用"。操作需二次确认。

#### Scenario: Set seat to maintenance
- **WHEN** 管理员点击可用座位的"设为维护"按钮并确认
- **THEN** 座位状态变为 maintenance，表格状态标签更新

#### Scenario: Restore seat to available
- **WHEN** 管理员点击维护中座位的"恢复可用"按钮并确认
- **THEN** 座位状态变为 available

### Requirement: Seat delete confirmation
br-admin 座位列表 SHALL 提供删除操作，删除前弹出确认对话框。如果座位存在活跃预约，提示无法删除。

#### Scenario: Successful deletion
- **WHEN** 管理员点击删除并确认，座位无活跃预约
- **THEN** 座位被删除，列表刷新

#### Scenario: Delete seat with active bookings
- **WHEN** 管理员点击删除，座位存在活跃预约
- **THEN** 显示错误提示"该座位存在活跃预约，无法删除"
