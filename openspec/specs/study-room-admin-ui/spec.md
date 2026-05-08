## Requirements

### Requirement: Study room list page
br-admin SHALL 提供自习室列表页面（路由 `/room/list`），展示所有自习室。页面包含搜索区域（按名称搜索、按状态筛选）和数据表格。表格列包含：封面缩略图、名称、地址、营业时间、最低价格、状态（带颜色标签）、座位总数、操作（编辑/删除/切换状态/管理座位）。

#### Scenario: Display room list with pagination
- **WHEN** 管理员访问 `/room/list`
- **THEN** 页面显示自习室分页列表，每页默认 10 条，包含所有状态的房间

#### Scenario: Search by name
- **WHEN** 管理员在搜索框输入"安静"并点击搜索
- **THEN** 表格仅显示名称包含"安静"的自习室

#### Scenario: Filter by status
- **WHEN** 管理员选择状态筛选为"营业中"
- **THEN** 表格仅显示 `status` 为 "open" 的自习室

#### Scenario: Navigate to seat management
- **WHEN** 管理员点击某自习室的"管理座位"操作
- **THEN** 跳转到 `/room/list/{room_id}/seats`

### Requirement: Create study room form
br-admin SHALL 提供新建自习室表单（路由 `/room/create`）。表单字段包含：名称（必填）、描述（textarea）、封面图片（图片上传）、地址（必填）、营业时间（时间范围选择器）、最低价格（数字输入，单位元）。提交成功后跳转回列表页。

#### Scenario: Successful creation
- **WHEN** 管理员填写表单并点击提交，所有必填字段已填写
- **THEN** 创建成功，显示成功提示，跳转回 `/room/list`

#### Scenario: Validation error
- **WHEN** 管理员提交表单时缺少必填字段
- **THEN** 表单高亮显示错误字段，不提交

### Requirement: Edit study room form
br-admin SHALL 提供编辑自习室表单（路由 `/room/edit/:id`），复用新建表单组件，预填充现有数据。

#### Scenario: Successful update
- **WHEN** 管理员修改信息并提交
- **THEN** 更新成功，显示成功提示，跳转回 `/room/list`

#### Scenario: Load existing data
- **WHEN** 管理员访问 `/room/edit/1`
- **THEN** 表单预填充该自习室的当前数据

### Requirement: Study room status toggle
br-admin 列表页 SHALL 提供状态切换操作。点击"下架"将营业中房间设为 closed，点击"上架"将已关闭房间设为 open。操作需二次确认。

#### Scenario: Close a room
- **WHEN** 管理员点击营业中房间的"下架"按钮并确认
- **THEN** 房间状态变为 closed，表格状态标签更新，显示成功提示

#### Scenario: Reopen a room
- **WHEN** 管理员点击已关闭房间的"上架"按钮并确认
- **THEN** 房间状态变为 open，表格状态标签更新

### Requirement: Study room delete confirmation
br-admin 列表页 SHALL 提供删除操作，删除前弹出确认对话框，提示"删除后将无法恢复，确定要删除吗？"。如果房间存在活跃预约，提示"该自习室存在活跃预约，无法删除"。

#### Scenario: Successful deletion
- **WHEN** 管理员点击删除并确认，房间无活跃预约
- **THEN** 房间被删除，列表刷新，显示成功提示

#### Scenario: Delete room with active bookings
- **WHEN** 管理员点击删除，房间存在活跃预约
- **THEN** 显示错误提示"该自习室存在活跃预约，无法删除"

### Requirement: Admin navigation menu entry
br-admin SHALL 在侧边栏导航菜单中新增"门店管理"菜单项，图标为商店图标，包含子菜单"门店列表"。

#### Scenario: Menu visibility
- **WHEN** 管理员登录后台
- **THEN** 侧边栏显示"门店管理"菜单项，展开后包含"门店列表"子项
