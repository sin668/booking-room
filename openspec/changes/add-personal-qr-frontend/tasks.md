## 1. 后端 Schema 与 Token 工具

- [ ] 1.1 创建 `br-server/app/schemas/booking_verification.py`，定义 `BookingVerificationBookingSummary`、`BookingVerificationTokenResponse`、`BookingVerificationDetailResponse`、`BookingVerificationConfirmResponse`，字段覆盖 booking id、用户展示信息、门店、座位、日期、时间段、金额、状态、`can_verify`、`token`、`expires_at`、`verify_url`，并使用 `ConfigDict(from_attributes=True)`。
- [ ] 1.2 在 `br-server/app/services/booking_verification_service.py` 中定义异常类：`NoVerifiableBookingError`、`InvalidVerificationTokenError`、`ExpiredVerificationTokenError`、`BookingAlreadyVerifiedError`、`BookingNotVerifiableError`，保持 route 层可映射到 404、400、410、409。
- [ ] 1.3 实现 token payload 结构：`booking_id`、`user_id`、`iat`、`nonce`；使用项目已有 `python-jose` 依赖签发 JWT，复用 `settings.SECRET_KEY`，过期时间固定 5 分钟。
- [ ] 1.4 实现 `_create_verification_token(booking_id: int, user_id: str, now: datetime) -> tuple[str, datetime]`，返回 token 和 `expires_at`。
- [ ] 1.5 实现 `_decode_verification_token(token: str, now: datetime) -> VerificationTokenPayload`，校验签名、过期时间和必要字段，过期抛 `ExpiredVerificationTokenError`，其他解析失败抛 `InvalidVerificationTokenError`。

## 2. 后端 Service 层

- [ ] 2.1 在 `booking_verification_service.py` 实现 `_build_booking_summary(booking, seat, room) -> BookingVerificationBookingSummary`，只返回核销页需要的安全展示字段，不直接复用普通用户 booking response。
- [ ] 2.2 实现 `issue_verification_token(db: AsyncSession, user_id: uuid.UUID, frontend_base_url: str | None = None) -> BookingVerificationTokenResponse`：查询当前用户 `confirmed` booking，按日期/开始时间选择最合适的一条，关联 seat、room，返回 token、`expires_at`、`verify_url` 和 booking 摘要；无记录时抛 `NoVerifiableBookingError`。
- [ ] 2.3 实现 `inspect_verification_token(db: AsyncSession, token: str) -> BookingVerificationDetailResponse`：解析 token，加载 booking、seat、room，返回 `can_verify = booking.status == "confirmed"`；token 过期、无效、booking 不存在时分别抛对应异常。
- [ ] 2.4 实现 `confirm_verification(db: AsyncSession, token: str) -> BookingVerificationConfirmResponse`：重新解析 token、重新加载 booking，只有 `confirmed` 能更新为 `completed`，`completed` 抛 `BookingAlreadyVerifiedError`，`cancelled` 或其他状态抛 `BookingNotVerifiableError`。
- [ ] 2.5 确认 service 不新增 token 数据表；一次性核销语义由 booking 状态保证，重复提交必须因状态已变为 `completed` 而失败。

## 3. 后端 Routes 与注册

- [ ] 3.1 创建 `br-server/app/api/routes/booking_verification.py`，`router = APIRouter(prefix="/api/v1/booking-verifications", tags=["booking-verifications"])`。
- [ ] 3.2 添加 `POST /token`：依赖 `get_current_user_id`，调用 `issue_verification_token`，无可核销 booking 返回 404，其他业务错误返回合适 HTTP 错误。
- [ ] 3.3 添加 `GET /{token}`：依赖 `get_current_admin`，调用 `inspect_verification_token`；过期 token 返回 410，已核销/不可核销返回 409 或 `can_verify: false` 响应，未授权由 `get_current_admin` 返回 401。
- [ ] 3.4 添加 `POST /{token}/confirm`：依赖 `get_current_admin`，调用 `confirm_verification`；成功返回核销后的 booking 信息，重复核销返回 409，过期返回 410，无效 token 返回 400。
- [ ] 3.5 在 `br-server/app/main.py` 引入并 `include_router(booking_verification_router)`，放在现有普通业务路由附近。
- [ ] 3.6 明确本阶段“员工/管理员权限”复用现有 `X-Admin-Token` / `get_current_admin` 机制，不引入新的员工账号或 RBAC 表。

