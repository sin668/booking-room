# 验证报告：booking-activity-notifications

- 验证日期：2026-11-25
- 流程：Comet Classic / tweak
- 验证模式：full（含 2 份 delta spec）
- 代码基线：`a6f5f14`，实现提交 `5c33778`
- 独立代码审查：未执行（`review_mode: off`，本 change 在 tweak 预设下未开启独立审查）

## 1. 任务完成度

| 项目 | 结果 |
| --- | --- |
| tasks.md 勾选 | 16/16 全部 `[x]` |
| 证据 | [tasks.md](../../../openspec/changes/booking-activity-notifications/tasks.md) |

## 2. 实现符合 design.md

| 设计要点 | 实现位置 | 结论 |
| --- | --- | --- |
| 三个预约通知方法统一走 `send_notification` 并尊重 `booking` 偏好 | `br-server/app/services/notification_service.py`（`notify_booking_paid` / `notify_booking_start_soon` / `notify_booking_completed` → `_send_booking_notification`） | 一致 |
| 按订单类型生成内容（学习室名称/时段、课程名称/课时时段） | `_booking_message_content` | 一致 |
| `target_type="booking"`，课程提醒 `target_id={订单ID}-{课时ID}`，默认 target_url 为订单列表 | `_send_booking_notification` | 一致 |
| 去重键 `(user_id, type, target_type, target_id, title)` | `_booking_notification_exists` | 一致 |
| 支付成功覆盖余额创建、余额待支付、课程余额创建、微信回调、支付对账 5 个触发点 | `booking_service.py`、`course_booking_service.py`、`booking_payment_service.py` | 一致 |
| 开始提醒：座位 `date+start_time`、课程 `lesson_date+lesson_time_slot`，窗口 `(now, now+15min]` | `order_status_scheduler.py`（`_is_within_reminder_window` / `_lesson_start_at`） | 一致 |
| 完成通知覆盖调度推进、核销确认、读取时懒同步 | `order_status_scheduler.py`、`booking_verification_service.py`、`booking_service.py` | 一致 |
| 活动群发仅在已上架且有关联卡券时触发，App 用户范围 + 偏好过滤，500 条分批 insert，内容去重，失败不阻断保存 | `activity_service.py`（`_broadcast_activity_if_published`，savepoint + 异常日志）、`notification_service.py`（`broadcast_activity`） | 一致 |

## 3. 能力规格场景

### message-notification-api

| 场景 | 实现 | 测试 |
| --- | --- | --- |
| Booking payment succeeded | 5 个支付成功触发点均调用 `notify_booking_paid` | `test_booking_paid_notification_content_and_dedupe`、`test_balance_payment_sends_booking_success` |
| Booking starts within 15 minutes | 座位/课程提醒按窗口判断，课程按课时去重 | `test_seat_start_reminder_only_inside_window`、`test_course_start_reminder_sends_for_due_lesson`、`test_course_start_reminder_uses_lesson_target`、`test_reminder_window_helpers` |
| Booking marked completed | 调度、核销、懒同步三条路径均调用 `notify_booking_completed` | `test_booking_completed_notification`、`test_scheduler_completes_booking_and_notifies` |
| User disabled booking notifications | `send_notification(respect_preferences=True)` | `test_booking_notification_respects_disabled_preference` |
| Duplicate lifecycle event | 发送前去重查询 | `test_booking_paid_notification_content_and_dedupe`、`test_scheduler_completes_booking_and_notifies` |
| Broadcast activity message | `broadcast_activity` 内容与 target_url 语义 | `test_activity_broadcast_scope_and_dedupe` |
| Skip users with disabled activity preference | `activity_enabled` 过滤（无偏好视为开启） | `test_activity_broadcast_scope_and_dedupe` |
| Avoid duplicated broadcast for unchanged activity | title + content + 活动 ID 去重 | `test_activity_broadcast_scope_and_dedupe` |

### activity-admin-api

| 场景 | 实现 | 测试 |
| --- | --- | --- |
| Create published activity with coupons | `create_activity` flush 后调用群发 | `test_activity_save_broadcasts_only_when_published_with_coupons` |
| Update activity to published with coupons | `update_activity` flush 后调用群发 | 同上（更新路径） |
| Save unpublished or coupon-less activity | `is_active` 与关联卡券双重前置判断 | 同上 |
| Broadcast failure does not roll back activity save | `db.begin_nested()` + `logger.exception` 捕获，不影响外层事务 | 代码审查确认（异常路径无自动化测试） |

## 4. proposal 目标

- 支付成功消息：已接入并验证。
- 开始前 15 分钟提醒：已接入并验证。
- 完成/核销消息：已接入并验证。
- 活动上架群发（title=活动标题、content=活动描述、target_url=活动详情）：已接入并验证。
- 偏好过滤与事件去重：已实现并验证。
- 无新增外部 API、无数据库 schema 迁移、前端无改动：与 proposal 一致。

## 5. delta spec 与 design 一致性

两份 delta spec 的验收场景与 design.md 的触发点、去重键、群发范围、事务边界描述一致，未发现矛盾。tweak 预设不生成 `docs/superpowers/specs/` 下的独立 Design Doc（`design_doc: null`），因此 "Design Doc 一致性" 与 "Design Doc 可定位" 两项按不适用处理，以 change 内 design.md 为设计依据。

## 6. 检查与证据

| 检查项 | 结果 | 证据 |
| --- | --- | --- |
| tasks.md 全部完成 | PASS | 16/16 |
| 改动文件与任务描述一致 | PASS | `5c33778` 14 个文件，全部落在任务清单范围内 |
| 构建通过 | PASS | `comet check run ... build --local`（exit=0） |
| 相关测试通过 | PASS | 本次相关测试集 109 passed / 3 skipped；验证证据 `comet check run ... verify --local`（exit=0） |
| 安全问题 | PASS | 无硬编码密钥、无新增 unsafe 操作、无越权数据访问；群发仅写入通知表 |
| 集成代码审查 | SKIPPED | `review_mode: off`（tweak 预设默认），以本报告的场景与设计核对替代 |
| 核心/边界场景 | PASS | 偏好关闭、重复事件、窗口边界（含窗口外不发送）、未上架/无卡券不群发均有测试或代码路径确认 |

## 7. 遗留建议（不影响归档）

- 建议后续为微信回调、支付对账、核销完成、懒同步四条集成路径补充"通知已写入"的断言，当前这些路径由共享方法测试 + 代码审查确认。
- 活动群发异常不阻断保存的路径建议补充一条异常注入测试。
- 提醒窗口依赖 5 分钟调度周期，服务在窗口内宕机会漏发，属于 design 中已记录的可接受降级。

## 结论

PASS — 无 CRITICAL / IMPORTANT 问题，实现与规格、设计一致，可以进入归档。
