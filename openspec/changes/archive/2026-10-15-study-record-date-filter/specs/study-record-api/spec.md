# Delta spec: study-record-api

## MODIFIED Requirements

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
