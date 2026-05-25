## Why

用户在订单列表点击"查看座位"后，只能跳转到自习室详情页，无法直观看到自己预定的具体座位位置。需要提供类似飞机选座的效果：跳转到对应自习室的座位布局图，预定的座位上显示小人图标，让用户一目了然。

## What Changes

- **新增座位查看模式**：在现有座位选择页（seat-select.vue）增加只读查看模式（viewMode），禁用交互操作，隐藏日期/时间选择器和确认按钮
- **高亮预定座位**：预定座位显示小人图标，其余座位保持原有状态展示
- **修复"查看座位"跳转**：将 orders/index.vue 的 viewSeat 方法改为传递完整参数（room_id, seat_id, date, start_time, end_time），跳转到 seat-select 页面的查看模式
- **注册页面参数**：seat-select 页面支持通过 URL 参数 `mode=view` 进入查看模式

## Capabilities

### New Capabilities
（无新增独立能力）

### Modified Capabilities
- `seat-view-mode`: 座位选择页新增只读查看模式，支持通过 URL 参数激活

## Impact

- **前端 br-app**：seat-select.vue（新增 viewMode 逻辑）、orders/index.vue（修复跳转参数）
- **API**：无需后端改动，复用现有 getSeats 接口
- **回滚方案**：移除 viewMode 相关代码，恢复 viewSeat 原始跳转逻辑即可
