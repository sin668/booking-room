# Tasks: wallet-transaction-room-scope

## 1. data_scope 条件函数

- [x] 1.1 重写 `booking_scope_condition`：学习室归属 OR（课程订单且课程创建人可见）
- [x] 1.2 重写 `review_scope_condition`：学习室归属 OR（有课程且课程创建人可见）
- [x] 1.3 新增 `wallet_scope_condition`：`booking_id` 非空 + 复用 `booking_scope_condition`

## 2. 钱包服务与端点

- [ ] 2.1 `wallet_service.admin_list_transactions` 加 `viewer` 参数与 outerjoin（Booking/Course/StudyRoom）+ scope 过滤（count 与 list）
- [ ] 2.2 `wallet_service.admin_get_statistics` 加 `viewer` 参数与 outerjoin + scope 过滤（分组统计与活跃用户）
- [ ] 2.3 `admin_wallet.py` list/statistics/export 三端点注入 `get_current_admin` 并传 `viewer`；export 内联 scope+join

## 3. 测试

- [x] 3.1 更新 `test_data_scope.py` 既有预约/评价断言（B 拥有 room_b → 可见 booking_course/review_course）
- [x] 3.2 新增「学习室拥有者跨创建人可见」预约/评价测试
- [ ] 3.3 新增钱包归属测试（PERMS 加 wallet:view）：拥有学习室消费/退款可见、充值隐藏、他人学习室不可见、存量/超管公开、超管全部、统计/导出同口径
- [ ] 3.4 运行 test_data_scope.py 全绿；全量 pytest 对照 19 基线零回归

## 4. 验证与归档

- [ ] 4.1 full 验证（delta spec 一致性 + 场景映射）并出验证报告
- [ ] 4.2 真实环境冒烟（普通管理员钱包/预约/评价按学习室归属，超管全部）
- [ ] 4.3 归档确认（A/B/C/D/E）并按授权提交推送 github