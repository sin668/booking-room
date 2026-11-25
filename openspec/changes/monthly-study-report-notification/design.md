## 设计概述

复用现有两条定时任务（订单状态 `interval`、排课状态 `cron`）的注册与降级模式，新增一个每周运行的 `cron` 任务；报告数据直接复用 `study_record_service.get_monthly_summary`，消息统一经 `NotificationService` 公共发送方法创建，避免重复实现统计与偏好过滤。

## 实现要点

### 1. 配置项（`br-server/app/core/config.py` + `.env.example`）

- `MONTHLY_STUDY_REPORT_ENABLED: bool = True`：定时任务启动开关，未启用时既不注册 APScheduler 任务，也不启动 asyncio 降级循环。
- `MONTHLY_STUDY_REPORT_DAY_OF_WEEK: str = "mon"`：执行星期，取值 `mon`~`sun`。
- `MONTHLY_STUDY_REPORT_TIME: str = "09:00"`：执行时间（HH:MM，Asia/Shanghai）。

新增解析函数 `_parse_monthly_study_report_schedule()`：校验星期与时间，非法值回退到 `mon` / `09:00` 并记录 warning，与 `_parse_schedule_status_check_time` 的处理方式一致。

### 2. 通知服务方法（`notification_service.py`）

`notify_monthly_study_report(user_id, month, summary)`：

- 去重键：`(user_id, type='report', target_type='monthly_study_report', target_id='YYYY-MM', title)`
- title「本月学习报告已生成」
- content「您本月已累计学习 {monthly_hours:.2f} 小时，完成学习 {monthly_bookings} 次，连续学习 {max_streak_days} 天，总累计学习 {total_hours:.2f} 小时。」
- target_url `/pages-sub/study-record/index`
- 经 `send_notification(respect_preferences=True)` 创建，尊重 `report_enabled` 偏好。

### 3. 定时任务（新增 `app/services/monthly_study_report_scheduler.py`）

`send_monthly_study_reports()`：

- 取 `booking_now(settings.BOOKING_TIMEZONE).date()` 作为运行日期，月份即「本月」。
- 查询 `user_source='app'` 且状态非 `deleted` 的用户。
- 对每个用户调用 `get_monthly_summary(db, user_id, today)`；`monthly_bookings == 0` 时跳过（本月无已完成学习不发零值报告）。
- 有学习记录时调用 `notify_monthly_study_report`，同一月份重复运行由去重查询保证只发一次。
- 单用户异常记录日志后继续处理其他用户，整体 `commit`。
- 返回统计 `{total_scanned, sent, skipped, failed}` 供任务日志输出。

### 4. 任务注册（`app/main.py`）

- APScheduler：启用时注册 `cron` 任务，`day_of_week` / `hour` / `minute` 来自配置，`timezone=Asia/Shanghai`，`id="monthly_study_report"`，`replace_existing=True`。
- 无 APScheduler 的降级模式：新增 `_monthly_study_report_loop()`，按配置计算下一次运行的星期与时间后 `asyncio.sleep`，与 `_schedule_status_check_loop` 同构；开关关闭时不创建任务。
- 启动日志输出实际生效的星期与时间。

### 5. 设置页文案（`br-app/src/pages-sub/utils/notificationTypes.js`）

`report` 类型：`settingLabel` 改为「学习月报」，`settingDescription` 改为「每周一推送本月学习总结」。

## 风险与取舍

- 逐用户聚合统计在用户量大时耗时线性增长，当前规模可接受；后续可改为批量查询或异步队列。
- 每周一运行一次，服务在该时点宕机会漏发当月报告；与现有定时任务一致的降级口径。
- 本月无已完成学习的用户不发送，避免零值消息打扰；如需全员提醒可后续调整。
