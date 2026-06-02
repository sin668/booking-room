## 1. 后端数据模型与迁移

- [x] 1.1 阅读现有 `br-server/app/models/user.py`、`br-server/app/schemas/user.py`、`br-server/app/services/user_profile_service.py`，确认用户状态字段、当前用户资料字段和设置页已有数据来源。
- [x] 1.2 新增实名认证模型 `UserIdentityVerification`，字段包含 `id`、`user_id`、`real_name`、`id_card_hash`、`id_card_masked`、`status`、`submitted_at`、`reviewed_at`、`created_at`、`updated_at`。
- [x] 1.3 将实名认证模型纳入 `br-server/app/models/__init__.py`，确保测试数据库和 Alembic metadata 能加载该模型。
- [x] 1.4 扩展用户状态约束，支持 `status='deleted'`；不得新增注销申请表，不得新增物理删除用户路径。
- [x] 1.5 新增 Alembic 迁移：创建 `user_identity_verifications` 表、索引和外键，并更新 `users.status` check constraint 支持 `deleted`。
- [x] 1.6 在迁移 downgrade 中恢复旧状态约束并删除实名认证表；如存在 `deleted` 用户，downgrade 前必须显式阻止或说明不可回滚，避免静默破坏数据。
- [x] 1.7 使用项目基础环境验证迁移链：`conda activate booking-room` 后运行 `alembic -c alembic.ini heads`，确认单一 head。
- [x] 1.8 使用项目基础环境验证迁移执行：`conda activate booking-room` 后运行 `alembic -c alembic.ini upgrade head`，确认迁移可应用。

## 2. 后端 Schema 与工具函数

- [x] 2.1 新增账号安全摘要响应 schema，包含手机号绑定状态、脱敏手机号、微信绑定状态、实名认证状态、脱敏身份证号、账号状态、注销风险摘要。
- [x] 2.2 新增修改密码请求/响应 schema，包含 `old_password`、`new_password`、`confirm_password`，并复用现有密码强度规则。
- [x] 2.3 新增实名认证提交/响应 schema，包含 `real_name`、`id_card_number`、`status`、`id_card_masked`，响应不得包含完整身份证号。
- [x] 2.4 新增注销账号响应 schema，包含 `status='deleted'`、`message` 和风险阻断信息；不得包含注销申请 id。
- [x] 2.5 新增或复用脱敏工具函数：手机号脱敏、身份证号脱敏、身份证号哈希；工具函数必须有确定性输出，便于测试。
- [x] 2.6 新增风险阻断原因结构，统一表达余额未清零、未完成预约、待处理支付/退款、未用卡券等阻断项。

## 3. 后端账号安全服务

- [x] 3.1 新增 `UserSecurityService.get_security_summary(user_id)`，聚合用户手机号、微信 OpenID 是否存在、实名记录、账号状态和注销风险。
- [x] 3.2 `get_security_summary` 必须只返回脱敏手机号、脱敏身份证号和状态，不返回 `password_hash`、完整身份证号、完整 OpenID、refresh token。
- [x] 3.3 新增 `UserSecurityService.change_password(user_id, data)`，先校验用户存在且未 deleted，再校验旧密码、新密码强度和确认密码。
- [x] 3.4 修改密码成功后更新 `password_hash`，并撤销该用户 refresh token；当前 access token 可保留到自然过期。
- [x] 3.5 新增 `IdentityVerificationService.submit_identity(user_id, data)`，校验姓名和身份证格式，生成身份证 hash 与脱敏号。
- [x] 3.6 实名认证本期提交成功后直接写入 `status='verified'`；如果已有 verified 记录，不允许覆盖为不同实名资料。
- [x] 3.7 新增账号注销服务方法，提交前统一检查余额、未完成预约、待处理支付/退款、未用卡券等风险。
- [x] 3.8 注销风险检查通过后只设置 `users.status='deleted'`，撤销 refresh token，保留用户历史订单、钱包流水、卡券、核销等业务记录。
- [x] 3.9 注销风险检查失败时返回 HTTP 409 语义所需的阻断原因列表，不修改用户状态。
- [x] 3.10 重构服务内共享逻辑，避免在安全摘要和注销流程中重复实现余额、订单、卡券风险查询。

## 4. 后端路由与认证规则

- [x] 4.1 在当前用户路由中新增 `GET /api/v1/users/me/security`，返回账号安全摘要。
- [x] 4.2 新增 `POST /api/v1/users/me/password`，处理当前用户修改密码。
- [x] 4.3 新增 `POST /api/v1/users/me/identity-verification`，处理当前用户实名认证提交。
- [x] 4.4 新增 `POST /api/v1/users/me/deactivation`，执行当前用户注销；虽然路径保留 deactivation 命名，但行为是设置 `status='deleted'`，不创建申请记录。
- [x] 4.5 所有新增接口必须使用 `get_current_user_id`，不得接受客户端传入任意 `user_id`。
- [x] 4.6 更新手机号/用户名密码登录逻辑，拒绝 `status='deleted'` 用户登录并返回 HTTP 403。
- [x] 4.7 更新微信快速登录逻辑，拒绝绑定到 `status='deleted'` 用户的 OpenID 登录并返回 HTTP 403。
- [x] 4.8 更新 refresh token 逻辑，拒绝 `status='deleted'` 用户刷新会话，不签发新 token。
- [x] 4.9 保持现有微信手机号绑定接口不搬迁；设置页微信绑定只复用现有 `/api/v1/auth/wechat/bind-phone` 和短信兜底接口。

