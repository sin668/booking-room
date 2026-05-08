## 1. 后端 Admin Schemas

- [x] 1.1 在 `br-server/app/schemas/booking.py` 末尾新增 `BookingAdminResponse` schema，复用现有 `SeatBrief`、`RoomBrief`，包含 id、user_id、room_id、seat_id、date、start_time、end_time、status、total_price、created_at、updated_at、seat、room 字段。参考 `br-server/app/schemas/activity.py:34` 的 `ActivityAdminResponse` 模式（含 updated_at）
- [x] 1.2 新增 `BookingAdminListResponse` schema，含 items（list[BookingAdminResponse]）、total、page、page_size 字段。参考 `br-server/app/schemas/activity.py:48` 的 `ActivityListResponse` 模式

## 2. 后端 Admin Service

- [x] 2.1 在 `br-server/app/services/booking_service.py` 末尾新增 `admin_list_bookings(db, page, page_size, status, room_id, date_start, date_end)` 方法。构建筛选条件：可选 status、room_id、date_start <= date <= date_end。参考现有 `list_bookings` 的分页模式（复用 `MAX_PAGE_SIZE`、`DEFAULT_PAGE_SIZE` 常量），返回 `BookingAdminListResponse`
- [x] 2.2 新增 `admin_get_booking(db, booking_id)` 方法，无 user_id 限制，直接按 id 查询，关联 seat 和 room 信息，返回 `BookingAdminResponse`。不存在抛 `BookingNotFoundError`
- [x] 2.3 新增 `admin_cancel_booking(db, booking_id)` 方法，检查状态为 confirmed 后改为 cancelled，关联 seat 和 room 返回 `BookingAdminResponse`。已取消抛 `BookingAlreadyCancelledError`，不存在抛 `BookingNotFoundError`

## 3. 后端 Admin 路由

- [x] 3.1 创建 `br-server/app/api/routes/admin_booking.py`。参考 `br-server/app/api/routes/admin_activity.py` 的完整模式：router 前缀 `/api/v1/admin/bookings`，`dependencies=[Depends(get_current_admin)]`。定义三个路由：GET `/`（列表，查询参数 page/page_size/status/room_id/date_start/date_end）、GET `/{booking_id}/`（详情）、POST `/{booking_id}/cancel/`（取消）
- [x] 3.2 在 `br-server/app/main.py` 的 import 区域（约第 9-20 行）新增 `from app.api.routes.admin_booking import router as admin_booking_router`，在路由注册区域（约第 57 行附近）新增 `app.include_router(admin_booking_router)`

## 4. 后端测试

- [x] 4.1 创建 `br-server/tests/test_admin_booking_service.py`，编写 `admin_list_bookings` 的单元测试：正常分页、按 status 筛选、按 room_id 筛选、按日期范围筛选、空结果。使用 pytest + async mock
- [x] 4.2 创建 `br-server/tests/test_admin_booking_api.py`，编写 API 集成测试：无 token 返回 401、列表正常返回 200、详情正常返回 200、详情不存在返回 404、取消 confirmed 订单返回 200、取消已取消订单返回 400、取消不存在订单返回 404

## 5. 前端 API 层

- [x] 5.1 创建 `br-admin/src/api/booking/index.ts`。参考 `br-admin/src/api/activity/index.ts` 的完整模式：定义 `adminMeta`（ignoreToken + isReturnNativeResponse）、`getAdminHeaders()`（X-Admin-Token）、类型接口 `BookingItem`/`BookingListParams`、API 函数 `getBookingList`/`getBookingDetail`/`cancelBooking`。注意：loadDataTable 中需要 snake_case → camelCase 转换

## 6. 前端订单列表页面

- [x] 6.1 创建 `br-admin/src/views/booking/list/index.vue`。参考 `br-admin/src/views/activity/list/index.vue` 的页面结构：BasicForm 筛选区域 + BasicTable 数据表格。表单 schema 包含：status（NSelect，选项 confirmed/cancelled）、room_id（NSelect，从自习室列表获取）、date_start/date_end（NDatePicker 范围选择）
- [x] 6.2 实现表格 columns 定义：id、user_id（截断显示）、room.name（自习室名称）、seat.seat_number（座位编号）、date（预约日期）、start_time~end_time（时段）、total_price（金额）、status（NTag 颜色标签：confirmed=success/已确认，cancelled=error/已取消）、created_at（创建时间）、操作列（Dropdown：查看详情、取消）。无新建/编辑按钮
- [x] 6.3 实现取消操作：点击取消 → dialog.confirm 确认（提示"确定要取消该订单吗？取消后不可恢复"）→ 调用 `cancelBooking` API → 成功后 `actionRef.value?.reload()` 刷新列表

## 7. 前端路由与导航

- [x] 7.1 创建 `br-admin/src/router/modules/booking.ts`。参考 `br-admin/src/router/modules/activity.ts`：path `/booking`，name `Booking`，title `订单管理`，icon 使用 FileTextOutlined 或类似图标，sort 取合理值（如 4），子路由 `list` 指向 `@/views/booking/list/index.vue`
- [x] 7.2 路由模块放入 `br-admin/src/router/modules/` 目录后会被自动扫描注册到侧边栏导航，无需额外配置

## 8. 文档与代码审查

- [x] 8.1 更新 `docs/api.md`，在 Admin API 部分补充订单管理三个接口的文档：GET /api/v1/admin/bookings/（列表）、GET /api/v1/admin/bookings/{id}/（详情）、POST /api/v1/admin/bookings/{id}/cancel/（取消）。包含请求参数、响应格式、状态码说明
- [x] 8.2 代码审查：确认 schema/service/route 三层职责清晰，与 admin_activity/admin_room 模式一致，无重复代码，无未使用的 import
