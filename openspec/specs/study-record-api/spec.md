# study-record-api Specification

## Purpose

提供自习室与培训课程的学习记录后端接口：月度统计汇总与学习记录分页列表，支持按月、按单日与按状态过滤。
## Requirements
### Requirement: 月度统计汇总 API

系统 SHALL 提供 `GET /api/v1/study-records/summary` 接口，返回指定月份的学习统计数据。接口 MUST 接受 `month` 查询参数（格式 YYYY-MM），返回当月学习时长（小时）、当月预约次数、最长连续学习天数、累计学习总时长，以及当月每日是否学习的日历标记数据。

#### Scenario: 查询有学习记录的月份
- **WHEN** 用户请求 `GET /api/v1/study-records/summary?month=2026-05`
- **THEN** 返回 200，包含 monthly_hours、monthly_bookings、max_streak_days、total_hours 字段，以及 calendar_mark 数组标记每日学习状态

#### Scenario: 查询无学习记录的月份
- **WHEN** 用户请求某月但没有 completed 的预约记录
- **THEN** 返回 200，统计字段均为 0，calendar_mark 为空数组

#### Scenario: 未登录用户访问
- **WHEN** 未认证用户请求该接口
- **THEN** 返回 401 Unauthorized

### Requirement: 学习记录列表 API

系统 SHALL 提供 `GET /api/v1/study-records` 接口，返回当前用户的学习记录分页列表。每条记录 MUST 包含门店名称、座位编号、预约日期、开始时间、结束时间、学习时长（小时）、消费金额。接口 MUST 支持可选 `date` 查询参数（格式 YYYY-MM-DD）按单日过滤记录。

#### Scenario: 分页查询学习记录
- **WHEN** 用户请求 `GET /api/v1/study-records?page=1&page_size=10`
- **THEN** 返回 200，包含 items 数组和分页元数据（total、page、page_size），按日期倒序排列

#### Scenario: 按月份筛选记录
- **WHEN** 用户请求 `GET /api/v1/study-records?month=2026-05`
- **THEN** 仅返回该月份的 completed 预约记录

#### Scenario: 按单日筛选记录
- **WHEN** 用户请求 `GET /api/v1/study-records?month=2026-05&date=2026-05-12`
- **THEN** 仅返回记录日期等于 2026-05-12 的学习记录，分页元数据的 total 反映过滤后的条数

#### Scenario: 未登录用户访问
- **WHEN** 未认证用户请求该接口
- **THEN** 返回 401 Unauthorized

