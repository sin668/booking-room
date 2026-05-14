# 卡券套餐完整闭环实施任务

## 文件职责边界

- `br-server/app/models/coupon.py`: 只定义 `Coupon`、`UserCoupon` ORM 模型和表字段关系。
- `br-server/app/schemas/coupon.py`: 只定义卡券接口请求/响应 schema、枚举 Literal 和序列化字段。
- `br-server/app/services/coupon_service.py`: 只负责卡券查询、动态过期归类、适用性校验、抵扣金额计算、卡券使用/恢复状态流转。
- `br-server/app/api/routes/coupon.py`: 只负责 HTTP 参数解析、鉴权依赖、调用 service、映射错误响应。
- `br-server/app/services/booking_service.py`: 保留预约冲突检测和订单创建职责；通过 `coupon_service` 完成卡券校验和抵扣，不重复实现卡券规则。
- `br-app/src/api/coupons.js`: 只封装卡券后端接口，不存放业务展示状态。
- `br-app/src/pages/coupon/index.vue`: 只负责卡券包列表、页签、空状态和跳转预约。
- `br-app/src/pages/booking/confirm.vue`: 只负责订单确认页选券、金额展示、提交 `coupon_id`。

## 1. 后端模型与迁移

- [x] 1.1 新增后端模型文件 `br-server/app/models/coupon.py`，定义 `Coupon` 表字段：`id`、`name`、`description`、`type`、`discount_amount`、`discount_percent`、`min_order_amount`、`scope`、`seat_zone`、`valid_from`、`expires_at`、`is_active`、`created_at`、`updated_at`
- [x] 1.2 在 `br-server/app/models/coupon.py` 定义 `UserCoupon` 表字段：`id`、`user_id`、`coupon_id`、`status`、`used_booking_id`、`used_at`、`created_at`、`updated_at`
- [x] 1.3 在 `br-server/app/models/__init__.py` 导出 `Coupon` 和 `UserCoupon`
- [x] 1.4 修改 `br-server/alembic/env.py` 的模型导入列表，加入 `Coupon` 和 `UserCoupon`，确保 Alembic metadata 能识别新表
- [x] 1.5 新增 Alembic 迁移文件，创建 `coupons` 表，字段类型和默认值与 `design.md` 的 Data Model 保持一致
- [x] 1.6 在同一迁移或后续迁移中创建 `user_coupons` 表，添加 `user_id/status`、`coupon_id`、`used_booking_id` 索引
- [x] 1.7 在预约表迁移中增加 `original_price`、`discount_amount`、`coupon_id` 字段，保留 `total_price` 表示抵扣后实付金额
- [x] 1.8 为已有预约数据提供迁移回填：`original_price = total_price`，`discount_amount = 0`，`coupon_id = null`
- [ ] 1.9 执行迁移验证命令：`alembic upgrade head`，期望成功创建/更新表结构
- [ ] 1.10 执行迁移回滚验证命令：`alembic downgrade -1` 后再 `alembic upgrade head`，期望可回滚并重新升级

## 2. 后端卡券 Schema

- [x] 2.1 新增 `br-server/app/schemas/coupon.py`，定义卡券类型枚举：`amount_off`、`threshold_amount_off`、`percentage_off`
- [x] 2.2 在 `br-server/app/schemas/coupon.py` 定义卡券适用范围枚举：`all`、`first_booking`、`seat_zone`
- [x] 2.3 在 `br-server/app/schemas/coupon.py` 定义卡券状态枚举：`available`、`used`、`expired`
- [x] 2.4 定义 `CouponResponse`，包含用户卡券 id、模板 id、名称、说明、类型、适用范围、状态、金额/折扣、门槛、生效时间、过期时间、使用时间和使用订单
- [x] 2.5 定义 `AvailableCouponForBookingResponse`，在 `CouponResponse` 基础上增加 `discount_amount` 和 `payable_amount`
- [x] 2.6 定义 `AvailableCouponsForBookingListResponse`，包含 `original_price` 和 `items`
- [ ] 2.7 运行 schema 相关导入检查：`python -m pytest tests/test_api_auth.py -q`，期望现有测试不因新增 schema 破坏导入

## 3. 后端卡券服务：查询与归类

- [x] 3.1 新增 `br-server/app/services/coupon_service.py`，定义卡券领域错误：`CouponError`、`CouponNotFoundError`、`CouponUnavailableError`
- [x] 3.2 实现动态状态判断函数：未使用且未过期为 `available`，已使用为 `used`，未使用但过期为 `expired`
- [x] 3.3 实现 `list_user_coupons(db, user_id, status=None)`，只返回当前用户卡券，不泄露其他用户数据
- [x] 3.4 为 `list_user_coupons` 增加按 `available`、`used`、`expired` 过滤逻辑
- [x] 3.5 新增 `br-server/tests/test_coupon_service.py`，覆盖动态过期归类、状态过滤、只返回当前用户数据
- [x] 3.6 执行测试：`pytest tests/test_coupon_service.py -q`，期望新增服务测试通过

