# Design: admin-settings-page-integration

## 实现说明

### br-server
- `app/schemas/admin_auth.py`：`AdminCurrentResponse` 增加 `phone`、`gender`、`birthday`、`signature`、`username_updated_at`、`phone_updated_at`；`admin_profile_from_model` 同步输出；`AdminProfileUpdate` 增加可选 `username`（max 50，格式仅在变更时由 service 校验，避免存量短用户名被 schema 拒绝）与 `phone`（max 11）、`gender`（max 10）、`birthday`（date）、`signature`（max 200），维持 `extra="forbid"`。
- `app/services/user_profile_service.py`：将既有原语开放复用——`_update_username`→`update_username`、`_enforce_cooldown`→`enforce_cooldown`（仅重命名，行为不变，含 C 端调用点）；从 `change_phone` 抽出 `update_phone(user, new_phone)`（冻结期校验 + 全局唯一 409 + 写入 `phone`/`phone_updated_at`，不 flush），`change_phone` 改为调用它。
- `app/services/admin_auth_service.py`：`update_profile` 中 `username`/`phone` 与当前值不同才委托 `UserProfileService.update_username` / `update_phone`（复用格式校验、唯一性、30 天冻结期），其余字段沿用 setattr + flush。
- `app/api/routes/admin_auth.py`：`PUT /profile` 捕获 `ProfileCooldownError`，返回 429 `{detail, retry_after_seconds}`（与 C 端 `/users/me` 口径一致）。
- 无 alembic 迁移（`users.phone`、`username_updated_at`、`phone_updated_at` 列已存在）。

### br-admin
- `src/api/system/user.ts`：`AdminUserInfo` 增加 `phone?`、`username_updated_at?`、`phone_updated_at?`；`AdminProfileParams` 增加 `username?`、`phone?`（去掉 mobile 口径）。
- `views/setting/account/BasicSetting.vue`：字段顺序 头像→用户名（必填）→联系电话（必填）→昵称（选填）→邮箱（选填）→性别（n-select：男/女/保密 → male/female/secret）→生日（n-date-picker → YYYY-MM-DD）→个性签名（textarea，≤200）；头像区块复用 `/training/teachers/edit.vue` 样式（圆形预览/暂无头像/上传按钮/建议文案），仍走公共 `uploadImage(file, 'avatar')` → OSS；表单字段 `mobile` → `phone` 并回显 `result.phone`；提交体携带 `username`/`phone`/`nickname`/`email`/`avatar`/`gender`/`birthday`/`signature`，后端按冻结期/唯一性规则校验，429/409/422 的 `detail` 直接作为错误提示展示；用户名/电话按 `username_updated_at`/`phone_updated_at` 展示 30 天冻结期剩余天数提示。
- `layout/components/Header/index.vue`：下拉「个人设置」由 `router.push({ name: 'Setting' })`（点击无效）改为 `push('/setting/account')`；右上角展示 `n-avatar`（`userStore.getAvatar`，为空回退 `websiteConfig.logo`）+ 名称（优先 `getNickname`，空回退 `info.username`）。
- `views/setting/account/SafetySetting.vue`：根 `n-grid` 移除 `class="-mt-4"`，恢复与卡片标题「安全设置」的正常间隔。

### 验证口径
- 后端：pytest 覆盖 /me 返回 phone 与时间戳、username/phone 更新入库并刷新冻结时间戳、冻结期 429、重复 409、格式 422、未知字段（mobile）422、未变化字段不受冻结期影响；回归 C 端 `tests/test_api_user_profile.py`。
- 前端：浏览器实测保存个人资料成功且刷新后回显；安全设置 TAB 间距正常。

## 回滚
单 commit revert 即可，无数据迁移。
