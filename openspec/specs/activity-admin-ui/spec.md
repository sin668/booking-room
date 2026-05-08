## ADDED Requirements

### Requirement: Activity list page
系统 SHALL 在 br-admin 中提供活动管理列表页，路径为 `/activity/list`，展示所有活动数据，支持搜索、筛选和分页。

#### Scenario: Display activity list
- **WHEN** 管理员访问活动管理页面
- **THEN** 页面以表格形式展示活动列表，包含列：标题、描述（截断显示）、封面图（缩略图）、参与人数、排序值、状态（上架/下架标签）、创建时间、操作

#### Scenario: Search by keyword
- **WHEN** 管理员在搜索框输入关键词并点击搜索
- **THEN** 表格仅显示标题或描述中包含关键词的活动

#### Scenario: Filter by status
- **WHEN** 管理员选择状态筛选（全部/已上架/已下架）
- **THEN** 表格仅显示对应状态的活动

#### Scenario: Pagination
- **WHEN** 活动数量超过每页显示数量
- **THEN** 表格底部显示分页器，支持切换页码和调整每页数量

### Requirement: Activity create/edit modal
系统 SHALL 提供活动编辑弹窗（Modal），支持新建和编辑活动，包含表单字段：标题（必填）、描述（可选文本域）、封面图（图片上传组件，调用后端上传接口）、参与人数（可选数字）、排序值（可选数字）、是否上架（开关）。

#### Scenario: Open create modal
- **WHEN** 管理员点击"新建活动"按钮
- **THEN** 弹出编辑弹窗，表单为空，标题为"新建活动"

#### Scenario: Open edit modal
- **WHEN** 管理员点击某活动的"编辑"操作
- **THEN** 弹出编辑弹窗，表单预填充该活动的当前数据，标题为"编辑活动"

#### Scenario: Submit create form
- **WHEN** 管理员填写表单并点击提交
- **THEN** 调用创建 API，成功后关闭弹窗并刷新列表

#### Scenario: Submit edit form
- **WHEN** 管理员修改表单数据并点击提交
- **THEN** 调用更新 API，成功后关闭弹窗并刷新列表

#### Scenario: Form validation
- **WHEN** 管理员未填写标题直接提交
- **THEN** 表单显示"标题不能为空"校验提示，不提交请求

### Requirement: Activity delete confirmation
系统 SHALL 在管理员点击删除按钮时弹出确认对话框，确认后执行删除操作。

#### Scenario: Confirm delete
- **WHEN** 管理员点击"删除"按钮并在确认对话框中点击确认
- **THEN** 调用删除 API，成功后刷新列表

#### Scenario: Cancel delete
- **WHEN** 管理员点击"删除"按钮但在确认对话框中点击取消
- **THEN** 关闭对话框，不执行删除操作

### Requirement: Activity status toggle
系统 SHALL 在活动列表的操作列提供状态切换功能，允许管理员快速上架或下架活动。

#### Scenario: Toggle to active
- **WHEN** 管理员点击已下架活动的"上架"按钮
- **THEN** 调用状态切换 API，成功后该活动状态更新为"已上架"，列表刷新

#### Scenario: Toggle to inactive
- **WHEN** 管理员点击已上架活动的"下架"按钮
- **THEN** 调用状态切换 API，成功后该活动状态更新为"已下架"，列表刷新

### Requirement: Activity admin menu entry
系统 SHALL 在 br-admin 侧边栏菜单中添加"活动管理"菜单项，图标使用日历图标。

#### Scenario: Menu visibility
- **WHEN** 管理员登录 br-admin
- **THEN** 侧边栏显示"活动管理"菜单项，点击后跳转到 `/activity/list`
