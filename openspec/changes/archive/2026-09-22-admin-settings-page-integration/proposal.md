# Proposal: admin-settings-page-integration

## Why

br-admin 的「个人设置」（/setting/account）与「系统设置」（/setting/system）页面主体已调用 br-server 真实接口，但经确认存在一处功能断裂：基本设置表单固定提交 `mobile` 字段，而后端 `AdminProfileUpdate` 为 `extra="forbid"` 且不返回电话字段，导致保存个人资料必然 422，个人资料无法入库。同时安全设置 TAB 表单因 `-mt-4` 负边距与「安全设置」标题间距过小，视觉局促。

## What Changes

- br-server 管理端 profile 接口以统一用户表的 `phone` 列承载联系电话：`GET /api/v1/admin/auth/me` 与 `PUT /api/v1/admin/auth/profile` 响应新增 `phone`、`username_updated_at`、`phone_updated_at` 字段；`PUT /api/v1/admin/auth/profile` 请求支持可选 `username` 与 `phone`。
- 用户名/手机号变更复用 C 端 `UserProfileService` 既有规则（用户追加需求）：格式校验、全局唯一（冲突 409）、30 天（一个月）冻结期（再次修改返回 429 + `retry_after_seconds`）；值未变化不触发限制。
- br-admin 个人设置-基本设置表单新增「用户名」输入，字段 `mobile` 改为 `phone`，回显与提交走后端接口（用户名/昵称/邮箱/电话/头像入库）并补充性别/生日/个性签名；联系电话为前端必填，用户名/电话/邮箱/昵称后端均为可选字段；头像上传移至表单最上方并复用 `/training/teachers/edit.vue` 的头像 UI，上传沿用公共方法 `uploadImage(file, 'avatar')`（后端代理阿里 OSS，scope 已在 `UPLOAD_SCOPES` 白名单注册，无需改动）。
- br-admin 顶栏（Header）：下拉「个人设置」点击跳转 `/setting/account` 修复；右上角展示 头像+名称（名称优先后端昵称、空则回退用户名；头像为空时回退默认 logo）。
- br-admin 个人设置-安全设置 TAB 移除根节点 `-mt-4` 负边距，使「旧密码」行与「安全设置」标题拉开正常间隔。
- 系统设置页（基本设置/邮件设置）经确认已完整对接 `/api/v1/admin/settings*` 并入库，本次无功能改动，仅纳入验证范围。
- 无数据库 schema 变更（`users.phone` 列已存在）。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `admin-auth-api`: 「Current admin profile API」响应字段由 `mobile` 修正为 `phone`（取自 `users.phone`），新增 `username_updated_at`/`phone_updated_at`；新增管理端个人资料更新（`PUT /api/v1/admin/auth/profile`）的用户名/电话字段行为要求，含唯一性与 30 天冻结期（复用 C 端规则）。

## Impact

- 后端模块：`br-server/app/schemas/admin_auth.py`、`br-server/app/services/admin_auth_service.py`、`br-server/app/services/user_profile_service.py`（暴露可复用原语）、`br-server/tests/test_admin_auth_api.py`
- 前端模块：`br-admin/src/views/setting/account/BasicSetting.vue`、`br-admin/src/views/setting/account/SafetySetting.vue`、`br-admin/src/api/system/user.ts`
- 不影响：上传接口/OSS 配置、system_settings 存储、RBAC 权限码

## Rollback

单一 commit 粒度可整体 revert：revert 后端 schema/service 改动即恢复 `extra="forbid"` 拒绝 phone 的原行为，revert 前端改动即恢复原表单；无迁移、无数据写入格式变化，无需数据回滚。
