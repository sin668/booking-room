## MODIFIED Requirements

### Requirement: Homepage study room list
首页（`pages/index/index.vue`）自习室列表 SHALL 按当前选中城市过滤。页面顶部 SHALL 显示城市选择器（与预约页一致），点击可跳转城市选择页。切换城市后列表自动刷新。

#### Scenario: Display homepage with city filter
- **WHEN** 用户进入首页
- **THEN** 首页顶部显示当前城市名，自习室列表按当前城市过滤

#### Scenario: Switch city from homepage
- **WHEN** 用户在首页点击城市名并选择新城市
- **THEN** 返回首页后城市名更新，自习室列表按新城市刷新

#### Scenario: Homepage without city selection
- **WHEN** 用户首次使用，无本地存储的城市偏好
- **THEN** 首页使用默认城市（服务端 sort_order 最小的 active 城市），自习室列表按默认城市过滤

### Requirement: Store detail page
系统 SHALL 提供门店详情页（`pages/booking/detail.vue`）。页面包含：顶部封面大图、门店名称和营业状态标签、评分、地址（含距离）、营业时间、区域标签、环境照片横向滚动列表、座位概况统计卡片（总座位/可用/已占/维护中）、底部固定栏（收藏按钮 + "立即预约"按钮）。地址前 SHALL 显示城市名称（当 `city_name` 不为空时）。

#### Scenario: Display store detail with city
- **WHEN** 用户进入详情页，自习室关联了城市
- **THEN** 地址显示为"茂名市 茂南区油城三路88号"格式（城市名 + 地址）

#### Scenario: Display store detail without city
- **WHEN** 用户进入详情页，自习室未关联城市（`city_name` 为 null）
- **THEN** 地址仅显示原始 address 字段内容，不添加城市名前缀
