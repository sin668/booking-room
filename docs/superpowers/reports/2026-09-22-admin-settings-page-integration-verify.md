# 验证报告：admin-settings-page-integration

- 日期：2026-09-22
- 验证模式：full（scale 评估：9 tasks / 1 delta capability / 11 files → full）
- change：openspec/changes/admin-settings-page-integration
- review_mode：off（按配置跳过自动代码审查；已人工核对 diff 与 spec 一致性，无安全项变更）

## 摘要

| 维度 | 结论 |
|------|------|
| 完整性 Completeness | 9/9 任务 `[x]`；delta spec 1 项 Requirement 全部有实现与测试 |
| 正确性 Correctness | 10 个 Scenario 中 8 个新增行为全部有 pytest 覆盖且通过；2 个（Permission list format / Missing admin token）为既有行为回归，未破坏 |
| 一致性 Coherence | 实现符合 design.md（验证阶段已将 proposal/design 文案同步至最终范围：联系电话前端必填、头像置顶复用教师页 UI、Header 昵称优先展示） |

**最终结论：通过。无 CRITICAL / IMPORTANT 问题。**

## 检查项明细

1. **tasks.md 全部完成**：`- [x]` 9/9（含验证阶段补充的 Header 昵称优先微调，已实现、构建并提交）。
2. **实现符合 design.md**：
   - `br-server/app/schemas/admin_auth.py`：`AdminCurrentResponse`/`AdminProfileUpdate` 扩展 `phone/gender/birthday/signature/username_updated_at/phone_updated_at`，`extra="forbid"` 保持 ✓
   - `br-server/app/services/user_profile_service.py`：`update_username/update_phone/enforce_cooldown` 开放复用，C 端行为不变（仅重命名/抽取）✓
   - `br-server/app/services/admin_auth_service.py`：值未变不触发校验，委托复用冻结期/唯一性 ✓
   - `br-server/app/api/routes/admin_auth.py`：429 `{detail, retry_after_seconds}` 与 C 端口径一致 ✓
   - `br-admin` BasicSetting/SafetySetting/api 类型/Header 按 design 落地 ✓
3. **Design Doc（docs/superpowers/specs）**：tweak 预设无 Design Doc，跳过（N/A）。
4. **能力规格场景覆盖**（delta `admin-auth-api`）：
   - Current admin info → `test_me_returns_phone_and_cooldown_timestamps`
   - Update profile persists fields → `test_update_profile_persists_phone` / `test_update_profile_persists_username`
   - Rejects unknown fields（mobile）→ `test_update_profile_rejects_unknown_mobile_field`
   - Ignores unchanged fields → `test_update_profile_unchanged_phone_skips_cooldown`
   - Phone conflict 409 → `test_update_profile_phone_conflict_returns_409`
   - Username duplicate 409 → `test_update_profile_duplicate_username_returns_409`
   - Username invalid format 422 → `test_update_profile_invalid_username_format_returns_422`
   - Cooldown 429 + retry_after_seconds → `test_username_cooldown_returns_429`
   - Permission list format / Missing admin token → 既有用例未受本次改动影响（38 项定向测试全绿）
5. **proposal.md 目标满足**：profile 422 断裂修复、username/phone 冻结期复用、OSS 头像、安全设置 TAB 间距，均已交付；系统设置页经实测确认无需改动。
6. **delta spec 与 design doc 无矛盾**：无 superpowers Design Doc；proposal/design 已在验证阶段同步最终范围文案，与 delta spec 一致。
7. **构建/测试证据（本会话新鲜运行）**：
   - `pnpm build`（br-admin）exit 0，✓ built in 20.33s；comet check 证据已记录（cwd br-admin）
   - 定向后端：`pytest tests/test_admin_auth_api.py tests/test_api_user_profile.py tests/test_api_upload.py` → **38 passed**
   - 全量后端：`pytest -q` → 1012 passed, 15 failed, 16 skipped；**15 项失败全部归因为既有问题**（见下）
   - 浏览器实测（dev :8002）：字段顺序「头像|用户名|联系电话|昵称|邮箱|性别|生日|个性签名」✓；下拉「个人设置」点击跳转 `/setting/account` ✓；右上角展示头像（空则回退 logo）+ 昵称「超级管理员」（昵称优先、空回退 username）✓；PUT /profile 200 ✓；安全设置 TAB 间距 12px ✓

## 既有失败归因（与本 change 无关）

在改动前提交 61d9501 的临时 worktree 复跑验证：

- `test_activity_coupon_campaign`（2）、`test_admin_user_management::test_update_user_multiple_fields`（1，断言陈旧 `mobile` 键）、`test_coupon_service::TestAvailableCouponsForBooking`（8）→ pre-head 同样 11 failed，完全一致
- `test_api_booking::test_cancel_booking_refund_tiers[12-2h_24h-...]`（1）→ pre-head 同样失败（时刻相关陈旧用例，取消返回 400）
- `test_models_import::TestCourseModel`（3）→ 断言 Course 表 `teacher_id/price` 列，属 d1048ad 课时迁移后的陈旧 fixture；本 diff 未触及任何 model 文件

## WARNING / SUGGESTION

- WARNING（不阻塞，记录）：上述 15 项既有失败建议另开 change 清理陈旧测试（coupon/activity/admin-user/models-fixture/booking 时刻依赖）。
- SUGGESTION：BasicSetting 冻结期提示按 UTC 服务器时间计算剩余天数，与 C 端口径一致，无需处理。

## 偏差记录

- 验证阶段按用户追加要求微调 Header 名称展示优先级（昵称 → username），已实现、`pnpm build` 通过、浏览器复验并提交（commit 见 git log）；同步刷新 build 证据。
- proposal.md / design.md 文案在验证阶段同步为最终交付范围（电话必填口径、头像置顶教师页 UI、Header 修复、昵称优先展示）。
