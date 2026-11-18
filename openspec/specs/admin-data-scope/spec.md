# admin-data-scope Specification

## Purpose
TBD - created by archiving change role-page-user-type-data-scope. Update Purpose after archive.
## Requirements
### Requirement: Content ownership tracking
系统 SHALL 在管理员创建的内容型数据（课程、活动、自习室、优惠券、教师）上记录创建人 `created_by`（可空 UUID）。存量数据与 legacy 管理员创建的数据 `created_by` 为空。

#### Scenario: Admin creates content
- **GIVEN** 已登录的普通管理员
- **WHEN** 通过 admin 接口创建课程/活动/自习室/优惠券/教师
- **THEN** 数据记录 `created_by` 为该管理员 id

#### Scenario: Legacy admin creates content
- **GIVEN** 使用 legacy X-Admin-Token 的请求（admin_id 为 UUID(int=0)）
- **WHEN** 创建内容型数据
- **THEN** `created_by` 为空（不写入不存在的外键 id）

### Requirement: Data scope for non-super admins
非超级管理员 SHALL 可查看自己创建的内容型数据、创建人为空的存量数据，以及创建人当前为超级管理员（`user_type='super-admin'`）的内容型数据；超级管理员 SHALL 查看全部数据。座位随所属自习室归属；课时/排课子资源随课程入口。可见范围以拥有对应菜单/按钮权限为前提，权限控制不变。

#### Scenario: Normal admin lists own and legacy content
- **GIVEN** 普通管理员 A 创建了课程 X，普通管理员 B 创建了课程 Y，存量课程 Z 创建人为空
- **WHEN** A 请求课程列表
- **THEN** 返回 X 与 Z，不包含 Y

#### Scenario: Super admin sees all
- **GIVEN** 超级管理员
- **WHEN** 请求内容型列表
- **THEN** 返回全部数据（含他人创建）

#### Scenario: Detail respects scope
- **GIVEN** 普通管理员 A
- **WHEN** A 请求其他普通管理员创建且创建人非空的内容详情
- **THEN** 返回 404

#### Scenario: Seats follow room ownership
- **GIVEN** 普通管理员 A 创建了自习室 R
- **WHEN** A 请求座位列表
- **THEN** 仅返回所属自习室归 A、创建人为空或创建人为超级管理员的座位

#### Scenario: Super-admin created content is public
- **GIVEN** 超级管理员 S 创建了课程 X、自习室 R、活动、优惠券、教师，普通管理员 A 拥有对应菜单权限
- **WHEN** A 请求上述内容型列表或详情
- **THEN** 超管创建的数据对 A 可见（列表包含、详情 200）
- **AND** 自习室 R 的座位对 A 可见

#### Scenario: Creator demoted loses public visibility
- **GIVEN** 超级管理员 S 创建了课程 X，随后 S 被降级为普通用户（`user_type='normal-user'`）
- **WHEN** 其他普通管理员 A 请求课程列表
- **THEN** 课程 X 不再对 A 公开可见（恢复按创建人归属过滤）

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

### Requirement: Super-admin created content is read-only for non-super admins
非超级管理员 SHALL 不能修改「创建人当前为超级管理员」的内容型数据及其随属记录（座位、课时/排课、预约、评价）：所有修改类 admin 写端点（更新、删除、状态切换、课时/排课增删改、座位增删改、预约确认/取消、评价审核/回复）SHALL 返回 403。列表与详情响应 SHALL 携带 `readonly` 标志（超管创建的数据对非超管为 true，自己创建与创建人为空的数据为 false；超管查看恒为 false）。br-admin 列表 SHALL 将 `readonly` 行整行置灰并禁用修改类操作按钮，纯查看入口保留。创建人降级为普通用户后，其数据恢复按归属过滤，本人可正常修改。

#### Scenario: Non-super admin write rejected
- **GIVEN** 超级管理员 S 创建了自习室 R、课程 X、活动、优惠券、教师，普通管理员 A 拥有对应菜单与按钮权限
- **WHEN** A 调用上述内容的更新/删除/状态切换接口
- **THEN** 返回 403，数据不被修改

#### Scenario: Sub-resource and record writes rejected
- **GIVEN** 超管创建的自习室 R（含座位）与课程 X（含课时/排课），以及关联 R/X 的预约与评价
- **WHEN** 普通管理员 A 调用座位增删改、课时/排课增删改与延期、预约确认/取消、评价审核/回复接口
- **THEN** 均返回 403，数据不被修改

#### Scenario: List rows carry readonly flag
- **GIVEN** 普通管理员 A 的列表中同时存在超管创建的数据、A 自己创建的数据与创建人为空的存量数据
- **WHEN** A 请求列表或详情
- **THEN** 超管创建的行 `readonly=true`，自己创建与存量行 `readonly=false`
- **AND** 预约/评价/座位的 `readonly` 随关联内容（课程或自习室）的创建人判定

#### Scenario: Super admin unaffected
- **GIVEN** 超级管理员 S
- **WHEN** S 请求任意列表/详情并执行写操作
- **THEN** 所有行 `readonly=false`，写操作按既有权限规则正常执行

#### Scenario: Frontend grays readonly rows
- **GIVEN** 普通管理员 A 打开业务列表页，列表含超管创建的数据
- **WHEN** 页面渲染
- **THEN** 超管创建的行整行置灰，编辑/删除/状态切换等修改类按钮禁用
- **AND** 查看详情、管理座位等纯查看入口仍可用（座位页内修改操作同样禁用）

#### Scenario: Own and legacy content stays writable
- **GIVEN** 普通管理员 A 拥有对应按钮权限
- **WHEN** A 修改自己创建的数据或创建人为空的存量数据
- **THEN** 写操作正常执行，`readonly=false`