## 4. 后端卡券服务：金额与适用性

- [x] 4.1 在 `coupon_service.py` 实现订单原价计算函数，使用座位 `price_per_hour` 和预约时长计算 Decimal 金额，保留 2 位小数
- [x] 4.2 实现满减券抵扣：订单原价达到 `min_order_amount` 时抵扣 `discount_amount`
- [x] 4.3 实现立减券抵扣：无门槛或门槛为 0 时抵扣 `discount_amount`，抵扣金额不得超过订单原价
- [x] 4.4 实现折扣券抵扣：按 `discount_percent` 计算抵扣金额，保留 2 位小数
- [x] 4.5 实现全场通用适用范围校验
- [x] 4.6 实现首次预约适用范围校验：存在 `confirmed` 或 `completed` 历史预约时不可用
- [x] 4.7 实现指定座位类型适用范围校验：`coupon.seat_zone` 必须匹配 `seat.zone`
- [x] 4.8 实现 `list_available_coupons_for_booking(db, user_id, seat_id, date, start_time, end_time)`，返回原价和可用券抵扣结果
- [x] 4.9 扩展 `tests/test_coupon_service.py`，覆盖满减、立减、折扣、门槛不足、首次预约、VIP 座位类型、过期不可用
- [x] 4.10 执行测试：`pytest tests/test_coupon_service.py -q`，期望全部通过

## 5. 后端卡券 API

- [x] 5.1 新增 `br-server/app/api/routes/coupon.py`，创建 `APIRouter(prefix="/api/v1/coupons", tags=["coupons"])`
- [x] 5.2 实现 `GET /api/v1/coupons`，接收 `status` 查询参数，依赖 `get_current_user_id` 和 `get_db`
- [x] 5.3 实现 `GET /api/v1/coupons/available-for-booking`，接收 `seat_id`、`date`、`start_time`、`end_time` 查询参数
- [x] 5.4 在 `br-server/app/main.py` 注册 coupon router
- [x] 5.5 新增 `br-server/tests/test_api_coupon.py`，覆盖未登录 401、状态过滤、过期列表、预约可用券列表
- [x] 5.6 执行测试：`pytest tests/test_api_coupon.py -q`，期望全部通过

## 6. 后端预约下单抵扣

- [x] 6.1 修改 `br-server/app/schemas/booking.py`，`BookingCreate` 增加可选 `coupon_id: int | None = None`
- [x] 6.2 修改 `BookingResponse` 和 `BookingAdminResponse`，增加 `original_price`、`discount_amount`、`coupon_id`
- [x] 6.3 修改 `br-server/app/models/booking.py`，增加 `original_price`、`discount_amount`、`coupon_id` ORM 字段
- [x] 6.4 修改 `booking_service.create_booking`：无卡券时 `original_price=total_price`、`discount_amount=0`
- [x] 6.5 修改 `booking_service.create_booking`：有 `coupon_id` 时调用 `coupon_service` 校验并计算抵扣，不在 booking service 复制卡券规则
- [x] 6.6 在同一数据库事务中创建预约并将 `UserCoupon` 标记为 `used`，写入 `used_booking_id` 和 `used_at`
- [x] 6.7 确保卡券不可用时抛出 booking 层可映射的错误，API 返回 HTTP 400，且不创建预约、不改变卡券状态
- [x] 6.8 修改 `booking_service.cancel_booking`：取消使用卡券的 `confirmed` 预约时恢复用户卡券为 `available`
- [x] 6.9 修改 `br-server/app/api/routes/booking.py`，把卡券不可用错误映射为“卡券不可用，请重新选择”
- [x] 6.10 更新 `br-server/tests/test_api_booking.py` 和 booking service 测试，覆盖无卡券下单、使用卡券下单、无效卡券下单、取消恢复卡券
- [x] 6.11 执行测试：`pytest tests/test_api_booking.py tests/test_coupon_service.py tests/test_api_coupon.py -q`，期望全部通过

## 7. 前端卡券 API 与路由

- [x] 7.1 在 `br-app/src/pages.json` 注册 `pages/coupon/index`，导航标题为“卡券包”
- [x] 7.2 新增 `br-app/src/api/coupons.js`，封装 `getCoupons(status)`，请求 `/api/v1/coupons`
- [x] 7.3 在 `br-app/src/api/coupons.js` 封装 `getAvailableCouponsForBooking(params)`，请求 `/api/v1/coupons/available-for-booking`
- [x] 7.4 修改 `br-app/src/api/bookings.js` 的创建预约调用说明，确保传入对象允许包含 `coupon_id`
- [x] 7.5 确认 `br-app/src/pages/index/index.vue` 的“卡券套餐”入口路径为 `/pages/coupon/index`
- [x] 7.6 执行前端构建：`npm run build:h5`，期望路由注册不报错

