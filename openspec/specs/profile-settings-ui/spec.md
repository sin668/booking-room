## Purpose
Define the app settings page UI for profile display, username editing, and logout.
## Requirements
### Requirement: Settings page layout
小程序 SHALL 提供“我的设置”页面，并保持与 `prototype/settings.html` 的总体视觉风格一致，包括顶部导航、头像资料卡、白色圆角分组卡片、个人资料、账号与安全、通知设置、通用、关于和退出登录入口。头像资料卡 SHALL 支持点击头像选择本地图片并上传，上传成功后更新当前用户头像。

#### Scenario: Open settings from profile
- **GIVEN** 用户已登录并停留在“我的”页面
- **WHEN** 用户点击设置入口
- **THEN** 小程序导航到“我的设置”页面
- **AND** 页面展示头像资料卡和设置分组列表

#### Scenario: Settings page visual hierarchy
- **GIVEN** 用户进入“我的设置”页面
- **WHEN** 页面加载完成
- **THEN** 页面 SHALL 使用浅灰背景、白色圆角卡片、紧凑列表行和右侧箭头/开关控件呈现内容

#### Scenario: Upload avatar from settings
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击头像并选择一张图片
- **THEN** 小程序调用统一图片上传接口上传该图片
- **AND** 上传请求使用 `avatar` scope，图片大小不得超过 2MB
- **AND** 上传成功后调用当前用户资料更新接口保存 `avatar` 为返回的图片 URL
- **AND** 页面头像和“我的”页面头像刷新为新 URL

#### Scenario: Avatar upload failure
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户选择头像图片但上传接口失败
- **THEN** 页面展示上传失败提示
- **AND** 当前用户头像保持原值

#### Scenario: Avatar profile save failure
- **GIVEN** 用户头像图片已上传成功
- **WHEN** 保存用户资料接口失败
- **THEN** 页面展示保存失败提示
- **AND** 当前用户头像保持原值

### Requirement: Profile fields display
设置页 SHALL 在“个人资料”分组展示昵称、用户名、手机号、性别、生日和个性签名等资料行，其中用户名必须来自当前用户资料。

#### Scenario: Display username row
- **GIVEN** 当前用户 username 为 `Luna48392`
- **WHEN** 用户打开“我的设置”页面
- **THEN** “个人资料”分组展示“用户名”行
- **AND** 该行右侧展示 `Luna48392`

#### Scenario: Mask phone number
- **GIVEN** 当前用户手机号为 `13800138000`
- **WHEN** 用户打开“我的设置”页面
- **THEN** 手机号行右侧展示脱敏值 `138****8000`

### Requirement: Edit username interaction
设置页 SHALL 支持从“用户名”资料行进入编辑流程，并在保存成功后刷新页面展示的用户名。用户名编辑界面 SHALL 提示“用户名修改后 24 小时内不可再次修改”。

#### Scenario: Save valid username
- **GIVEN** 当前用户打开“我的设置”页面
- **WHEN** 用户点击“用户名”行并提交新用户名 `LunaStudy01`
- **THEN** 小程序调用当前用户资料更新接口
- **AND** 保存成功后“用户名”行展示 `LunaStudy01`
- **AND** 用户名编辑界面展示 24 小时冷却规则提示

#### Scenario: Username cooldown feedback
- **GIVEN** 用户正在编辑用户名
- **WHEN** 后端返回 HTTP 429 表示用户名修改处于冷却期
- **THEN** 小程序 SHALL 保持当前用户名不变
- **AND** 展示剩余冷却时间提示，如“用户名修改冷却中，请在 X 小时 Y 分钟后再试”

#### Scenario: Duplicate username feedback
- **GIVEN** 用户正在编辑用户名
- **WHEN** 后端返回 HTTP 409 表示用户名已存在
- **THEN** 小程序 SHALL 保持编辑界面可继续修改
- **AND** 展示“该用户名已存在”的错误提示

### Requirement: Logout confirmation
设置页 SHALL 在用户点击退出登录时展示确认弹层，用户确认后清除登录态并返回登录页。

#### Scenario: Confirm logout
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“退出登录”并在确认弹层中确认
- **THEN** 小程序清除本地登录态
- **AND** 导航到登录页

### Requirement: Notification preference switches
设置页 SHALL 在“通知设置”分组提供 4 类消息通知开关：预约提醒、活动通知、学习报告、到店打卡提醒。每个开关 SHALL 使用稳定类型键：`booking`、`activity`、`report`、`arrival`，并通过 br-server 通知偏好接口读取和保存。

#### Scenario: Display notification preference switches
- **GIVEN** 用户进入“我的设置”页面
- **WHEN** 页面加载完成
- **THEN** “通知设置”分组 SHALL 展示“预约提醒”、“活动通知”、“学习周报”、“到店打卡提醒”四个开关
- **AND** 四个开关 SHALL 分别映射到 `booking`、`activity`、`report`、`arrival`

