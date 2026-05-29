## MODIFIED Requirements

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
