## Purpose
定义 br-admin 活动管理页面能力，包括活动列表、创建编辑弹窗、富文本正文编辑、关联卡券配置、删除确认、上下架提示和菜单入口，确保运营人员可以安全发布活动和卡券。
## Requirements
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
系统 SHALL 提供活动编辑弹窗（Modal），支持新建和编辑活动，包含表单字段：标题（必填）、描述（可选文本域）、封面图（图片上传组件，调用统一 OSS 图片上传接口）、参与人数（可选数字）、排序值（可选数字）、是否上架（开关）。封面图上传成功后 SHALL 将返回的 OSS URL 写入 `cover_image` 字段并展示预览；上传失败时 SHALL 保持原值并提示失败。

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

#### Scenario: Upload activity cover to OSS
- **GIVEN** 管理员打开活动编辑弹窗
- **WHEN** 管理员通过封面图上传组件选择图片
- **THEN** br-admin 调用共享上传 API 客户端
- **AND** 上传请求使用 `activity-cover` scope，图片大小不得超过 5MB
- **AND** 后端返回 OSS 图片 URL
- **AND** 表单 `cover_image` 更新为该 URL
- **AND** 弹窗展示该 OSS URL 的图片预览

#### Scenario: Activity cover upload failure
- **GIVEN** 管理员打开活动编辑弹窗且已有封面图
- **WHEN** 管理员选择新图片但上传失败
- **THEN** 页面展示上传失败提示
- **AND** 表单 `cover_image` 保持原封面 URL

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

### Requirement: 活动表单富文本正文编辑
br-admin SHALL 在活动创建和编辑表单中提供活动详情富文本编辑能力，用于维护活动规则、图文说明和使用须知。富文本编辑器 SHALL 支持基础排版、图片、链接、列表和强调样式。

#### Scenario: 编辑活动详情富文本
- **GIVEN** 管理员打开活动创建或编辑表单
- **WHEN** 管理员在富文本编辑区域输入图文内容并提交
- **THEN** 页面将富文本正文作为 `content_html` 提交给后端
- **AND** 保存成功后再次打开编辑表单可回显该正文

#### Scenario: 富文本正文为空
- **GIVEN** 管理员创建普通活动
- **WHEN** 管理员未填写富文本正文并提交
- **THEN** 页面允许保存活动
- **AND** 小程序活动详情页不展示空正文区域

### Requirement: 活动表单关联卡券配置
br-admin SHALL 在活动创建和编辑表单中提供关联卡券配置区域，支持添加、删除、启停和排序活动卡券配置，并填写卡券类型、优惠规则、有效期、总库存、每人限领数量、领取时间和展示文案。

#### Scenario: 新增活动卡券配置
- **GIVEN** 管理员打开活动创建或编辑表单
- **WHEN** 管理员点击新增卡券配置
- **THEN** 页面新增一组卡券配置表单项
- **AND** 管理员可以填写卡券规则、库存、限领、有效期和展示文案

#### Scenario: 表单校验必填字段
- **GIVEN** 管理员新增了一组活动卡券配置
- **WHEN** 管理员未填写卡券类型或总库存直接提交
- **THEN** 页面显示字段校验提示
- **AND** 不提交保存请求

### Requirement: 活动列表卡券状态提示
br-admin SHALL 在活动列表中展示活动是否关联卡券，以及关联卡券数量和领取概况。

#### Scenario: 活动存在关联卡券
- **GIVEN** 活动关联了 3 个活动卡券
- **WHEN** 管理员查看活动列表
- **THEN** 该活动行展示卡券数量
- **AND** 展示已领取数量汇总

### Requirement: 发布活动时提示卡券同步发布
br-admin SHALL 在管理员发布包含启用卡券配置的活动时提示“将同步展示关联卡券”。发布失败时 SHALL 展示后端返回的校验原因。

#### Scenario: 发布包含卡券的活动
- **GIVEN** 活动包含启用的活动卡券配置
- **WHEN** 管理员点击上架
- **THEN** 页面展示同步发布关联卡券的确认提示
- **AND** 管理员确认后调用状态切换接口

#### Scenario: 卡券配置无效导致发布失败
- **GIVEN** 后端返回卡券配置校验错误
- **WHEN** 管理员发布活动
- **THEN** 页面展示错误原因
- **AND** 活动列表刷新后仍显示原状态
