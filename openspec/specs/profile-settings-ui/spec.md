## Purpose
Define the app settings page UI for profile display, username editing, and logout.

## Requirements

### Requirement: Settings page layout
小程序 SHALL 提供“我的设置”页面，并保持与 `prototype/settings.html` 的总体视觉风格一致，包括顶部导航、头像资料卡、白色圆角分组卡片、个人资料、账号与安全、通知设置、通用、关于和退出登录入口。

#### Scenario: Open settings from profile
- **GIVEN** 用户已登录并停留在“我的”页面
- **WHEN** 用户点击设置入口
- **THEN** 小程序导航到“我的设置”页面
- **AND** 页面展示头像资料卡和设置分组列表

#### Scenario: Settings page visual hierarchy
- **GIVEN** 用户进入“我的设置”页面
- **WHEN** 页面加载完成
- **THEN** 页面 SHALL 使用浅灰背景、白色圆角卡片、紧凑列表行和右侧箭头/开关控件呈现内容

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
