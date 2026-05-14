## Why

首页已经提供“卡券套餐”快捷入口，但当前产品缺少真实卡券数据、订单确认页选券和下单抵扣闭环。仅实现前端静态卡券包会造成用户能看到优惠券却无法真正使用，和预约场景不一致。

本变更将补齐由 `br-server` 提供真实卡券数据的完整闭环：用户查看卡券、订单确认页筛选可用卡券、下单时后端校验并抵扣、订单绑定卡券、卡券状态流转。

## What Changes

- 新增 `br-server` 卡券后端能力：
  - 新增卡券模板和用户卡券数据模型。
  - 提供当前用户卡券列表接口，支持 `available`、`used`、`expired` 状态过滤。
  - 提供按预约参数筛选可用卡券的接口。
  - 支持满减券、立减券、折扣券三类卡券。
  - 支持全场通用、首次预约、指定座位类型三类适用范围。
  - 使用 `expires_at` 在查询和下单时动态判断过期，不引入定时任务。
- 修改预约下单能力：
  - `POST /api/v1/bookings` 请求体增加可选 `coupon_id`。
  - 后端在服务层重新校验卡券归属、状态、有效期、适用范围和订单门槛。
  - 每个订单最多使用 1 张卡券。
  - 订单保存原价、抵扣金额、实付金额和使用的卡券。
  - 下单成功后用户卡券状态变为 `used`。
  - 取消已确认订单时，首版恢复该订单使用的卡券为可使用状态。
- 新增 `br-app` 卡券包页面：
  - `/pages/coupon/index` 展示可使用、已使用、已过期卡券。
  - 页面数据来自真实后端接口，不再以 fallback 数据作为主要数据源。
- 修改 `br-app` 订单确认页：
  - 根据座位、日期、时间和订单原价请求可用卡券。
  - 支持选择 1 张卡券并展示抵扣后金额。
  - 创建预约时提交 `coupon_id`。
- 保持 `prototype/coupon.html` 的总体视觉风格一致。

## Capabilities

### New Capabilities
- `coupon-api`: 后端卡券数据、规则校验、用户卡券状态流转和用户端 REST API。
- `coupon-package-ui`: 移动端卡券包前端能力，覆盖卡券列表、状态切换、空状态和可使用卡券入口行为。

### Modified Capabilities
- `homepage-ui`: 首页“卡券套餐”快捷入口 MUST 指向真实可访问的卡券包页面，而不是缺失路由。
- `study-room-booking-api`: 预约下单 MUST 支持可选卡券抵扣，并由后端完成价格计算、卡券校验和状态流转。
- `study-room-booking-ui`: 订单确认页 MUST 支持展示可用卡券、选择卡券和提交 `coupon_id`。

## Impact

- 后端影响模块：
  - `br-server/app/models/coupon.py`
  - `br-server/app/schemas/coupon.py`
  - `br-server/app/services/coupon_service.py`
  - `br-server/app/api/routes/coupon.py`
  - `br-server/app/models/booking.py`
  - `br-server/app/schemas/booking.py`
  - `br-server/app/services/booking_service.py`
  - `br-server/app/api/routes/booking.py`
  - `br-server/app/main.py`
  - `br-server/alembic/versions/*`
  - `br-server/tests/test_coupon_service.py`
  - `br-server/tests/test_api_coupon.py`
  - 相关 booking API/service 测试
- 前端影响模块：
  - `br-app/src/pages/coupon/index.vue`
  - `br-app/src/pages/booking/confirm.vue`
  - `br-app/src/pages.json`
  - `br-app/src/api/coupons.js`
  - `br-app/src/api/bookings.js`
  - `br-app/src/pages/index/index.vue`
  - 如需新增空状态图标，可能影响 `br-app/src/static/icons/iconfont.css`
- 文档影响：
  - `docs/api.md` 需要记录卡券接口、预约下单 `coupon_id`、金额字段和错误码。
- 数据库影响：
  - 新增卡券相关表。
  - 预约表增加卡券和金额拆分字段。
- 原型参考：
  - `prototype/coupon.html`
  - `prototype/order-confirm.html`
- 回滚方案：
  - 前端回滚：移除卡券包路由、页面、订单确认页选券区和 coupon API 调用。
  - 后端回滚：回退卡券相关迁移，移除卡券路由/服务/模型，恢复 booking schema/service 中的 `coupon_id` 和金额拆分字段。
  - 数据回滚前需确认没有生产订单依赖新增的卡券字段；若已有订单数据，应先导出订单与卡券绑定关系。
