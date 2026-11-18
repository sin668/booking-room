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
非超级管理员 SHALL 只能查看自己创建的内容型数据及创建人为空的存量数据；超级管理员 SHALL 查看全部数据。座位随所属自习室归属；课时/排课子资源随课程入口。

#### Scenario: Normal admin lists own and legacy content
- **GIVEN** 普通管理员 A 创建了课程 X，管理员 B 创建了课程 Y，存量课程 Z 创建人为空
- **WHEN** A 请求课程列表
- **THEN** 返回 X 与 Z，不包含 Y

#### Scenario: Super admin sees all
- **GIVEN** 超级管理员
- **WHEN** 请求内容型列表
- **THEN** 返回全部数据（含他人创建）

#### Scenario: Detail respects scope
- **GIVEN** 普通管理员 A
- **WHEN** A 请求他人创建且创建人非空的内容详情
- **THEN** 返回 404

#### Scenario: Seats follow room ownership
- **GIVEN** 普通管理员 A 创建了自习室 R
- **WHEN** A 请求座位列表
- **THEN** 仅返回所属自习室归 A 或创建人为空的座位

### Requirement: Record data follows associated content
预约与评价 SHALL 随关联内容归属过滤：课程订单/有课程的评价随课程创建人，座位订单/无课程的评价随自习室创建人。认证、钱包流水、教育 listing 不做数据过滤。

#### Scenario: Booking visibility by associated content
- **GIVEN** 普通管理员 A 创建了课程 X 与自习室 R
- **WHEN** A 请求预约列表
- **THEN** 返回课程 X 的课程订单、自习室 R 的座位订单，以及关联内容创建人为空的订单
- **AND** 不返回他人创建内容关联的订单

#### Scenario: Review visibility by associated content
- **GIVEN** 普通管理员 A
- **WHEN** A 请求评价列表
- **THEN** 仅返回关联课程/自习室归 A 或创建人为空的评价

