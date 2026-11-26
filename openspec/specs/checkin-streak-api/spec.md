# checkin-streak-api Specification

## Purpose
为 br-app 提供连续签到与补签的服务端能力：签到状态汇总、每日签到奖励、补签卡补签，以及按月返回可供日历渲染的签到/漏签标记。
## Requirements
### Requirement: 签到汇总接口

系统 SHALL 提供 `GET /api/v1/checkin/summary` 接口，返回当前用户的签到汇总与指定月份的日历标记。接口 MUST 接受 `month` 查询参数（格式 YYYY-MM），并以 `Asia/Shanghai` 时区的当天日期作为「今日」。

响应 MUST 包含以下字段：
- `today`：服务端判定的今日日期；
- `today_signed`：今日是否已有签到记录；
- `streak`：当前连续签到天数；
- `total_days`：累计签到天数（按去重日期计数，含补签）；
- `points`：累计签到积分；
- `makeup_cards`：剩余补签卡数量；
- `calendar_mark`：指定月份每日标记数组，每项含 `date`、`signed`、`missed`、`makeup_eligible`；
- `missed_dates`：近 30 天内仍可补签的日期列表（升序）。

连续天数口径 MUST 为：若今日已签到，从今日向前连续统计；若今日未签到，从昨日向前连续统计。漏签口径 MUST 为：晚于该用户首次签到日期、早于今日且没有签到记录的日期；`makeup_eligible` MUST 仅在漏签日期距今日不超过 30 天时为真。今日未签到 MUST NOT 计为漏签。

#### Scenario: 查询有签到记录的月份
- **GIVEN** 用户已连续签到 3 天且今日已签到
- **WHEN** 用户请求当月汇总
- **THEN** 返回 200，`today_signed=true`、`streak>=3`、`total_days` 为去重签到日期数
- **AND** `calendar_mark` 覆盖该月每一天，已签到日期 `signed=true`

#### Scenario: 今日未签到但昨日已签到
- **GIVEN** 用户昨日及之前连续签到，今日尚未签到
- **WHEN** 用户请求当月汇总
- **THEN** `today_signed=false`，`streak` 从昨日向前连续统计
- **AND** 今日的 `missed` MUST 为 `false`

#### Scenario: 漏签日期超过补签窗口
- **GIVEN** 用户 40 天前漏签且其后有签到记录
- **WHEN** 用户请求当月汇总
- **THEN** 该日期 `missed=true` 且 `makeup_eligible=false`，不出现在 `missed_dates` 中

#### Scenario: 未登录用户访问
- **WHEN** 未认证用户请求汇总接口
- **THEN** 返回 401 Unauthorized

### Requirement: 每日签到接口

系统 SHALL 提供 `POST /api/v1/checkin` 接口完成今日签到。签到成功 MUST 为今日创建唯一签到记录，并返回最新汇总数据以及本次获得的 `reward_points` 与 `reward_cards`。

奖励口径 MUST 为：每次签到固定 +5 积分；连续天数达到 7 的整数倍时额外 +20 积分；连续天数达到 30 的整数倍时额外 +1 张补签卡。同一用户同一天 MUST 只有一条签到记录，重复签到 MUST 返回 400。

#### Scenario: 今日首次签到
- **GIVEN** 用户今日尚未签到
- **WHEN** 用户调用签到接口
- **THEN** 返回 200，`reward_points=5`，`today_signed=true`，`total_days` 加 1
- **AND** 返回的 `streak` 包含今日

#### Scenario: 连续第 7 天签到
- **GIVEN** 用户昨日已连续签到 6 天且今日未签到
- **WHEN** 用户调用签到接口
- **THEN** `streak=7`，`reward_points=25`（5 + 20 连续奖励）

#### Scenario: 连续第 30 天签到
- **GIVEN** 用户昨日已连续签到 29 天且今日未签到
- **WHEN** 用户调用签到接口
- **THEN** `streak=30`，`reward_cards=1`，`makeup_cards` 加 1

#### Scenario: 重复签到
- **GIVEN** 用户今日已经签到
- **WHEN** 用户再次调用签到接口
- **THEN** 返回 400，且不新增签到记录、不重复发放积分

#### Scenario: 未登录用户签到
- **WHEN** 未认证用户调用签到接口
- **THEN** 返回 401 Unauthorized

### Requirement: 补签接口

系统 SHALL 提供 `POST /api/v1/checkin/makeup` 接口，请求体包含 `dates` 日期数组，使用补签卡为漏签日期补签。补签成功 MUST 为每个日期创建签到记录、按补签日期数量扣减补签卡，并返回最新汇总数据与 `restored_dates`。补签 MUST NOT 发放签到积分与连续奖励。

每个日期 MUST 满足：早于今日、距今日不超过 30 天、晚于或等于用户首次签到日期、当前没有签到记录；`dates` MUST 去重且数量不超过用户剩余补签卡。任一条件不满足 MUST 返回 400，且不产生任何签到记录、不扣减补签卡。补签成功后，连续天数与漏签状态 MUST 按补签后的记录重新计算。

#### Scenario: 使用补签卡补签
- **GIVEN** 用户剩余 2 张补签卡，近 30 天内有 2 天漏签
- **WHEN** 用户提交这 2 个日期补签
- **THEN** 返回 200，`restored_dates` 包含这 2 天
- **AND** `makeup_cards` 减 2，`total_days` 加 2，`points` 不变
- **AND** 这些日期在汇总中 `signed=true`、`missed=false`

#### Scenario: 补签卡不足
- **GIVEN** 用户剩余 1 张补签卡，请求补签 2 个漏签日期
- **WHEN** 用户提交补签
- **THEN** 返回 400
- **AND** 不创建任何签到记录，补签卡余额不变

#### Scenario: 补签窗口外日期
- **GIVEN** 请求日期早于今日 30 天以上，或为今日/未来日期
- **WHEN** 用户提交补签
- **THEN** 返回 400，且不扣减补签卡

#### Scenario: 补签已有记录的日期
- **GIVEN** 请求日期已有签到记录
- **WHEN** 用户提交补签
- **THEN** 返回 400，且不重复扣卡

#### Scenario: 未登录用户补签
- **WHEN** 未认证用户调用补签接口
- **THEN** 返回 401 Unauthorized

### Requirement: 签到统计初始化

系统 SHALL 在用户首次访问签到能力时初始化该用户的签到统计记录，初始积分 MUST 为 0，初始补签卡 MUST 为 2 张（新人礼）。积分与补签卡余额 MUST NOT 小于 0。

#### Scenario: 新用户首次查询
- **GIVEN** 用户从未使用过签到功能
- **WHEN** 用户首次请求签到汇总
- **THEN** 返回 200，`points=0`、`makeup_cards=2`、`total_days=0`、`streak=0`