#### Scenario: Toggle notification preference
- **GIVEN** 用户进入“我的设置”页面
- **WHEN** 用户关闭“学习周报”开关
- **THEN** 小程序 SHALL 调用 br-server 通知偏好更新接口保存 `report_enabled=false`
- **AND** 消息通知页面 SHALL 能读取该偏好并展示对应类型已关闭提示

#### Scenario: Restore notification preferences from backend
- **GIVEN** 用户已修改并保存通知设置
- **WHEN** 用户离开并重新进入“我的设置”页面
- **THEN** 页面 SHALL 从 br-server 通知偏好接口恢复上次保存的 4 类通知开关状态

#### Scenario: Roll back failed preference save
- **GIVEN** 用户进入“我的设置”页面且“学习周报”开关为开启
- **WHEN** 用户关闭“学习周报”开关但 br-server 通知偏好更新接口失败
- **THEN** 页面 SHALL 将“学习周报”开关恢复为开启
- **AND** 页面 SHALL 展示保存失败提示

### Requirement: Account security entries are actionable
设置页 SHALL 在“账号与安全”分组提供可操作的“修改密码”、“微信绑定”、“实名认证”和“注销账号”入口，不得继续只展示暂未开放提示。

#### Scenario: Open change password flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“修改密码”
- **THEN** 小程序 SHALL 打开修改密码表单
- **AND** 表单 SHALL 包含旧密码、新密码、确认新密码和提交按钮

#### Scenario: Open WeChat binding flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“微信绑定”
- **THEN** 小程序 SHALL 根据当前微信绑定状态展示已绑定信息或打开绑定流程

#### Scenario: Open identity verification flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“实名认证”
- **THEN** 小程序 SHALL 打开实名认证页面或弹层
- **AND** 页面 SHALL 展示实名状态、姓名输入、身份证号输入和提交按钮

#### Scenario: Open account deactivation flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“注销账号”
- **THEN** 小程序 SHALL 打开注销账号说明页或确认弹层
- **AND** 页面 SHALL 展示注销影响、风险检查结果和二次确认操作

### Requirement: Account security statuses
设置页 SHALL 在账号与安全入口右侧展示当前状态摘要，便于用户判断是否已完成安全设置。

#### Scenario: Display security status summary
- **GIVEN** 用户已登录
- **WHEN** 设置页加载账号安全摘要成功
- **THEN** “微信绑定”行 SHALL 展示“已绑定”或“未绑定”
- **AND** “实名认证”行 SHALL 展示“已认证”或“未认证”
- **AND** “注销账号”行 SHALL 在账号已注销前保持可进入状态

#### Scenario: Fallback when security summary fails
- **GIVEN** 用户已登录
- **WHEN** 设置页加载账号安全摘要失败
- **THEN** 页面 SHALL 保持账号与安全入口可见
- **AND** 状态摘要 SHALL 展示为空或“--”
- **AND** 用户点击入口时 SHALL 重新尝试加载必要数据

### Requirement: Change password feedback
修改密码流程 SHALL 对前端校验和后端错误提供明确反馈。

#### Scenario: Reject mismatched new password confirmation
- **GIVEN** 用户正在修改密码
- **WHEN** 新密码和确认新密码不一致
- **THEN** 小程序 SHALL 阻止提交
- **AND** 展示“确认密码与新密码不一致”

#### Scenario: Show old password error
- **GIVEN** 用户正在修改密码
- **WHEN** 后端返回旧密码错误
- **THEN** 小程序 SHALL 保持表单可编辑
- **AND** 展示“原密码错误”

#### Scenario: Password changed successfully
- **GIVEN** 用户正在修改密码
- **WHEN** 后端确认密码修改成功
- **THEN** 小程序 SHALL 展示“密码已更新”
- **AND** 返回“我的设置”页面或关闭修改密码弹层

### Requirement: Identity verification feedback
实名认证流程 SHALL 对身份证号、姓名、提交状态和脱敏展示提供明确反馈。

#### Scenario: Reject invalid identity format
- **GIVEN** 用户正在实名认证
- **WHEN** 用户提交空姓名或格式错误的身份证号
- **THEN** 小程序 SHALL 阻止提交或展示后端错误
- **AND** 不得保存无效实名资料

#### Scenario: Show masked identity after submission
- **GIVEN** 用户提交实名认证资料成功
- **WHEN** 设置页重新加载
- **THEN** “实名认证”入口 SHALL 展示认证状态
- **AND** 实名详情 SHALL 只展示脱敏身份证号

### Requirement: Account deletion confirmation
注销账号流程 SHALL 在提交前展示风险检查和二次确认，提交成功后清除本地登录态。

#### Scenario: Block deactivation with unresolved risks
- **GIVEN** 用户打开注销账号流程
- **WHEN** 后端返回余额、未完成订单、未用卡券等阻断原因
- **THEN** 小程序 SHALL 展示阻断原因列表
- **AND** 不允许用户提交注销申请

#### Scenario: Submit account deletion
- **GIVEN** 用户无注销阻断风险
- **WHEN** 用户完成二次确认并提交注销
- **THEN** 小程序 SHALL 调用注销账号接口
- **AND** 成功后清除本地登录态并跳转登录页
