# Proposal: wallet-transaction-room-scope

## 动机

`admin-data-scope` 已让预约管理、评价管理随关联内容创建人过滤（自己拥有 + 存量无创建人 + 超管创建公开）。但存在两处与用户预期不符：

1. **钱包流水完全无归属过滤**：`admin_list_transactions`、`admin_get_statistics`、`export_transactions` 仅按 type/status/user_id/date 筛选，普通用户管理员能看到全平台所有前端用户的充值/消费/退款流水。
2. **预约/评价对「学习室拥有者」不够宽**：现规则下，课程订单/课程评价只看 `Course.created_by`。当普通管理员 A 拥有学习室 R，但课程 X 由另一管理员 B 创建、且 X 在 R 上课/被预约时，A 看不到 R 里发生的这些课程订单与评价——尽管 R 归 A。

用户要求：普通用户（`user_type='normal-user'`）管理员查看这些「前端生成数据」时，主要按「他拥有的学习室」过滤：

- 钱包流水只显示前端用户预约该管理员拥有的学习室的座位或课程所产生的消费/退款流水。
- 预约管理、评价管理：只要学习室归该管理员，即使课程不是他创建的，相关预约与评价记录也应可见。

学习室归属即 `StudyRoom.created_by`（无独立 owner 字段）。

## 目标

1. **预约/评价按学习室归属放宽**：可见 = 关联学习室创建人可见（自己拥有 + 存量空 + 超管公开）**或** 关联课程创建人可见。即学习室拥有者能看到该室发生的全部订单/评价（含他人创建课程产生的），课程创建者仍能看到自己课程的订单/评价（即使在他人的室）。
2. **钱包流水按归属过滤**：交易经 `booking_id → Booking → (StudyRoom | Course).created_by` 回溯，复用放宽后的预约可见性口径，仅保留可见交易。
3. 无关联预约（`booking_id` 为空，如充值 recharge）的流水对非超管**不可见**；超管不受限，查看全部。
4. 不改数据库 schema、不改权限码、不改超管公开/只读规则；口径在预约/评价/钱包三者间完全一致。

## 范围

- br-server：
  - `data_scope.py`：重写 `booking_scope_condition`、`review_scope_condition`（学习室归属 OR 课程创建人）；新增 `wallet_scope_condition`（复用 `booking_scope_condition` + 要求 `booking_id` 非空）。
  - `wallet_service.py`：`admin_list_transactions`/`admin_get_statistics` 加 `viewer` 与 join 过滤。
  - `admin_wallet.py`：list/statistics/export 三端点注入 `get_current_admin` 并传 `viewer`（export 内联 scope+join）。
  - 测试：更新 `test_data_scope.py` 既有预约/评价断言以反映放宽后的预期，新增学习室拥有者跨创建人可见场景与钱包归属测试。
- br-server 预约/评价服务：`admin_list_bookings`、`list_reviews` 已 outerjoin 所需表（Course/StudyRoom/Booking），仅条件函数变化即可生效，无需改 join。
- br-admin：无需改动（服务端强制过滤，API 签名不变）。
- delta spec：MODIFIED `admin-data-scope` 的「Record data follows associated content」需求，移除「钱包流水不做过滤」排除项，更新预约/评价场景为学习室归属口径，新增钱包流水与跨创建人可见场景（保留原两个场景标题）。

## 用户已确认决策

- 无归属流水（充值）对普通用户**不显示**，仅超管可见。
- 超管创建学习室的交易对普通用户**公开可见**，与预约/评价一致。
- 学习室拥有者可见该室发生的他人创建课程的预约/评价（本次扩展）。
- main 分支直接修复验证并提交 github（isolation=current）。