## 5. 后端测试

- [x] 5.1 新增账号安全摘要 API 测试：已登录成功、未登录返回 401、响应不包含敏感字段。
- [x] 5.2 新增账号安全摘要聚合测试：未绑定微信/已绑定微信、未实名/已实名、active/deleted 状态均能正确返回。
- [x] 5.3 新增修改密码测试：旧密码正确时成功更新 hash 并撤销 refresh token。
- [x] 5.4 新增修改密码测试：旧密码错误、新密码弱、确认密码不一致时拒绝，且不更新 `password_hash`。
- [x] 5.5 新增实名认证测试：合法姓名和身份证提交成功，返回 `verified` 和脱敏身份证号。
- [x] 5.6 新增实名认证测试：非法身份证、空姓名、重复 verified 实名资料覆盖请求均被拒绝。
- [x] 5.7 新增注销账号测试：无风险用户提交后 `users.status` 变为 `deleted`，用户记录仍存在。
- [x] 5.8 新增注销账号风险阻断测试：余额大于 0、存在未完成预约、存在待处理支付/退款、存在未用卡券时返回 409 且状态不变。
- [x] 5.9 新增认证守卫测试：`deleted` 用户不能手机号/用户名登录、不能微信登录、不能 refresh token。
- [x] 5.10 运行后端目标测试：`pytest tests/test_api_user_profile.py tests/test_api_auth.py tests/test_wechat_auth_service_login.py` 以及新增账号安全测试文件。

## 6. 前端 API 与状态管理

- [x] 6.1 新增 `br-app/src/api/accountSecurity.js`，封装账号安全摘要、修改密码、实名认证、注销账号四类接口。
- [x] 6.2 在前端新增账号安全状态格式化函数：微信绑定状态、实名状态、账号状态、风险阻断文案。
- [x] 6.3 更新设置页加载流程，进入页面时请求账号安全摘要；失败时保留入口并显示空状态或 `--`。
- [x] 6.4 修改密码、微信绑定、实名认证、注销账号任一流程成功后，刷新账号安全摘要。
- [x] 6.5 确认前端请求封装能正确处理账号安全接口的 200/201/204 成功响应，以及 400/401/403/409/422 错误响应。

## 7. 前端设置页交互

- [x] 7.1 将“修改密码”占位提示替换为真实表单入口，表单包含旧密码、新密码、确认新密码、提交按钮和 loading 状态。
- [x] 7.2 修改密码表单在前端校验确认密码一致；后端返回旧密码错误、弱密码等错误时展示明确提示并保持表单可编辑。
- [x] 7.3 将“微信绑定”占位提示替换为状态化入口：已绑定展示说明，未绑定打开现有微信手机号授权/短信兜底绑定流程。
- [x] 7.4 将“实名认证”占位提示替换为实名表单入口，包含真实姓名、身份证号、提交按钮、提交成功后的已认证状态和脱敏身份证展示。
- [x] 7.5 将“注销账号”占位提示替换为注销说明与风险检查流程，展示余额、预约、卡券、支付/退款等阻断原因。
- [x] 7.6 注销账号在无风险时必须二次确认；确认成功后调用注销接口，清除本地登录态并跳转登录页。
- [x] 7.7 设置页账号与安全分组右侧展示状态摘要：“已绑定/未绑定”、“已认证/未认证”，注销入口保持危险色文案。
- [x] 7.8 UI 保持现有设置页风格：浅灰背景、白色圆角分组、紧凑行高、右侧状态文本、底部安全区留白。

## 8. 前端测试与体验验证

- [x] 8.1 扩展 `br-app/scripts/test-refactored-page-logic.js` 或新增脚本，覆盖账号安全 API wrapper 和状态格式化函数。
- [x] 8.2 增加前端逻辑测试：修改密码确认密码不一致、实名身份证格式错误、注销风险阻断文案映射。
- [x] 8.3 使用基础环境 `nvm use v22.22.0` 后运行 `npm run test:refactor`。
- [ ] 8.4 启动 H5 或微信小程序开发环境，手动验证设置页四个入口均能打开且状态文案不溢出。
- [ ] 8.5 手动验证注销成功后本地 token 被清除，返回登录页，重新登录 deleted 账号被拒绝。

## 9. 文档、审查与收尾

- [x] 9.1 更新 `docs/api.md`，补充账号安全摘要、修改密码、实名认证、注销账号接口的路径、请求、响应和错误码。
- [x] 9.2 审查后端分层：route 只处理 HTTP，service 处理业务规则，model 只描述持久化，schema 不泄露敏感字段。
- [x] 9.3 审查前端分层：页面负责交互状态，API 文件负责请求，格式化/错误映射逻辑避免重复。
- [x] 9.4 确认实现中没有新增注销申请表，没有调用物理删除用户，没有返回完整身份证号或完整 OpenID。
- [x] 9.5 运行 `openspec status --change account-security-settings`，确认 proposal/design/specs/tasks 仍完整。
- [x] 9.6 运行 `openspec validate account-security-settings --strict` 或项目可用的等价校验命令，修复 OpenSpec 格式问题。
- [x] 9.7 整理最终验证记录：后端 pytest、前端 npm 测试、Alembic heads/upgrade、设置页手动验证。
