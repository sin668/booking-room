# Design: admin-contact-phone-sms-settings

## 实现说明

### br-server
- `app/api/routes/admin_auth.py`：新增 `PATCH /api/v1/admin/auth/phone`，实现完全镜像 C 端 `user.py` 的 `/me/phone`（60-85 行）：
  - 请求体直接复用 C 端 `app.schemas.user.ChangePhoneRequest`（`phone` 正则 `^1[3-9]\d{9}$` + 6 位 `sms_code`）与 `ChangePhoneResponse`，不新建 schema。
  - `SMSService.verify_code(phone, sms_code)` 失败 → 400 `{"detail": "验证码无效或已过期"}`。
  - `UserProfileService.change_phone(admin_id, phone)`（既有：30 天冻结期 + 全局唯一 409 + 写 `phone_updated_at`）；`ProfileCooldownError` → 429 `{detail, retry_after_seconds}`。
  - 验证码发送复用公共 `POST /api/v1/auth/send-code`（无鉴权、60s/日限流、验证码 300s TTL），后端零改动。
- `app/schemas/admin_auth.py`：`AdminProfileUpdate` 移除 `phone` 字段（`extra="forbid"` 下提交 phone 即 422，手机号变更统一走验证码接口）；`AdminCurrentResponse` 保留 `phone`/`phone_updated_at` 用于回显。

### br-admin
- `src/api/system/user.ts`：新增 `changeAdminPhone({phone, sms_code})`（PATCH `/admin/auth/phone`）与 `sendSmsCode(phone)`（POST `/auth/send-code`，公共接口）；`AdminProfileParams` 移除 `phone`。
- `views/setting/account/account.vue`：左侧 TAB 列表在「安全设置」下新增「联系方式设置」（key 3），渲染新组件 `ContactSetting.vue`。
- `views/setting/account/BasicSetting.vue`：
  - 移除「联系电话」表单项、`phone` 字段与必填规则、`phonePlaceholder`/`phoneCooldown`（迁至联系方式设置）。
  - 「用户名」label 使用 `#label` 插槽：文本 + `n-tooltip`（QuestionCircleOutlined 图标），提示固定文案「用户名修改后 30 天内不可再次修改」；`usernameCooldown > 0` 时输入框 `disabled`（灰掉），placeholder 保留剩余天数提示。
  - 提交体不再含 `phone`。
- `views/setting/account/ContactSetting.vue`（新增）：
  - 回显当前 `phone`；「联系电话」label 同款 tooltip 提示「联系电话修改后 30 天内不可再次修改」。
  - `phoneCooldown > 0` 时电话输入、验证码输入、「获取验证码」「保存」全部 `disabled`，placeholder 显示剩余天数。
  - 「获取验证码」：校验电话格式后 `sendSmsCode(newPhone)`，60 秒倒计时；429/其他错误 toast 后端 `detail`。
  - 「保存」：`changeAdminPhone({phone, sms_code})`，成功后刷新 store 的 CURRENT-USER（电话回显与冻结期），400/409/429 的 `detail` 直接 toast。

### 验证口径
- 后端 pytest：新端点成功更换（mock Redis 预置验证码）、验证码错误 400、重复手机号 409、冻结期 429 + `retry_after_seconds`；`PUT /profile` 提交 phone 返回 422；更新既有 phone-persists 用例迁移到新端点。
- 前端：vite build + 浏览器实测三个 TAB 渲染、用户名冻结期置灰、获取验证码倒计时与保存链路、错误提示可见。

## 回滚
单 change revert；无迁移、无数据格式变化。
