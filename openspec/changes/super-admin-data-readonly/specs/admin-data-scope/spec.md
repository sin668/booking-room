# admin-data-scope Delta Spec

## ADDED Requirements

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