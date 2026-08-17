# Brainstorm Summary

- Change: course-booking
- Date: 2026-08-17

## 确认的技术方案

1. **数据模型**：扩展 Course 表（custom_price, full_package_price）和 Booking 表（booking_type, course_id, lesson_ids ARRAY, schedule_type），seat_id 改 nullable
2. **服务层**：新建 course_booking_service.py，复用 coupon_service / booking_payment_service / wallet_service
3. **API 路由**：GET /courses/{id}/lessons + POST /course-bookings（独立路由，共享底层服务）
4. **前端**：新建 course-booking.vue 独立页面，复用优惠券弹窗逻辑，订单列表通过 booking_type 条件渲染
5. **价格计算**：fixed=数量×price, custom=数量×custom_price, full_package=full_package_price（全选时触发）

## 关键取舍与风险

- 扩展 bookings 表而非新建表 → 复用订单管理/支付/取消逻辑，降低维护成本
- lesson_ids 用 PostgreSQL ARRAY → 类型安全，查询高效，避免关联表
- 独立 API 路由 → 参数结构完全不同，避免条件分支污染现有 booking 创建逻辑
- seat_id nullable 需保护现有 seat 相关代码路径，通过 booking_type 条件判断

## 测试策略

- 单元测试：价格计算（3 种模式 + 边界）、课时验证
- 集成测试：创建预约（余额/微信）、取消+退款+优惠券恢复、列表混合查询
- 前端：构建验证 + 原型一致性手动验证

## Spec Patch

无