## 4. 后端测试

- [ ] 4.1 创建 `br-server/tests/test_booking_verification_service.py`，准备 fixtures：用户 UUID、study room、seat、`confirmed` booking、`cancelled` booking、`completed` booking。
- [ ] 4.2 添加 service 测试：`issue_verification_token` 在有 `confirmed` booking 时返回 token、5 分钟 `expires_at`、包含 `/pages/verify-booking/index?token=` 的 `verify_url` 和 booking 摘要。
- [ ] 4.3 添加 service 测试：无 `confirmed` booking 时 `issue_verification_token` 抛 `NoVerifiableBookingError`。
- [ ] 4.4 添加 service 测试：篡改 token 调用 `inspect_verification_token` 抛 `InvalidVerificationTokenError`。
- [ ] 4.5 添加 service 测试：过期 token 调用 `inspect_verification_token` 和 `confirm_verification` 均抛 `ExpiredVerificationTokenError`。
- [ ] 4.6 添加 service 测试：`confirm_verification` 将 `confirmed` booking 更新为 `completed` 并返回 `can_verify: false` 或成功状态。
- [ ] 4.7 添加 service 测试：已 `completed` booking 重复核销抛 `BookingAlreadyVerifiedError`，`cancelled` booking 核销抛 `BookingNotVerifiableError`。
- [ ] 4.8 创建 `br-server/tests/test_api_booking_verification.py`，覆盖用户签发 token、管理员解析 token、管理员确认核销、未登录签发失败、无 admin token 解析/核销失败、过期 token 返回 410、重复核销返回 409。
- [ ] 4.9 运行 `cd br-server && pytest tests/test_booking_verification_service.py tests/test_api_booking_verification.py tests/test_api_booking.py -q`，确保新增核销逻辑不破坏现有 booking API。

## 5. API 文档

- [ ] 5.1 更新 `docs/api.md`，新增 `Booking Verification / 到店核销` 小节，记录三个接口：`POST /api/v1/booking-verifications/token`、`GET /api/v1/booking-verifications/{token}`、`POST /api/v1/booking-verifications/{token}/confirm`。
- [ ] 5.2 文档中明确认证要求：签发接口使用普通用户 Bearer token；解析和确认接口使用现有管理员凭证 `X-Admin-Token`。
- [ ] 5.3 文档中列出错误码：401 未认证/无管理员权限、404 暂无可核销预约、400 无效 token、410 token 已过期、409 已核销或不可核销状态。
- [ ] 5.4 文档示例响应必须包含 `expires_at`、`verify_url`、booking 摘要和 `can_verify` 字段，字段名与 schema 保持一致。

## 6. 前端 API 层

- [ ] 6.1 创建 `br-app/src/api/bookingVerifications.js`，从 `@/utils/request` 引入 `get`、`post`。
- [ ] 6.2 实现 `issueVerificationToken()`，调用 `post('/api/v1/booking-verifications/token')`，路径不带尾斜杠。
- [ ] 6.3 实现 `inspectVerificationToken(token)`，调用 `get(\`/api/v1/booking-verifications/${encodeURIComponent(token)}\`)`，路径不带尾斜杠。
- [ ] 6.4 实现 `confirmVerification(token)`，调用 `post(\`/api/v1/booking-verifications/${encodeURIComponent(token)}/confirm\`)`，路径不带尾斜杠。
- [ ] 6.5 如 H5 员工页无法通过 Bearer token 携带管理员权限，新增最小请求 header 支持方案或在页面中明确使用已有登录态；不得绕过后端 `get_current_admin`。

## 7. 用户端个人学习码页面

