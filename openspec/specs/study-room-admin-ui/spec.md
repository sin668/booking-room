## Purpose

br-admin 学习室管理界面提供自习室的列表、创建、编辑与座位管理能力，供运营人员维护学习室信息。
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
br-admin SHALL 提供新建自习室表单（路由 `/room/create`）。表单字段包含：名称（必填）、描述（textarea）、封面图片（图片上传）、地址（必填）、营业时间（时间范围选择器）、最低价格（数字输入，单位元）、地图选点（可选）。封面图片上传 SHALL 调用统一 OSS 图片上传客户端，上传成功后将 OSS URL 写入 `cover_image`。地图选点 SHALL 使用腾讯位置服务 JavaScript API GL 内嵌地图，点击地图任意位置即回填 GCJ-02 的 `latitude`、`longitude`；地点搜索与地址自动回填依赖该 Key 的 WebServiceAPI 权限，未开通时 MUST NOT 阻塞选点，并给出可点击地图选点的提示。已配置 key 时展示选点入口，未配置 key 时隐藏入口并给出提示。提交时 SHALL 携带坐标字段。提交成功后跳转回列表页。

#### Scenario: Successful creation
- **WHEN** 管理员填写表单并点击提交，所有必填字段已填写
- **THEN** 创建成功，显示成功提示，跳转回 `/room/list`

#### Scenario: Validation error
- **WHEN** 管理员提交表单时缺少必填字段
- **THEN** 表单高亮显示错误字段，不提交

#### Scenario: Pick location on map
- **GIVEN** 已配置 `VITE_TENCENT_MAP_KEY`
- **WHEN** 管理员点击「在地图上选点」并点击地图任意位置
- **THEN** 表单回填该位置的 `latitude`、`longitude`，并在表单中展示已选坐标
- **AND** 提交请求体包含 `latitude`、`longitude`

#### Scenario: Search unavailable without WebServiceAPI
- **GIVEN** 腾讯 Key 未开通 WebServiceAPI
- **WHEN** 管理员在地图选点中使用地点搜索
- **THEN** 页面提示搜索需开通 WebServiceAPI，且不阻塞地图点击选点

#### Scenario: Map key not configured
- **GIVEN** 未配置 `VITE_TENCENT_MAP_KEY`
- **WHEN** 管理员打开新建自习室表单
- **THEN** 页面不展示地图选点入口，并提示可仅填写地址由后端自动解析

#### Scenario: Create without coordinates
- **WHEN** 管理员未选点直接提交表单
- **THEN** 请求体不包含坐标字段，创建成功后由后端地理编码兜底或保持坐标为空

#### Scenario: Upload study room cover to OSS
- **GIVEN** 管理员打开新建自习室表单
- **WHEN** 管理员通过封面图片上传组件选择图片
- **THEN** br-admin 调用共享上传 API 客户端
- **AND** 上传请求使用 `room-cover` scope，图片大小不得超过 5MB
- **AND** 不从活动管理 API 模块导入通用上传函数
- **AND** 后端返回 OSS 图片 URL
- **AND** 表单 `cover_image` 更新为该 URL 并展示预览

### Requirement: Edit study room form
br-admin SHALL 提供编辑自习室表单（路由 `/room/edit/:id`），复用新建表单组件，预填充现有数据，包括已有的 `latitude`、`longitude`。编辑封面图片时 SHALL 调用统一 OSS 图片上传客户端，上传成功后将新 OSS URL 写入 `cover_image`；上传失败时 SHALL 保持原封面 URL。地图选点行为与新建表单一致，并 SHALL 支持清除已选坐标后提交（清除后后端可按地址重新解析）。

#### Scenario: Successful update
- **WHEN** 管理员修改信息并提交
- **THEN** 更新成功，显示成功提示，跳转回 `/room/list`

#### Scenario: Load existing data
- **WHEN** 管理员访问 `/room/edit/1`
- **THEN** 表单预填充该自习室的当前数据，包括 `latitude`、`longitude`（存在时）

#### Scenario: Update coordinates via map picker
- **GIVEN** 管理员正在编辑已有自习室
- **WHEN** 管理员重新选点并提交
- **THEN** 请求体携带新的 `latitude`、`longitude`，更新成功后表单回显新坐标

#### Scenario: Clear coordinates
- **GIVEN** 管理员正在编辑已有自习室且已有坐标
- **WHEN** 管理员点击清除坐标并提交
- **THEN** 请求体不包含坐标字段或包含空值，更新成功

#### Scenario: Replace study room cover
- **GIVEN** 管理员正在编辑已有自习室且已存在封面图
- **WHEN** 管理员选择新的封面图片并上传成功
- **THEN** 表单 `cover_image` 更新为新的 OSS URL
- **AND** 上传请求使用 `room-cover` scope
- **AND** 图片预览展示新的 OSS URL

#### Scenario: Study room cover upload failure
- **GIVEN** 管理员正在编辑已有自习室且已存在封面图
- **WHEN** 管理员选择新的封面图片但上传失败
- **THEN** 页面展示上传失败提示
- **AND** 表单 `cover_image` 保持原封面 URL

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

