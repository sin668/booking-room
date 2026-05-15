## MODIFIED Requirements

### Requirement: Booking tab page
系统 SHALL 将 br-app"预约"tab 页改造为预约主页面。页面包含：顶部城市选择器（显示当前城市名，点击跳转城市选择页）、日期选择器（横向滚动，显示近 7 天）、时段选择网格、区域筛选标签、座位平面图、底部座位信息栏及"立即预约"按钮。城市选择器 SHALL 动态显示 Vuex store 中的当前城市名，不再硬编码。

#### Scenario: Display booking tab with dynamic city
- **WHEN** 用户点击底部"预约" tab
- **THEN** 页面顶部城市选择器显示当前城市名（从 Vuex store 读取），点击可跳转城市选择页

#### Scenario: Navigate to city selection
- **WHEN** 用户点击顶部城市选择器
- **THEN** 跳转到城市选择页 `pages/city-select/index`

#### Scenario: City updated after selection
- **GIVEN** 用户在城市选择页选择了新城市
- **WHEN** 返回预约页
- **THEN** 顶部城市名更新为所选城市，自习室列表按新城市过滤刷新
