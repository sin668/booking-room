## Why

学习统计能力（`study_record_service.get_monthly_summary`）已能聚合本月学习时长、次数、连续天数与累计时长，但用户需要主动进入小程序查看。项目已有订单状态、排课状态等定时任务，但缺少按周触发的学习报告推送，用户无法在固定时间获知本月学习进展。

## What Changes

- 新增每周一执行的学习报告定时任务：读取当月（定时任务运行日期所在月份）的学习统计，通过公共发送消息方法向每个 App 用户发送 `report` 类型通知。
- 通知内容：title 固定为「本月学习报告已生成」，content 为「您本月已累计学习 X 小时，完成学习 N 次，连续学习 D 天，总累计学习 Y 小时。」，target_url 为 `/pages-sub/study-record/index`。
- 定时任务启动开关、星期（默认周一）与运行时间（默认 09:00）写入 `br-server` 配置（`app/core/config.py` 与 `.env.example`），未启用时不注册任务。
- 同一用户同一月份只发送一次（按 `report` + 月份去重），用户关闭 `report` 通知偏好时不发送。
- br-app 通知设置文案调整：`report` 类型由「学习周报 / 每周一推送上周学习总结」改为「学习月报 / 每周一推送本月学习总结」。

## Capabilities

### New Capabilities

无。

### Modified Capabilities

- `message-notification-api`: 新增每月学习报告通知的发送规则（内容模板、目标地址、按月去重、偏好过滤与定时任务配置开关）。

## Impact

- 影响模块：br-server `app/services`（新增 `monthly_study_report_scheduler`、扩展 `notification_service`）、`app/core/config.py`、`app/main.py`、`br-server/.env.example`；br-app `src/pages-sub/utils/notificationTypes.js`。
- API：不新增或变更外部 API。
- 数据库：复用 `notifications` 表，无 schema 迁移；定时任务依赖现有 `bookings`、`study_rooms`、`lesson_schedules` 数据。
- 回滚方案：将 `MONTHLY_STUDY_REPORT_ENABLED` 设为 `false` 即可停止发送；已写入的通知记录可按 `target_type='monthly_study_report'` 清理。
