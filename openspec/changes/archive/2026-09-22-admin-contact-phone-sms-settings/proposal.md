# Proposal: admin-contact-phone-sms-settings

## Why

个人设置页已对接后端 profile，但「联系电话」目前随基本设置一起提交，改电话不经过任何所有权验证，存在账号接管风险；同时用户名/联系电话的 30 天冻结期只体现在输入框 placeholder 上，提示不显著，且冻结期内输入框仍可编辑（提交才被后端 429 拒绝）。

## What Changes

- br-server 新增管理端验证码改手机号接口 `PATCH /api/v1/admin/auth/phone`（请求 `{phone, sms_code}`）：复用公共 `POST /api/v1/auth/send-code`（阿里短信 + 60s/日限流，无需改动）与 C 端既有原语 `SMSService.verify_code`、`UserProfileService.change_phone`（30 天冻结期 429 + `retry_after_seconds`、全局唯一 409），错误契约与 C 端 `/users/me/phone` 完全一致。
- `PUT /api/v1/admin/auth/profile` 不再接受 `phone` 字段（`extra="forbid"` 下回退为 422），手机号变更统一走验证码接口。
- br-admin 个人设置左侧新增「联系方式设置」TAB（位于「安全设置」之下）：联系电话 + 手机验证码 + 「获取验证码」按钮（60 秒倒计时），保存调用新接口；提示「联系电话修改后 30 天内不可再次修改」。
- 「用户名」标签后增加同款提示「用户名修改后 30 天内不可再次修改」（tooltip，参考安全设置样式）。
- 冻结期内（`username_updated_at`/`phone_updated_at` 距今 < 30 天）对应输入框置灰禁用，提示剩余天数，不再允许提交后才报错。
- 基本设置移除「联系电话」字段。
- 无数据库 schema 变更，无新依赖。

## Capabilities

### New Capabilities

（无）

### Modified Capabilities

- `admin-auth-api`: profile 更新字段移除 `phone`；新增 Requirement「Admin phone change with SMS verification」（验证码校验、409 唯一、429 冻结期契约）。

## Impact

- 后端：`br-server/app/api/routes/admin_auth.py`、`br-server/app/schemas/admin_auth.py`、`br-server/tests/test_admin_auth_api.py`
- 前端：`br-admin/src/views/setting/account/account.vue`、`BasicSetting.vue`、新增 `ContactSetting.vue`、`br-admin/src/api/system/user.ts`
- 不影响：C 端接口、上传/OSS、system_settings、RBAC

## Rollback

单 change revert：revert 后端即恢复 profile 直接改电话（无验证码），revert 前端即恢复基本设置含电话；无数据迁移，`users.phone` 写入格式不变。
