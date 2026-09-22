# Tasks: admin-settings-page-integration

## 1. br-server：profile 接口支持 username/phone/性别生日签名 + 30 天冻结期

- [x] 1.1 `AdminCurrentResponse`/`admin_profile_from_model` 增加 `phone`、`gender`、`birthday`、`signature`、`username_updated_at`、`phone_updated_at`；`AdminProfileUpdate` 增加可选 `username`（max 50，格式仅在变更时由服务层校验，避免存量短用户名被 422）与 `phone`（max 11，维持 extra=forbid）
- [x] 1.2 `UserProfileService` 开放复用原语：`update_username`/`enforce_cooldown` 去私有化、抽出 `update_phone`（冻结期+唯一性），C 端行为不变
- [x] 1.3 `AdminAuthService.update_profile` 委托 username/phone 变更给 `UserProfileService`（值未变不触发校验）；`PUT /profile` 路由捕获 `ProfileCooldownError` 返回 429 + `retry_after_seconds`
- [x] 1.4 `tests/test_admin_auth_api.py` 补充用例：/me 含 phone 与时间戳、更新 username/phone/gender/birthday/signature 入库、冻结期 429（含 30 天文案与 retry_after_seconds）、重复 409、格式 422、未知字段 422、未变化字段不受限；修复 `test_api_user_profile.py` 陈旧 24h 断言与 `test_api_upload.py` 两个陈旧 scope 用例；本次改动相关测试全部通过

## 2. br-admin：设置页修复

- [x] 2.1 `api/system/user.ts` 类型补 `phone`/`gender`/`birthday`/`signature`/时间戳/`username`；`BasicSetting.vue` 重写：字段顺序 头像→用户名→联系电话（必填）→昵称（选填）→邮箱（选填）→性别→生日→个性签名；头像置顶并复用 `/training/teachers/edit.vue` 样式（圆形预览/暂无头像/上传按钮/提示文案），经公用 `uploadImage(file, 'avatar')` 上 OSS；用户名/联系电话沿用 30 天冻结期提示（剩余 X 天）；表单 `mobile`→`phone` 并回显
- [x] 2.2 `SafetySetting.vue` 移除 `-mt-4`，拉开「旧密码」与「安全设置」标题间隔（实测 12px）
- [x] 2.3 `Header/index.vue`：下拉「个人设置」点击修复（push `/setting/account`）；右上角展示 头像+用户名（用户头像为空时回退默认 logo）
- [x] 2.4 br-admin 构建通过（vite build），浏览器实测：个人设置页字段顺序正确、保存 PUT /profile 200、下拉「个人设置」可跳转 /setting/account、头像/用户名展示正常

## 3. 回归确认

- [x] 3.1 确认系统设置页（基本设置/邮件设置）读写与 `system_settings` 入库正常，无需代码改动