- [ ] 7.1 在 `br-app/src/pages.json` 注册 `pages/qrcode/index`，标题为 `我的学习码`。
- [ ] 7.2 修改 `br-app/src/pages/profile/index.vue`，在“会员服务”区域添加“我的学习码”菜单项，点击 `uni.navigateTo({ url: '/pages/qrcode/index' })`。
- [ ] 7.3 创建 `br-app/src/pages/qrcode/index.vue`，采用现有 Vue/SCSS 单文件页面风格，视觉参考 `prototype/qrcode.html` 的用户信息、白色二维码卡片、会员/预约信息卡片和安全提示。
- [ ] 7.4 页面加载时调用 `issueVerificationToken()`；成功后渲染用户身份、booking 摘要、二维码、`核销码 X:XX 后失效` 倒计时和“刷新核销码”按钮。
- [ ] 7.5 实现二维码渲染：优先使用兼容 uni-app H5/小程序的轻量库或 canvas 工具；不得使用原型中的伪二维码网格替代真实可扫码二维码。
- [ ] 7.6 处理空态：接口返回 404 时展示 `暂无可核销预约`，提供返回预约/刷新入口。
- [ ] 7.7 处理错误态：网络错误或 token 生成失败时展示失败文案和重试按钮；未登录时跳转或提示登录。
- [ ] 7.8 移除或弱化“保存到相册/分享给好友”：如保留，必须在按钮附近标注“核销码 5 分钟内有效”，避免用户误以为截图长期可用。

## 8. 员工 H5 核销页面

- [ ] 8.1 在 `br-app/src/pages.json` 注册 `pages/verify-booking/index`，标题为 `预约核销`。
- [ ] 8.2 创建 `br-app/src/pages/verify-booking/index.vue`，在 `onLoad(options)` 或等价生命周期中读取 `options.token`。
- [ ] 8.3 页面加载时调用 `inspectVerificationToken(token)`，展示用户安全信息、门店、座位、日期、时间段、金额、状态和 `can_verify`。
- [ ] 8.4 实现状态视图：加载中、未授权/未登录、token 过期、token 无效、已核销、已取消/不可核销、可核销、核销成功。
- [ ] 8.5 在可核销状态显示主按钮 `确认核销`；点击后调用 `confirmVerification(token)`，请求中禁用按钮，成功后锁定成功状态，失败时按错误码展示原因。
- [ ] 8.6 确认页面在微信 H5 URL 形态下可读 token：`/#/pages/verify-booking/index?token=...`，并与后端返回的 `verify_url` 约定一致。

## 9. 前端验证

- [ ] 9.1 运行 `cd br-app && npm run build:h5`，确认 H5 构建通过。
- [ ] 9.2 如新增二维码依赖，运行 `cd br-app && npm run build:mp-weixin`，确认微信小程序构建不因依赖或 canvas API 失败。
- [ ] 9.3 手动验证用户端：有可核销 booking 时二维码渲染，倒计时递减，刷新可重新签发 token；无 booking 时展示空态。
- [ ] 9.4 手动验证员工端：使用后端返回的 `verify_url` 打开核销页，能展示 booking，点击“确认核销”后成功，再次点击或刷新后显示已核销/不可重复核销。
- [ ] 9.5 手动验证错误态：缺 token、无管理员凭证、过期 token、无效 token、cancelled booking 均有明确文案。

## 10. 收尾与代码审查

- [ ] 10.1 运行 `cd br-server && pytest -q`，确认后端全量测试通过。
- [ ] 10.2 运行 OpenSpec 状态检查：`openspec status --change add-personal-qr-frontend`，确认 artifacts 仍 complete。
- [ ] 10.3 代码审查后端分层：routes 只做 HTTP 映射，service 负责业务规则，schemas 负责响应结构，token 工具不泄漏到前端。
- [ ] 10.4 代码审查权限边界：token 签发只允许本人，token 解析和确认只允许管理员，确认核销必须二次查询 booking 状态。
- [ ] 10.5 代码审查前端体验：页面文案不鼓励保存长期二维码，按钮在加载/成功/失败状态不重复提交，移动端布局不溢出。
- [ ] 10.6 提交实现时建议按后端基础、后端 API、后端测试、前端 API、用户 QR 页、员工核销页、文档验证分批提交。
