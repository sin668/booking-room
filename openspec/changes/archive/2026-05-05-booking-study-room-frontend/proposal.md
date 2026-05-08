## Why

当前 br-app 的"预约"和"订单"页面均为占位符状态，后端仅有自习室列表接口 (`GET /api/v1/rooms/`)，无座位数据和预约 API，用户无法完成选座预约的完整流程。需要补齐座位模型、预约 API，并参照 prototype 高保真原型图实现前端预约全流程，打通核心业务闭环。

## What Changes

- 新增后端座位（Seat）数据模型，支持按区域（静音区、键盘区、VIP区）和楼层分类，模拟生成座位数据
- 新增后端座位列表 API（按房间/日期/时段查询可用座位）
- 新增后端预约（Booking）数据模型和 RESTful API（创建预约、查询我的预约、取消预约）
- 将 br-app "预约" tab 页从占位符改造为预约主页面（日期选择 + 时段选择 + 区域筛选 + 座位图 + 立即预约），参照 `prototype/booking.html`
- 新增门店详情页（封面/评分/地址/座位概况/环境照片/立即预约），参照 `prototype/store-detail.html`
- 新增座位选择页（区域tab + 楼层切换 + 座位平面图 + 确认选座），参照 `prototype/seat-select.html`
- 新增订单确认页（门店信息 + 座位信息 + 日期时段 + 费用明细 + 立即支付），参照 `prototype/order-confirm.html`
- 将 br-app "订单" tab 页从占位符改造为我的预约列表页，参照 `prototype/orders.html`

## Capabilities

### New Capabilities

- `study-room-seats-api`: 座位数据模型与 API —— Seat model、座位列表接口（支持按区域/日期/时段筛选可用座位）
- `study-room-booking-api`: 后端预约 API —— Booking model、创建预约（按座位+时段）、查询预约列表/详情、取消预约接口
- `study-room-booking-ui`: 前端预约全流程 UI —— 预约tab页、门店详情页、座位选择页、订单确认页、我的预约列表页

### Modified Capabilities

（无现有 spec 需要修改）

## Impact

- **br-server**: 新增 Seat/Booking model、seats/booking route/service/schema、alembic migration、座位种子数据
- **br-app**: 改造 `pages/booking/index.vue`，新增 detail/seat-select/confirm 页面，改造 `pages/orders/index.vue`，新增 `api/seats.js` 和 `api/bookings.js`
- **br-app/pages.json**: 注册新增页面路由
- **数据库**: 新增 `seats` 表和 `bookings` 表
- **回滚方案**: alembic downgrade 回滚数据库迁移；前端 revert 对应 commit 即可恢复占位符状态
- **影响模块范围**: br-server（models、routes、services、schemas、migrations）、br-app（pages、api、router）
