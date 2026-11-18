# 验证报告：wallet-transaction-room-scope

- 日期：2026-11-18
- 工作流：Comet Classic tweak（isolation=current，绑定分支 main）
- 验证模式：full（delta spec 1 个：admin-data-scope；规模评估 tasks=11 / deltaSpecs=1 / changedFiles=12 → full）
- 审查模式：standard（独立集成审查，见 §4）
- 基线：8be34356（archive super-admin-data-readonly）→ HEAD 6318ad9
- 产物语言：zh-CN

## 1. 摘要记分卡

| 维度 | 结果 |
| --- | --- |
| Completeness | 11/11 tasks 勾选；1/1 MODIFIED requirement 已实现 |
| Correctness | 5/5 delta spec 场景覆盖（单测 + 真实环境冒烟）；全量 pytest 零回归 |
| Coherence | 实现与 change design.md 一致；delta spec 与 design.md 无矛盾；tweak 无 Superpowers Design Doc（以 change design.md 为准） |

结论：**全部检查通过，无 CRITICAL/IMPORTANT 问题**。2 项非 CRITICAL 偏差经用户确认接受并记录（§5）。可进入归档。

## 2. 完整性与改动对照

- tasks.md：11/11 `[x]`（1.1–1.3 条件函数；2.1–2.3 钱包服务/端点；3.1–3.4 测试；4.1 真实环境冒烟）。
- 交付源码/测试 6 文件（`git diff --stat 8be34356...6318ad9 -- br-server/app br-server/tests`，+261/−56），与 tasks 描述一致：
  - br-server/app/services/data_scope.py（+32/−）
  - br-server/app/services/wallet_service.py（+89/−）
  - br-server/app/api/routes/admin_wallet.py（+40/−）
  - br-server/tests/test_data_scope.py（+142/−）
  - br-server/tests/test_wallet_service.py（+13/−）
  - br-server/tests/test_admin_wallet_api.py（+1）
- 未改数据库 schema、权限码、超管公开/只读规则、readonly 归属判定；br-admin 无改动（服务端强制过滤）。
- delta spec 校验：`comet classic openspec -- validate wallet-transaction-room-scope` → valid。

## 3. 正确性：需求与场景映射（5/5）

需求「Record data follows associated content」（MODIFIED）实现证据：

- 统一可见性 `_visible_creator_condition` = created_by IS NULL（legacy）OR == viewer.admin_id（自有）OR IN 超管 id 子查询（公开）：data_scope.py:35-42；`_unrestricted`（None/超管/legacy int=0）：data_scope.py:45-46。
- 预约 = 学习室归属 OR（course_id 非空 AND 课程创建人可见）：data_scope.py:127-145；调用方 outerjoin Course/StudyRoom：booking_service.py:943,952,955（list+count）、1049,1051（detail）。
- 评价 = 学习室归属 OR（course_id 非空 AND 课程创建人可见）：data_scope.py:148-166；调用方 outerjoin Course/Booking/StudyRoom：admin_review_service.py:110,121-128（list+count）。
- 钱包 = booking_id 非空 AND 复用预约可见性：data_scope.py:169-182；wallet_service.admin_list_transactions（618-702）/admin_get_statistics（705-762）加 viewer + `_wallet_scope_joins`（111-117）；admin_wallet.py 三端点注入 get_current_admin（45,70,93），export 内联 scope+join（113-140）。

| # | 场景 | 单测证据 | 真实环境冒烟证据 |
| --- | --- | --- | --- |
| 1 | Booking visibility by associated content | test_data_scope.py test_booking_follows_associated_content（B={booking_course,booking_seat,booking_legacy}） | 普通管理员 bookings：R_owned=[123,124]、R_super=[125]、R_other=[]；超管含 R_other=[126] |
| 2 | Review visibility by associated content | test_review_follows_associated_content（B={review_course,review_seat}） | 普通管理员 reviews 共 2 条（9,10 均可见）；超管共 10 条含 9,10 |
| 3 | Room owner sees cross-created course records | test_data_scope.py:303 test_room_owner_sees_cross_created_course_records | 预约 124（课程「冒烟他人课程」由 B 创建、开设于 A 自有室）对 A 可见；评价 9（同课程）对 A 可见 |
| 4 | Wallet transactions follow room ownership | test_data_scope.py:742/764/775/792（list/recharge/statistics/export） | 普通管理员 wallet list 共 4 条（consume_owned/refund_owned/consume_course/consume_super），consume_other 与 recharge 不可见；statistics recharge=0/consume=60/refund=5/total=4；export 5 行无「钱包充值」 |
| 5 | Super admin sees all records | 各测试 super 断言（wallet 6 条含 recharge） | 超管 wallet list 6 条含 recharge；statistics recharge=250/total=118；export 7 行含「钱包充值」；bookings/reviews 全量 |

列表/统计/导出三者口径一致（场景 4 AND 条款）：单测 test_wallet_statistics_scope / test_wallet_export_scope + 冒烟三者数值互相吻合（4 条 / consume60+refund5 / 5 行）。

## 4. 集成代码审查（独立 reviewer，standard）

