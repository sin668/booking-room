## ADDED Requirements

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
