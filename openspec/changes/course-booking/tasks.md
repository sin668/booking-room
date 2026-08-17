# 课程预约功能 - 任务清单

## 1. 数据库模型与迁移

- [x] Task 1.1: 扩展 Course 模型 — 新增 `custom_price`（Numeric(10,2)）和 `full_package_price`（Numeric(10,2), nullable）字段
- [x] Task 1.2: 扩展 Booking 模型 — 新增 `booking_type`（String(20), default='seat'）、`course_id`（Integer, FK→courses, nullable）、`lesson_ids`（ARRAY(Integer), nullable）、`schedule_type`（String(20), nullable）字段；`seat_id` 改为 nullable
- [x] Task 1.3: 生成 Alembic 迁移文件并验证迁移执行

## 2. 后端 Schema 定义

- [x] Task 2.1: 创建 `app/schemas/course_booking.py` — 定义 `CourseBookingCreate`（course_id, booking_type, lesson_ids, schedule_type, payment_method, coupon_id）、`CourseBookingResponse`、`CourseLessonItem`（id, title, duration_minutes, sort_order, status）
- [x] Task 2.2: 更新 `app/schemas/course.py` — `CourseResponse` 和 `CourseDetailResponse` 增加 `custom_price`、`full_package_price` 字段

## 3. 后端服务层

- [x] Task 3.1: 创建 `app/services/course_booking_service.py` — 实现 `get_course_lessons(course_id)` 查询课时列表
- [x] Task 3.2: 实现 `create_course_booking()` — 验证课程/课时、计算价格（固定/1V1/全套优惠）、验证优惠券、创建 booking 记录、处理余额支付
- [x] Task 3.3: 实现课程预约微信支付集成 — 复用 `booking_payment_service.py` 的微信支付创建和回调逻辑，确保支持 course booking_type
- [x] Task 3.4: 实现课程预约取消 — 复用现有取消退款逻辑，增加优惠券恢复逻辑

## 4. 后端 API 路由

- [x] Task 4.1: 创建 `app/api/routes/course_booking.py` — `GET /api/v1/courses/{course_id}/lessons`（课时列表）、`POST /api/v1/course-bookings`（创建课程预约）
- [x] Task 4.2: 扩展 `app/api/routes/booking.py` — 列表接口返回数据增加 `course_name`、`lesson_titles`、`booking_type` 字段；取消接口支持课程预约优惠券恢复
- [x] Task 4.3: 在 `app/main.py` 注册 course_booking 路由

## 5. 后端测试

- [x] Task 5.1: 编写 `tests/test_course_booking_service.py` — 测试价格计算逻辑（固定/1V1/全套优惠）、课时验证、优惠券验证
- [x] Task 5.2: 编写 `tests/test_api_course_booking.py` — 集成测试课时查询、创建预约（余额/微信）、取消预约

## 6. 前端 API 模块

- [x] Task 6.1: 创建 `br-app/src/api/courseBooking.js` — 封装 `getCourseLessons(courseId)`、`createCourseBooking(data)`、`getCourseBookingCoupons(courseId)` 接口

## 7. 前端课程预约页面

- [x] Task 7.1: 创建 `br-app/src/pages/training/course-booking.vue` — 页面骨架 + 课程信息摘要区域（封面、名称、教师、单价）
- [x] Task 7.2: 实现预约类型切换组件（固定班课/1V1 双列卡片，选中态切换，价格联动）
- [x] Task 7.3: 实现课时多选组件（课时列表、checkbox 选中/取消、已选计数、价格实时更新）
- [x] Task 7.4: 实现全套课时展开功能（"查看全套"推广条、点击全选、优惠价格展示、toast 提示）
- [x] Task 7.5: 实现上课时间展示区域（固定班课时间表 / 1V1 日期时段选择器切换）
- [x] Task 7.6: 实现优惠券选择（复用现有优惠券弹窗逻辑）
- [x] Task 7.7: 实现支付方式选择（余额/微信 radio 切换，余额不足检测）
- [x] Task 7.8: 实现价格摘要与底部操作栏（课程费明细、优惠券抵扣、实付金额、立即支付按钮）
- [x] Task 7.9: 实现下单与支付流程（余额支付直接下单 / 微信支付调起 + 轮询结果 + 成功弹窗 + 跳转订单页）

## 8. 前端订单列表扩展

- [x] Task 8.1: 修改 `br-app/src/pages/orders/index.vue` — 订单卡片根据 `booking_type` 区分渲染：课程预约显示课程名称+课时信息（替代门店名+座位信息）
- [x] Task 8.2: 课程预约订单操作按钮适配（待支付→去支付/取消，已确认→取消/查看课程，已完成→再来一单）

## 9. 前端入口与路由注册

- [x] Task 9.1: 在 `br-app/src/pages.json` 注册 `pages/training/course-booking` 路由
- [x] Task 9.2: 修改 `br-app/src/pages/training/course-detail.vue` — 添加"立即预约"按钮，跳转到课程预约页

## 10. 已知问题规避（参考 bug-fixed.md）

- [x] Task 10.1: 确保 `onMounted` 从 `vue` 导入而非 `@dcloudio/uni-app`（BUG-14）
- [x] Task 10.2: 确保不在 `<style>` 中使用 `@import '@/uni.scss'`（BUG-1）
- [x] Task 10.3: 确保 WXML 中不使用 `<` `>` 字符，使用 Unicode 替代（BUG-20）
- [x] Task 10.4: 确保 API 路由定义不带尾部斜杠（BUG-22）
- [x] Task 10.5: 确保 datetime 字段使用 naive datetime（Asia/Shanghai），不混用 aware/naive（BUG-15）
