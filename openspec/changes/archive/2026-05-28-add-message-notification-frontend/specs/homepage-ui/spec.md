## MODIFIED Requirements

### Requirement: Homepage top navigation bar
首页 SHALL 展示固定顶部导航栏，包含三个区域：左侧城市定位（显示当前城市名+下拉箭头图标，可点击切换城市）、中间搜索框（灰色背景圆形搜索框，显示"搜索自习室"占位文案，点击跳转搜索页面）、右侧通知铃铛（带红色未读提示点）。导航栏背景为白色，固定在页面顶部。通知铃铛 SHALL 作为消息通知页面入口；当 br-server 未读摘要显示存在用户已开启类型的未读消息时，铃铛 SHALL 展示红色未读提示点。

#### Scenario: Display navigation bar
- **WHEN** 用户进入首页
- **THEN** 顶部展示白色导航栏，左侧显示城市定位"茂名市"+下拉箭头，中间显示"搜索自习室"搜索框，右侧显示通知铃铛图标

#### Scenario: Tap search bar
- **WHEN** 用户点击中间搜索框
- **THEN** 系统跳转到搜索页面（V1 暂为占位页面）

#### Scenario: Tap notification bell
- **WHEN** 用户点击通知铃铛
- **THEN** 系统 SHALL 跳转到消息通知页面

#### Scenario: Display unread notification dot
- **GIVEN** br-server 未读摘要返回用户存在已开启类型的未读消息
- **WHEN** 用户进入首页
- **THEN** 通知铃铛 SHALL 展示红色未读提示点

#### Scenario: Hide unread notification dot
- **GIVEN** br-server 未读摘要返回用户不存在未读消息或未读消息类型均已在设置中关闭
- **WHEN** 用户进入首页
- **THEN** 通知铃铛 SHALL 不展示红色未读提示点

#### Scenario: Unread summary load failure
- **GIVEN** br-server 未读摘要接口加载失败
- **WHEN** 用户进入首页
- **THEN** 首页 SHALL 正常展示主要内容
- **AND** 通知铃铛 SHALL 不展示红色未读提示点
