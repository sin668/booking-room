# message-notification-ui Delta Spec

## ADDED Requirements

### Requirement: Arrival reminder trigger on room detail

自习室、培训室、综合室共用的房间详情页 SHALL 在用户定位成功且距离房间不超过 500 米时，自动触发一条「到店签到提醒」消息；该触发 MUST NOT 阻塞页面渲染或弹出提示。

#### Scenario: Trigger reminder when within 500 meters

- **GIVEN** 用户已登录且打开房间详情页
- **WHEN** 定位成功且用户与房间距离不超过 500 米
- **THEN** 客户端 SHALL 调用到店提醒接口提交房间与用户坐标
- **AND** 客户端 SHALL NOT 因该请求阻塞详情页展示或弹出 toast

#### Scenario: No reminder when beyond 500 meters

- **GIVEN** 用户打开房间详情页
- **WHEN** 定位成功且用户与房间距离超过 500 米
- **THEN** 客户端 SHALL NOT 触碰到店提醒请求

#### Scenario: No reminder without location

- **GIVEN** 用户打开房间详情页
- **WHEN** 用户拒绝定位、定位失败或房间没有坐标
- **THEN** 客户端 SHALL NOT 触碰到店提醒请求
- **AND** 页面 SHALL 保持原有地址降级展示

#### Scenario: No reminder for guests

- **GIVEN** 用户未登录
- **WHEN** 用户打开房间详情页且距离房间不超过 500 米
- **THEN** 客户端 SHALL NOT 触碰到店提醒请求

#### Scenario: Trigger at most once per page visit

- **GIVEN** 用户进入房间详情页且满足到店提醒条件
- **WHEN** 页面内重复发生定位回调
- **THEN** 客户端 SHALL NOT 在同一次页面访问中重复触发该请求

### Requirement: Non-conversation notification navigation

消息中心中除会话以外的系统消息 SHALL 在点击并标记已读成功后跳转到对应目标链接。

#### Scenario: Navigate by target URL

- **GIVEN** 系统消息包含 `target_url`
- **WHEN** 用户点击该消息且标记已读成功
- **THEN** 小程序 SHALL 跳转到 `target_url` 指向的页面

#### Scenario: Navigate arrival reminder to learning code

- **GIVEN** 到店签到提醒消息不包含 `target_url`
- **WHEN** 用户点击该消息且标记已读成功
- **THEN** 小程序 SHALL 跳转到我的学习码页面

#### Scenario: Conversation entries keep their own routing

- **GIVEN** 消息中心展示了会话条目
- **WHEN** 用户点击会话条目
- **THEN** 小程序 SHALL 进入对应的 IM 会话窗口
- **AND** 该行为 SHALL NOT 受系统消息跳转逻辑影响
