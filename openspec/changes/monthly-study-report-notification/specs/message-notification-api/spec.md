## ADDED Requirements

### Requirement: Monthly study report notification

br-server SHALL provide a scheduled job that sends each App user a `report` type notification with their current-month study summary every Monday, and SHALL respect the user's `report_enabled` preference.

#### Scenario: Send current month report on Monday

- **GIVEN** 定时任务已启用，运行日期为某周一
- **WHEN** 定时任务扫描到本月存在已完成学习记录的 App 用户
- **THEN** br-server SHALL 通过公共发送消息方法为该用户创建一条 `report` 通知
- **AND** 通知标题 SHALL 为「本月学习报告已生成」
- **AND** 通知 `target_url` SHALL 为 `/pages-sub/study-record/index`
- **AND** 报告统计月份 SHALL 为定时任务运行日期所在月份

#### Scenario: Report content follows study summary

- **GIVEN** 用户在当月的学习统计为已学习小时数、完成次数、连续天数与累计小时数
- **WHEN** br-server 生成学习报告消息
- **THEN** 通知 content SHALL 为「您本月已累计学习 {小时} 小时，完成学习 {次数} 次，连续学习 {天数} 天，总累计学习 {累计小时} 小时。」
- **AND** 小时数 SHALL 保留两位小数

#### Scenario: Skip duplicate report for the same month

- **GIVEN** 同一用户在当月已收到过「本月学习报告已生成」通知
- **WHEN** 定时任务重复执行
- **THEN** br-server SHALL NOT 重复创建该月份的学习报告通知

#### Scenario: Skip user with disabled report preference

- **GIVEN** 用户已关闭 `report` 通知偏好
- **WHEN** 定时任务为该用户生成学习报告
- **THEN** br-server SHALL NOT 为该用户创建学习报告通知

#### Scenario: Skip user without completed study this month

- **GIVEN** 用户本月没有任何已完成学习记录
- **WHEN** 定时任务扫描到该用户
- **THEN** br-server SHALL NOT 创建学习报告通知

#### Scenario: Scheduled job disabled by configuration

- **GIVEN** 配置项 `MONTHLY_STUDY_REPORT_ENABLED` 为关闭状态
- **WHEN** 服务启动
- **THEN** br-server SHALL NOT 注册学习报告定时任务
- **AND** SHALL NOT 发送学习报告通知
