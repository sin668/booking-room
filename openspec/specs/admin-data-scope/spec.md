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
预约与评价 SHALL 随关联内容归属过滤：课程订单/有课程的评价随课程创建人，座位订单/无课程的评价随自习室创建人；关联内容创建人为空或当前为超级管理员时，对应预约/评价对拥有权限的所有管理员可见。认证、钱包流水、教育 listing 不做数据过滤。

#### Scenario: Booking visibility by associated content
- **GIVEN** 普通管理员 A 创建了课程 X 与自习室 R
- **WHEN** A 请求预约列表
- **THEN** 返回课程 X 的课程订单、自习室 R 的座位订单，以及关联内容创建人为空或为超级管理员的订单
- **AND** 不返回其他普通管理员创建内容关联的订单

#### Scenario: Review visibility by associated content
- **GIVEN** 普通管理员 A
- **WHEN** A 请求评价列表
- **THEN** 仅返回关联课程/自习室归 A、创建人为空或创建人为超级管理员的评价

