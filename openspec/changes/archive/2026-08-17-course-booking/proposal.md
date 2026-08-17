## Why

平台目前仅支持自习室座位预约，培训课程页面（课程详情、课程列表）只提供浏览功能，用户无法直接预约课程。需要在 br-app 中新增课程预约下单功能，支持课时选择、全套课时优惠、优惠券抵扣和支付，并将课程预约订单纳入现有订单列表统一管理。

## What Changes

- **数据模型扩展**：在 `courses` 表新增全套课时优惠价格字段（`full_package_price`）；扩展 `bookings` 表支持课程预约类型（新增 `booking_type`、`course_id`、`lesson_ids`、`schedule_type` 字段，`seat_id` 改为可空）
- **新增课程预约 API**：在 br-server 新增课程预约路由和服务，支持获取课程课时列表、创建课程预约订单（含全套优惠计算）、课程订单支付与取消
- **新增课程预约页面**：在 br-app 新增 `pages/training/course-booking.vue` 页面，严格参考 `prototype/course-booking.html` 原型，包含预约类型切换、课时多选、全套课时一键选择与优惠价格、优惠券选择、支付方式选择、价格实时计算
- **扩展订单列表**：修改 `pages/orders/index.vue`，支持展示课程预约订单，显示课程名称、课时信息等差异化内容

## Capabilities

### New Capabilities

- `course-booking-api`: 课程预约后端 API —— 课时列表查询、课程预约下单（含固定班课/1V1/全套课时优惠定价逻辑）、课程订单支付与取消
- `course-booking-ui`: 课程预约前端页面 —— 参考高保真原型实现课时选择、全套课时展开、优惠价格展示、优惠券与支付选择、下单确认的完整流程

### Modified Capabilities

- `booking-payment`: 扩展支付流程以支持课程预约订单的创建、支付确认与取消退款

## Impact

- **后端**（br-server）：新增 `app/api/routes/course_booking.py` 路由、`app/services/course_booking_service.py` 服务、`app/schemas/course_booking.py` 数据模型；修改 `app/models/booking.py` 和 `app/models/course.py`；新增 Alembic 数据库迁移
- **前端**（br-app）：新增 `pages/training/course-booking.vue` 页面、`api/courseBooking.js` 接口模块；修改 `pages/orders/index.vue` 订单列表页、`pages.json` 路由注册
- **复用依赖**：复用现有优惠券系统（coupon）、钱包/微信支付（wallet/wechat-payment）、用户认证（auth）
- **回滚方案**：通过 feature flag 关闭课程预约入口；Alembic migration 提供 downgrade 路径；前端页面独立可删除，不影响现有自习室预约功能
