## ADDED Requirements

### Requirement: 管理员查询交易流水
系统 SHALL 提供 `GET /api/v1/admin/wallet/transactions` 接口，允许管理员查询所有用户的交易流水。支持以下筛选参数：`page`、`page_size`、`type`（recharge/consume/refund）、`status`（pending/completed/failed/cancelled）、`user_id`、`date_start`、`date_end`。该接口需要 `wallet:view` 权限。

#### Scenario: 按类型筛选交易流水
- **WHEN** 管理员请求 `GET /api/v1/admin/wallet/transactions?type=recharge`
- **THEN** 系统返回交易类型为 recharge 的流水列表，包含分页信息

#### Scenario: 按时间范围筛选
- **WHEN** 管理员请求 `GET /api/v1/admin/wallet/transactions?date_start=2026-05-01&date_end=2026-05-25`
- **THEN** 系统返回该时间范围内的交易流水

#### Scenario: 按用户筛选
- **WHEN** 管理员请求 `GET /api/v1/admin/wallet/transactions?user_id=xxx`
- **THEN** 系统返回该用户的交易流水

#### Scenario: 无权限访问
- **WHEN** 未持有 `wallet:view` 权限的用户请求该接口
- **THEN** 系统返回 403 Forbidden

### Requirement: 管理员获取财务统计概览
系统 SHALL 提供 `GET /api/v1/admin/wallet/statistics` 接口，返回核心财务指标：总充值金额、总消费金额、总退款金额、平台净收入（总消费 - 总退款）、有交易记录的用户数、总交易笔数。支持 `date_start` 和 `date_end` 可选参数限定统计范围。该接口需要 `wallet:view` 权限。

#### Scenario: 获取全部时间统计
- **WHEN** 管理员请求 `GET /api/v1/admin/wallet/statistics`（不带时间参数）
- **THEN** 系统返回所有时间的累计财务统计数据

#### Scenario: 获取指定时间范围统计
- **WHEN** 管理员请求 `GET /api/v1/admin/wallet/statistics?date_start=2026-05-01&date_end=2026-05-25`
- **THEN** 系统返回该时间范围内的财务统计数据

### Requirement: 导出交易流水 CSV
系统 SHALL 提供 `GET /api/v1/admin/wallet/transactions/export` 接口，按当前筛选条件导出交易流水为 CSV 文件。支持相同的筛选参数（`type`、`status`、`user_id`、`date_start`、`date_end`）。单次导出上限 10000 条记录。该接口需要 `wallet:export` 权限。

#### Scenario: 成功导出
- **WHEN** 管理员请求 `GET /api/v1/admin/wallet/transactions/export?type=recharge&date_start=2026-05-01`
- **THEN** 系统返回 CSV 文件，Content-Type 为 `text/csv`，包含筛选后的交易记录

#### Scenario: 超出导出上限
- **WHEN** 筛选结果超过 10000 条记录
- **THEN** 系统返回 400 错误，提示用户缩小筛选范围
