# 验证报告：admin-contact-phone-sms-settings

- 日期：2026-09-22
- 工作流：comet tweak（Classic）
- 验证模式：full（含 delta spec，capability：admin-auth-api）
- 结论：**通过**

## 1. 需求与范围

1. 「用户名」label 增加提示「用户名修改后 30 天内不可再次修改」，冻结期内输入框置灰不可修改。
2. 在「安全设置」下新增「联系方式设置」TAB；联系电话迁移至此，改为「短信验证码校验」后更新；label 增加「联系电话修改后 30 天内不可再次修改」提示，冻结期内全部置灰。
3. 会话内追加：安全设置/联系方式设置输入框宽度与基本设置一致；联系方式设置移除底部「当前手机号」文案，改为在「联系电话」输入框内回显当前号码。

## 2. Tasks 完成情况

`tasks.md` 全部任务（1.1–1.3、2.1–2.4、3.1）均勾选完成。

## 3. 后端验证（br-server）

命令：`pytest tests/test_admin_auth_api.py tests/test_api_user_profile.py -q -p no:cacheprovider`
结果：**28 passed**（仅 Pydantic/FastAPI 弃用告警，非失败）。

实现要点：
- 新增 `PATCH /api/v1/admin/auth/phone`：先经公共 `POST /api/v1/auth/send-code` 发送、`SMSService.verify_code` 校验，失败返回 400「验证码无效或已过期」；成功复用 `UserProfileService.change_phone`（唯一性 409、30 天冻结期 429 + `retry_after_seconds`），复用 C 端既有规则。
- `AdminProfileUpdate` 移除 `phone`，`PUT /profile` 出现 `phone`/`mobile`/未知字段返回 422（extra="forbid"）。
- `AdminAuthService.update_profile` 不再处理 phone 分支。

## 4. Delta spec 场景 ↔ 测试映射

| 场景 | 覆盖测试 |
| --- | --- |
| Current admin info | `test_me_returns_phone` |
| Update profile persists fields | `test_profile_update_persists_username` / `_persists_gender_birthday_signature` |
| Update profile rejects unknown fields | `test_profile_update_does_not_accept_mobile` / `test_profile_update_rejects_phone_field` |
| Update profile ignores unchanged fields | `test_profile_update_unchanged_username_skips_cooldown` |
| Update profile persists phone（PATCH 成功） | `TestAdminPhoneChangeWithSms` 有效验证码 200 |
| Update phone conflicts with existing user | `TestAdminPhoneChangeWithSms` 冲突 409 |
| Phone change rejects invalid code | `TestAdminPhoneChangeWithSms` 无效验证码 400 |
| Username duplicate rejected | `test_profile_update_rejects_duplicate_username` |
| Username invalid format rejected | `test_profile_update_rejects_invalid_username_format` |
| Cooldown blocks second change within 30 days | `test_profile_update_username_cooldown_returns_429` + 手机号冻结期 429 |
| Permission list format | `test_admin_login_and_me_return_permissions` |

无未覆盖场景。

## 5. 前端验证（br-admin）

命令：`pnpm build` → **built 成功，无类型/编译错误**。

浏览器实测（vite dev :8002，已登录超级管理员）：
- 三 TAB 切换正常：基本设置 / 安全设置 / 联系方式设置。
- 用户名 label 含 tooltip 图标；置灰演示：冻结期内（模拟 25 天）`username` 输入框 `disabled=true`，placeholder「用户名修改后 30 天内不可再次修改（剩余 25 天）」。
- 联系方式：`联系电话` 输入框预填当前号码 `13726755889`；冻结期内电话/验证码/获取验证码/保存全部 `disabled=true`，展示「剩余 25 天」文案。
- 网络链路：`sendSmsCode → /api/v1/auth/send-code` 触达真实短信网关（该号码当日流控上限，未发码）；`changeAdminPhone → PATCH /api/v1/admin/auth/phone` 使用错误验证码返回 400，前端 toast「验证码无效或已过期」。
- 宽度对齐：用户名与联系电话输入框宽度均为 164px，与安全/基本设置一致。
- 未改动禁用：联系电话输入框预填当前号码时「获取验证码」按钮 `disabled=true`；改为不同号码后按钮恢复可点击（实测 13726755889 禁用、13900139001 启用）。
- 演示用的临时置灰覆盖已全部回退（`grep TEMP-DEMO` 无残留），冻结期判断回归读取 `username_updated_at`/`phone_updated_at`。

> 说明：当前共享管理员的 `username_updated_at`/`phone_updated_at` 均为 `null`，故默认态输入框可编辑属预期行为；置灰仅在真实发生过一次修改后的 30 天内出现。因目标库为共享远程 Postgres，未写入测试性时间戳，改以可回退的前端渲染验证 + 后端 429 用例共同证明机制。

## 6. 回归

- 基本设置其余字段（头像/昵称/邮箱/性别/生日/签名）保存与回显不受影响。
- C 端 `/api/v1/users/me/phone`、`/api/v1/auth/send-code` 未改动，行为不变。

## 7. 安全

- 无新增硬编码密钥；验证码走服务端 `SMSService`；改号必须验证码 + 唯一性 + 冻结期三重校验。

## 8. 提交

- `a2d940c` 后端接口与 profile 移除 phone
- `f85af79` 联系方式 TAB + 冻结期置灰 + 用户名提示
- `357dbd2` 输入框宽度对齐 + 联系电话回显当前号码
- `25b2896` 联系电话未改动时禁用「获取验证码」按钮