- 审查者：独立 general-purpose subagent（非实现者），输入=最终 diff 8be34356...6318ad9 + tasks/delta spec/design + 调用方/模型/认证依赖；并自行运行触及测试（47 passed）。
- 结论：**PASS，无 CRITICAL/IMPORTANT**。
- 核实要点：scope SQL 与 spec 一致；wallet 三端点均服务端注入 viewer（未认证 401，HTTP 下 viewer 不会为 None）；Tx→Booking→Course/StudyRoom 皆多对一主键 join，无行扇出，COUNT/SUM 与 count(distinct user_id) 不会重复计数；UUID 批量映射跨 SQLite/PostgreSQL 正确、缺失 id 降级 (None,None) 不崩溃；测试断言精确可见 id 集合，功能回退即失败；无硬编码密钥/unsafe 操作。
- 非 CRITICAL findings 见 §5（用户已确认接受）。

## 5. 接受的非 CRITICAL 偏差（用户决策：接受并记录，2026-11-18）

1. **WARNING — 删除学习室后的 legacy 公开面**：`Booking.room_id` 无外键（models/booking.py:17），`delete_room` 仅拦截进行中订单（study_room_service.py:234）。学习室被硬删除后 outerjoin 得 `StudyRoom.created_by IS NULL`，其历史预约/评价/钱包流水按 legacy 对所有普通管理员公开；本次放宽使他人创建课程的记录也落入该口径。
   - 接受原因：与 delta spec 字面「创建人为空=legacy 公开」一致，属删除学习室后历史数据的边缘场景；座位订单的该行为在本次变更前已存在。收紧将改变已确认的 legacy 口径（范围/行为取舍），超出本次需求。
   - 影响范围：仅「学习室被硬删除且留有历史已完成订单」时，相关历史记录对普通管理员可见性放宽；不影响正常存续学习室的归属过滤与充值隐藏。
2. **SUGGESTION — 统计/昵称断言补强**：test_data_scope.py:786-799 统计单测未断言 active_users；无自动化真实库测试断言非空昵称/手机号。
   - 接受原因：真实环境冒烟已断言 normal statistics active_users=1、wallet list user_nickname=「冒烟学员」/user_phone=13900008881（非空），覆盖该回归面；补自动化断言属 nice-to-have，留待后续。
   - 影响范围：仅测试断言密度，不影响运行时正确性。

## 6. 回归与构建/验证证据

- 全量 pytest（br-server，`.venv/bin/python -m pytest -q`，2026-11-18 复跑）：**19 failed / 1100 passed / 16 skipped**（88.44s）。19 个失败恰为存量基线（test_models_import 3、test_coupon_service 8、test_im_callback_sync 5、test_admin_user_management 1、test_activity_coupon_campaign 2），**零回归**；1100 = 基线 1095 + 新增 5。
- Build 证据：`comet check run ... build --local -- .venv/bin/python -m pytest tests/test_data_scope.py -q` → exit=0，log `.comet/checks/9cd987d1-….log`（cwd br-server）。
- Verify 证据：`comet check run ... verify --local -- .venv/bin/python -m pytest tests/test_data_scope.py -q` → exit=0，**28 passed**，log `.comet/checks/c26e3176-4802-4862-9168-031e2d6acbb3.log`（cwd br-server）。
- 触及单测合计：test_data_scope 28 + test_wallet_service 18 + test_admin_wallet_api 1 = 47 passed（reviewer 复跑一致）。

## 7. 真实环境冒烟（task 4.1，PostgreSQL + 独立 CDP Chrome）

- 种子：临时普通管理员 A（拥有 R_owned）、超管（R_super 公开）、临时普通管理员 B（R_other + 在 R_owned 创建课程 C_B）、前端学员 U；4 预约 / 2 评价 / 6 流水（含 recharge 无 booking_id）。
- API 断言（/tmp/wallet-smoke-evidence-api.json、-reviews.json）：见 §3 表；昵称/手机号映射在真实 PostgreSQL 正确返回。
- 前端渲染（CDP 截图 /tmp/wallet-cdp-normal.png、-booking.png、-review.png）：
  - 钱包流水页（普通管理员）：统计卡 钱包充值¥0.00 / 预约消费¥60.00 / 预约退款¥5.00 / 净收入¥55.00；表格共 4 条（−20 公开室消费、+5 退款、−10 自有室消费、−30 跨创建课程消费），无充值、无他人室 −15。
  - 预约列表页：共 3 条（125 超管室只读置灰、124 课程「冒烟他人课程」、123 自有室），无 126。
  - 评价审核页：共 2 条（10 座位评价、9 跨创建课程评价）。
- 清理：冒烟后按 FK 顺序删除 6 流水/2 评价/4 预约/1 课程/3 学习室/3 用户/1 角色；复查 users/roles/rooms/courses/reviews/bookings 残留均 0。

## 8. 最终评估

全部检查通过：11/11 tasks、5/5 场景、零回归、构建/验证证据 exit=0、独立集成审查 PASS、真实环境冒烟通过。2 项非 CRITICAL 偏差经用户确认接受并记录（§5）。无 CRITICAL/IMPORTANT。**可进入归档。**