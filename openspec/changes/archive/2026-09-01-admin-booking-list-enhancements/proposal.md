# Proposal: admin-booking-list-enhancements

## 动机

br-admin `/booking/list` 预约列表页面目前只覆盖自习室（座位）预约场景，信息展示与操作能力不足以支持课程预约订单的管理：

1. "查看"按钮仅弹出一行文本，无法查看订单与关联表（用户、课程、排课、课时、优惠券、退款流水等）的完整信息；
2. 自习室预约订单不应提供"取消"按钮（取消由用户侧流程处理），但目前对所有待开始订单显示取消；
3. 课程预约订单的"时段"列显示 `start_time~end_time`（定制订单该字段为下单时间，无意义），应展示 `time_slots` 的周几+时间段格式；
4. 课程预约"待开始"订单缺少管理员取消能力（全额退款 + 清理订单专属排课数据）。

## 目标

1. 查看弹窗升级为详情弹窗：分类展示订单及关联表（users、study_rooms、seats、courses、teachers、course_schedules、lesson_schedules、coupons、wallet_transactions）尽可能多的信息。
2. 自习室预约类型订单操作列不显示"取消"按钮。
3. 课程预约订单"时段"列展示 `time_slots`，格式如"周三 10:00-12:00、周六 12:00-14:00"。
4. 课程预约"待开始"订单（`booking_type='course'`，状态 `pending`/`pending_confirm` 且已支付）可通过"取消"操作：状态变为 `cancelled`、全额退款、删除订单专属的 `course_schedules` 与 `lesson_schedules` 记录。

## 范围

- **br-server**: `app/schemas/booking.py`（响应模型扩展）、`app/services/booking_service.py`（详情聚合、课程订单取消分支）、`app/api/routes/admin_booking.py`（详情路由响应模型）
- **br-admin**: `src/api/booking/index.ts`（类型与接口）、`src/views/booking/list/builders.ts`（列定义）、`src/views/booking/list/index.vue`（操作与详情弹窗）、新增详情弹窗组件
- **测试**: `br-server/tests/test_admin_booking_service.py` 回归与新增用例

## 不在范围

- 用户侧（br-app）取消流程变更
- 自习室订单退款策略调整
- 排课管理页面（training/courses）功能变更
