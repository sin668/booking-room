# 任务清单

## 1. 配置与通知能力

- [x] 1.1 新增 `MONTHLY_STUDY_REPORT_ENABLED`、`MONTHLY_STUDY_REPORT_DAY_OF_WEEK`、`MONTHLY_STUDY_REPORT_TIME` 配置项并补充 `.env.example`
- [x] 1.2 `NotificationService` 新增 `notify_monthly_study_report`：内容模板、target_url、按用户+月份去重、尊重 `report` 偏好
- [x] 1.3 新增加星期/时间配置解析函数，非法值回退 `mon` / `09:00`

## 2. 定时任务

- [x] 2.1 新增 `monthly_study_report_scheduler.send_monthly_study_reports()`：扫描 App 用户、复用 `get_monthly_summary`、跳过本月无学习用户、单用户异常隔离
- [x] 2.2 `app/main.py` 注册每周 cron 任务（受开关控制）并实现无 APScheduler 的 asyncio 降级循环
- [x] 2.3 新增定时任务与通知单测：内容格式、月份口径、去重、偏好关闭、无学习跳过、配置开关与解析

## 3. 设置页文案

- [x] 3.1 `br-app/src/pages-sub/utils/notificationTypes.js` 将「学习周报 / 每周一推送上周学习总结」改为「学习月报 / 每周一推送本月学习总结」

## 4. 验证与交付

- [x] 4.1 运行 br-server 相关 pytest 与格式检查
- [x] 4.2 检查改动范围与文档一致，确认无新增外部 API 或数据库迁移
- [x] 4.3 提交并推送 GitHub main