## 8. 前端卡券包页面

- [x] 8.1 新增 `br-app/src/pages/coupon/index.vue` 页面骨架，使用现有 uni-app `<view>`、`<scroll-view>`、`<text>` 组件
- [x] 8.2 实现三个页签：可使用、已使用、已过期，默认选中可使用
- [x] 8.3 页签切换时调用 `getCoupons(status)`，加载真实后端数据
- [x] 8.4 实现可使用卡券卡片：白色票券卡、侧边缺口、状态色条、优惠标题、适用范围、有效期、“立即使用”
- [x] 8.5 实现已使用和已过期卡券弱化样式，不展示“立即使用”
- [x] 8.6 实现空状态：暂无可使用的优惠券、暂无已使用的优惠券、暂无已过期的优惠券
- [x] 8.7 实现接口失败状态：展示“卡券加载失败，请重试”并允许重新加载当前页签
- [x] 8.8 对照 `prototype/coupon.html` 调整背景、导航栏、页签、卡片圆角、阴影、按钮和间距
- [x] 8.9 点击“立即使用”时通过 `uni.switchTab({ url: '/pages/booking/index' })` 进入预约 tab
- [x] 8.10 执行 `npm run build:h5`，期望构建成功

## 9. 前端订单确认页选券

- [x] 9.1 修改 `br-app/src/pages/booking/confirm.vue`，导入 `getAvailableCouponsForBooking`
- [x] 9.2 在确认页 `loadData()` 完成座位和门店加载后，请求可用卡券列表
- [x] 9.3 在页面 state 中增加 `availableCoupons`、`selectedCouponId`、`selectedCoupon`、`couponLoading`、`couponLoadError`
- [x] 9.4 新增卡券选择区：展示可用卡券数量、当前选择结果和“不使用卡券”选项
- [x] 9.5 选择卡券后根据后端返回的 `discount_amount` 和 `payable_amount` 更新费用明细
- [x] 9.6 修改费用明细卡片，展示座位费、优惠券抵扣、实付金额
- [x] 9.7 修改底部合计金额，使用选券后的实付金额
- [x] 9.8 修改 `onPay()`，提交预约时携带 `coupon_id`
- [x] 9.9 处理卡券不可用错误：提示“卡券不可用，请重新选择”，清空选择并重新请求可用卡券
- [x] 9.10 修改预约成功弹窗，展示订单编号、预约摘要、原价、抵扣金额、实付金额
- [x] 9.11 执行 `npm run build:h5`，期望构建成功

## 10. 文档与联调验证

- [x] 10.1 更新 `docs/api.md`，新增 `GET /api/v1/coupons` 文档，包含查询参数、响应字段、401
- [x] 10.2 更新 `docs/api.md`，新增 `GET /api/v1/coupons/available-for-booking` 文档，包含查询参数、响应字段、不可用卡券过滤规则
- [x] 10.3 更新 `docs/api.md`，修改 `POST /api/v1/bookings` 文档，记录 `coupon_id`、`original_price`、`discount_amount`、`total_price`、卡券错误响应
- [x] 10.4 更新 `docs/api.md`，修改取消预约文档，记录取消后恢复卡券的首版行为
- [x] 10.5 执行后端验证：`pytest tests/test_coupon_service.py tests/test_api_coupon.py tests/test_api_booking.py -q`
- [x] 10.6 执行前端验证：`cd br-app && npm run build:h5`
- [ ] 10.7 手动验证卡券包：登录用户进入首页，点击“卡券套餐”，切换三个页签，确认接口数据、空状态、错误重试可用
- [ ] 10.8 手动验证下单闭环：订单确认页加载可用卡券，选择卡券后金额变化，提交后订单金额正确，卡券变为已使用
- [ ] 10.9 手动验证取消闭环：取消使用卡券的 confirmed 预约后，卡券恢复为可使用
- [x] 10.10 代码审查：确认卡券规则只在 `coupon_service.py` 实现，前端只展示后端返回的抵扣结果，不信任前端金额
- [x] 10.11 检查 `git diff`，确认变更范围只包含卡券闭环相关文件和既有首页入口修复

## 11. 实施顺序与提交建议

- [ ] 11.1 提交 1：后端卡券模型、迁移、schema
- [ ] 11.2 提交 2：后端卡券 service 和卡券 API
- [ ] 11.3 提交 3：预约下单卡券抵扣和取消恢复
- [ ] 11.4 提交 4：前端卡券 API、路由和卡券包页面
- [ ] 11.5 提交 5：订单确认页选券和金额展示
- [ ] 11.6 提交 6：API 文档、回归验证和清理
