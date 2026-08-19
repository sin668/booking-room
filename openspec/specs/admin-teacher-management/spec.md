# admin-teacher-management Specification

## Purpose
TBD - created by archiving change admin-teacher-management. Update Purpose after archive.
## Requirements
### Requirement: 老师数据模型扩展
系统 SHALL 在 teachers 表存储老师的专业方向（specialty）、教龄（teaching_years）、学历（education）、毕业院校（school）、在职状态（status: active/inactive）、教学特色标签（teaching_tags）与资质认证（qualifications, JSON）；并 SHALL 通过 teacher_rooms 关联表支持一位老师关联多个培训室或综合室（study_rooms.room_type ∈ training|comprehensive），同一老师与房间的组合 MUST 唯一。

#### Scenario: 老师关联多个培训室/综合室
- **WHEN** 管理员保存老师时选择多个 room_type 为 training 或 comprehensive 的房间
- **THEN** teacher_rooms 中保存对应关联记录，详情接口返回全部 room_ids

#### Scenario: 关联房间类型校验
- **WHEN** 保存老师时传入 room_type 为 study 的房间 ID
- **THEN** 接口返回 400，不写入关联

### Requirement: 后台老师管理 CRUD
系统 SHALL 提供 `/api/v1/admin/teachers` 管理端接口，支持分页列表（keyword 搜索）、详情、新增、编辑、删除与停用/启用，全部接口 MUST 校验管理员权限（teacher:view/create/update/delete/status）；列表接口响应 MUST 保持 items 含 id/name/avatar/title 以兼容排课老师下拉。

#### Scenario: 删除存在排课的老师
- **WHEN** 管理员删除仍有关联排课记录的老师
- **THEN** 接口返回 400 拒绝删除

#### Scenario: 停用老师
- **WHEN** 管理员将老师状态切换为 inactive
- **THEN** 老师列表状态显示停用，C 端教师详情接口对该老师返回 404

### Requirement: br-admin 老师管理页面
br-admin SHALL 在培训管理下提供老师管理列表页与新增/编辑老师页面；新增/编辑 MUST 采用页面跳转模式（独立路由页，hideInMenu），页面布局 MUST 与培训课程编辑页风格一致，编辑页 MUST 支持多选所属培训室/综合室。

#### Scenario: 从列表跳转编辑页
- **WHEN** 管理员在老师列表点击编辑或新增老师
- **THEN** 跳转至 `/training/teachers/edit/:id?` 独立页面，保存成功后返回列表页

### Requirement: C 端教师简介页数据来自库表
br-app 教师简介页 `/pages/teacher/profile` 展示的个人简介、专业方向、教龄、学历、资质认证、教学特色 MUST 来自 br-server `GET /api/v1/teachers/{teacher_id}` 返回的库表数据，不得硬编码；资质认证或教学特色为空时对应区块 MUST 隐藏。

#### Scenario: 资质认证为空
- **WHEN** 老师未配置资质认证数据
- **THEN** 教师简介页不显示资质认证区块

