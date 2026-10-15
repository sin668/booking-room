# Delta spec: study-record-api

## MODIFIED Requirements

### Requirement: 学习记录列表 API

系统 SHALL 提供 `GET /api/v1/study-records` 接口，返回当前用户的学习记录分页列表。每条记录 MUST 包含门店名称、座位编号、预约日期、开始时间、结束时间、学习时长（小时）、消费金额。接口 MUST 支持可选 `date` 查询参数（格式 YYYY-MM-DD）按单日过滤记录。默认列表 MUST 同时包含"已学习"（completed）与"未开始"（upcoming）记录，`status` 查询参数可选值 completed/upcoming 时仅返回对应状态；未开始记录来源于已支付的待开始自习室订单与待开始/进行中课程订单中未到日期的课时。

#### Scenario: 分页查询学习记录
- **WHEN** 用户请求 `GET /api/v1/study-records?page=1&page_size=10`
- **THEN** 返回 200，包含 items 数组和分页元数据（total、page、page_size），按日期倒序排列，含已学习与未开始记录

#### Scenario: 按月份筛选记录
- **WHEN** 用户请求 `GET /api/v1/study-records?month=2026-05`
- **THEN** 仅返回记录日期属于该月份的学习记录（含未开始）

#### Scenario: 按单日筛选记录
- **WHEN** 用户请求 `GET /api/v1/study-records?month=2026-05&date=2026-05-12`
- **THEN** 仅返回记录日期等于 2026-05-12 的学习记录，分页元数据的 total 反映过滤后的条数

#### Scenario: 按未开始状态筛选
- **WHEN** 用户请求 `GET /api/v1/study-records?status=upcoming`
- **THEN** 仅返回 status=upcoming 的记录；已学习记录不出现在结果中

#### Scenario: 未登录用户访问
- **WHEN** 未认证用户请求该接口
- **THEN** 返回 401 Unauthorized

### Requirement: 月度统计汇总 API

系统 SHALL 提供 `GET /api/v1/study-records/summary` 接口，返回指定月份的学习统计数据。接口 MUST 接受 `month` 查询参数（格式 YYYY-MM），返回当月学习时长（小时）、当月预约次数、最长连续学习天数、累计学习总时长，以及当月每日学习状态日历标记；calendar_mark 每项 MUST 含 `studied` 与 `upcoming` 两个布尔标记，upcoming 标记该日是否存在未开始的自习室预约或课程课时。统计数值口径保持仅统计已学习记录不变。

#### Scenario: 查询有学习记录的月份
- **WHEN** 用户请求 `GET /api/v1/study-records/summary?month=2026-05`
- **THEN** 返回 200，包含 monthly_hours、monthly_bookings、max_streak_days、total_hours 字段，以及 calendar_mark 数组标记每日学习状态

#### Scenario: 未开始课程课时标记日历
- **WHEN** 用户存在进行中课程订单且某未来日期有未完成课时
- **THEN** 该月份的 calendar_mark 中对应日期 studied=false、upcoming=true

#### Scenario: 查询无学习记录的月份
- **WHEN** 用户请求某月但没有 completed 的预约记录
- **THEN** 返回 200，统计字段均为 0，calendar_mark 为空数组

#### Scenario: 未登录用户访问
- **WHEN** 未认证用户请求该接口
- **THEN** 返回 401 Unauthorized
