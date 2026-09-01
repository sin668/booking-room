# Tasks: admin-booking-list-enhancements

## 后端（br-server）

- [x] 1. `app/schemas/booking.py`：`BookingAdminResponse` 增加 `booking_type`/`schedule_type`/`time_slots` 字段；新增 `BookingAdminDetailResponse` 及关联信息子模型（user/course/teacher/schedule/lesson/coupon/refund_transaction）
- [x] 2. `app/services/booking_service.py`：`_build_admin_booking_response` 补充新字段；`admin_get_booking` 聚合关联表数据返回详情响应（手动逐表查询，不返回懒加载 ORM 对象）
- [x] 3. `app/services/booking_service.py`：`admin_cancel_booking` 新增课程预约待开始分支——全额退款（含优惠券恢复、退款流水）+ 删除订单专属排课（先清 bookings.schedule_id 外键引用，再删 lesson_schedules 与 course_schedules；共享排课保留）
- [x] 4. `app/api/routes/admin_booking.py`：详情路由 `response_model` 切换为 `BookingAdminDetailResponse`
- [x] 5. `tests/test_admin_booking_service.py`：新增/更新用例——详情聚合字段、课程待开始取消全额退款与排课删除、共享排课保留；运行测试确认通过

## 前端（br-admin）

- [x] 6. `src/api/booking/index.ts`：扩展 `BookingItem` 类型（booking_type/schedule_type/time_slots）与 `BookingDetail` 详情类型；`getBookingDetail` 返回详情类型
- [x] 7. `src/views/booking/list/builders.ts`：新增预约类型列；时段列课程订单按 `time_slots` 格式化为"周几 HH:MM-HH:MM、…"（兼容 dict/字符串/start-end 三种格式）
- [x] 8. 新增 `src/views/booking/list/BookingDetailModal.vue`：详情弹窗，分类展示订单与关联表信息（确认所用 Naive UI 组件已在 `plugins/naive.ts` 注册，参照 BUG-23）
- [x] 9. `src/views/booking/list/index.vue`："查看"打开详情弹窗；取消按钮仅对课程预约且状态 `pending`/`pending_confirm` 显示；取消文案提示全额退款与排课清理

## 验证与提交

- [x] 10. 后端运行 `pytest tests/test_admin_booking_service.py tests/test_admin_booking_api.py -q`；前端执行构建（`pnpm build`）确认无错误
- [ ] 11. 提交代码并推送 GitHub（main 分支），提交信息 `tweak: ...`
