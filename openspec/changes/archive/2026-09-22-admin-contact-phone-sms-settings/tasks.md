# Tasks: admin-contact-phone-sms-settings

## 1. br-server：验证码改手机号接口

- [x] 1.1 `routes/admin_auth.py` 新增 `PATCH /admin/auth/phone`：复用 `ChangePhoneRequest/Response`、`SMSService.verify_code`（失败 400）、`UserProfileService.change_phone`（409/冻结期 429 + `retry_after_seconds`），镜像 C 端 `/me/phone` 契约
- [x] 1.2 `schemas/admin_auth.py`：`AdminProfileUpdate` 移除 `phone`；`AdminCurrentResponse` 保留 `phone`/`phone_updated_at` 回显
- [x] 1.3 `tests/test_admin_auth_api.py`：新端点用例（成功更换并刷新 `phone_updated_at`、验证码错误 400、重复 409、冻结期 429）；原 profile 改电话用例改为断言 422；相关测试全绿

## 2. br-admin：联系方式设置 TAB 与冻结期置灰

- [x] 2.1 `api/system/user.ts`：新增 `changeAdminPhone`、`sendSmsCode`；`AdminProfileParams` 移除 `phone`
- [x] 2.2 `BasicSetting.vue`：移除联系电话字段与规则；「用户名」label 加 tooltip 提示「用户名修改后 30 天内不可再次修改」；冻结期内用户名输入框 disabled
- [x] 2.3 `account.vue` + 新增 `ContactSetting.vue`：「安全设置」下新增「联系方式设置」TAB；电话 + 验证码 + 60s 倒计时获取验证码 + 保存；label tooltip「联系电话修改后 30 天内不可再次修改」；冻结期内全部 disabled 并显示剩余天数；成功后刷新 store 用户缓存
- [x] 2.4 br-admin 构建通过；浏览器实测：三 TAB 切换、用户名冻结期置灰与提示、验证码发送/保存链路与 400/409/429 提示

## 3. 回归确认

- [x] 3.1 基本设置其余字段（头像/昵称/邮箱/性别/生日/签名）保存与回显不受影响；C 端 `/users/me/phone` 与 `/auth/send-code` 行为不变
