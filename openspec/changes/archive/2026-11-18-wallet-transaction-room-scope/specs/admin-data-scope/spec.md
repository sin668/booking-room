# admin-data-scope Delta Spec

## MODIFIED Requirements

### Requirement: Record data follows associated content
预约、评价与钱包流水 SHALL 随关联内容归属过滤，口径统一为「关联学习室创建人可见 或 关联课程创建人可见」：

- 预约：所有订单都有所属学习室。学习室创建人可见（自己拥有、创建人为空、创建人当前为超级管理员）的订单全部可见；此外课程订单（`course_id` 非空）在课程创建人可见时也可见。即学习室拥有者可见该室发生的全部订单（含他人创建课程产生的订单），课程创建者可见自己课程的订单（即使在他人的学习室）。
- 评价：所有评价都关联订单，经订单取所属学习室。学习室创建人可见的评价全部可见；此外有课程的评价（`course_id` 非空）在课程创建人可见时也可见。
- 钱包流水：交易经 `booking_id` 回溯关联订单，复用预约可见性口径，且仅保留 `booking_id` 非空的交易；无关联预约的流水（如充值 recharge）对非超管不可见。列表、统计、导出同口径。

超级管理员 SHALL 查看全部预约/评价/钱包流水，不受过滤。认证、教育 listing 不做数据过滤。可见范围以拥有对应菜单/按钮权限为前提，权限控制与只读归属判定不变。

#### Scenario: Booking visibility by associated content
- **GIVEN** 普通管理员 A 创建了课程 X 与学习室 R，普通管理员 B 创建了学习室 S
- **WHEN** A 请求预约列表
- **THEN** 返回学习室 R 的全部订单（座位订单与课程订单，含他人创建课程在 R 产生的订单）、课程 X 的课程订单（即使在他人学习室），以及关联学习室/课程创建人为空或为超级管理员的订单
- **AND** 不返回学习室 S 中由其他普通管理员创建课程产生的、且与 A 无归属关联的订单

#### Scenario: Review visibility by associated content
- **GIVEN** 普通管理员 A 拥有学习室 R，课程 X 由其他普通管理员创建但在 R 产生评价
- **WHEN** A 请求评价列表
- **THEN** 返回学习室 R 关联的全部评价（含课程 X 的评价）、A 创建课程的评价（即使在他人学习室），以及关联学习室/课程创建人为空或为超级管理员的评价

#### Scenario: Room owner sees cross-created course records
- **GIVEN** 普通管理员 B 拥有学习室 S，普通管理员 A 创建了课程 X，前端用户在 S 预约课程 X 产生订单与评价
- **WHEN** B 请求预约列表与评价列表
- **THEN** B 可见该课程订单与评价（因学习室 S 归 B），尽管课程 X 非 B 创建
- **AND** A 仍可见该课程订单与评价（因课程 X 归 A）

#### Scenario: Wallet transactions follow room ownership
- **GIVEN** 普通管理员 A 拥有学习室 R，前端用户预约 R 的座位或课程产生消费/退款流水，另有充值流水（无关联预约）与他人学习室的消费流水
- **WHEN** A 请求钱包流水列表、统计或导出
- **THEN** 仅返回关联预约的学习室归 A、创建人为空或为超级管理员，或关联课程归 A 的消费/退款流水
- **AND** 充值等无关联预约的流水不返回，他人学习室且与 A 无归属关联的流水不返回
- **AND** 列表、统计、导出三者口径一致

#### Scenario: Super admin sees all records
- **GIVEN** 超级管理员 S
- **WHEN** S 请求预约/评价/钱包流水列表、统计或导出
- **THEN** 返回全部数据（含充值与他人创建内容关联的记录），不受过滤