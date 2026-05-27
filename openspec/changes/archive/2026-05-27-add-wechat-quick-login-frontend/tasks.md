## 1. 后端配置与契约

- [x] 1.1 在 `br-server/app/core/config.py` 增加微信小程序登录配置项：启用开关、AppID、Secret、API base URL、请求超时时间，并提供缺失配置检测方法。
- [x] 1.2 在 `br-server/app/schemas/user.py` 新增微信登录请求 schema，字段包含 `code`，并限制为空字符串。
- [x] 1.3 在 `br-server/app/schemas/user.py` 新增微信手机号授权绑定请求 schema，字段包含 `code`，并限制为空字符串。
- [x] 1.4 在 `br-server/app/schemas/user.py` 新增短信绑定请求 schema，字段包含 `phone` 和 `sms_code`，复用现有手机号和 6 位验证码校验规则。
- [x] 1.5 明确绑定/合并成功响应：最终实现统一返回 `TokenResponse`，并已同步更新 specs 和 `docs/api.md`。
- [x] 1.6 检查 `UserProfileResponse`、`UserResponse` 和前端调用方，确认 `phone` 允许为 null，不因微信新用户无手机号而序列化失败。

## 2. 后端微信 API Client

- [x] 2.1 新增 `br-server/app/services/wechat_auth_client.py`，封装微信 `jscode2session` 调用。
- [x] 2.2 在微信 client 中实现配置缺失、HTTP 失败、微信错误码、响应缺字段的统一异常类型。
- [x] 2.3 在微信 client 中实现手机号授权 code 换取手机号的调用方法。
- [x] 2.4 为微信 client 增加可注入 HTTP 传输或测试替身，确保单元测试不访问真实微信服务。
- [x] 2.5 新增 `br-server/tests/test_wechat_auth_client.py`，覆盖成功响应、微信错误码、缺少 openid/session_key、缺少手机号、配置缺失和 HTTP 失败。

## 3. 后端微信认证服务

- [x] 3.1 新增 `br-server/app/services/wechat_auth_service.py`，负责微信登录、手机号绑定、账号合并和 token 签发编排。
- [x] 3.2 抽取或复用现有 token 签发逻辑，避免 `AuthService.register()`、`AuthService.login()` 和 `WechatAuthService` 重复创建 access/refresh token。
- [x] 3.3 实现微信登录：OpenID 已绑定用户时校验用户状态并签发 token。
- [x] 3.4 实现微信登录：OpenID 未绑定时创建 `phone = null` 的 app 用户，写入 `users.wechat_openid`，生成 username 和默认昵称。
- [x] 3.5 实现 `session_key` 服务端缓存，使用 Redis，TTL 控制在 10 到 30 分钟，不返回给前端。
- [x] 3.6 实现微信登录错误映射：无效/过期 code 返回 400，配置缺失或微信服务不可用返回 503，禁用账号返回 403。
- [x] 3.7 新增 `br-server/tests/test_wechat_auth_service_login.py`，覆盖首次微信登录、再次微信登录、禁用账号、无效 code、服务不可用、session_key 缓存和 token 响应。

## 4. 后端手机号绑定与账号合并

- [x] 4.1 实现微信手机号授权绑定：用微信手机号 code 换取手机号，手机号未占用时写入当前用户 `phone`。
- [x] 4.2 实现短信备用绑定：复用现有 `SMSService.verify_code()` 校验手机号和验证码，校验通过后走同一绑定服务。
- [x] 4.3 实现手机号已存在时的受限合并判断：当前用户必须是 `phone IS NULL` 且 `wechat_openid` 非空的微信临时账号。
- [x] 4.4 合并前检查目标手机号账号是否已经绑定不同 `wechat_openid`；如已绑定，返回 409，不覆盖。
- [x] 4.5 合并前检查微信临时账号是否已有余额、订单、优惠券或其他资产；如存在资产，返回 409，不自动迁移。
- [x] 4.6 合并成功时把当前 `wechat_openid` 写入已有手机号用户，并清除或禁用微信临时账号，确保该临时账号不可继续登录。
- [x] 4.7 合并成功时撤销微信临时账号 refresh token，并签发已有手机号主账号的新 token。
- [x] 4.8 新增 `br-server/tests/test_wechat_phone_binding.py`，覆盖微信授权绑定新手机号、短信绑定新手机号、微信手机号 code 失败、短信验证码失败、合并成功、OpenID 冲突、临时账号有资产、非临时账号绑定已存在手机号。

## 5. 后端路由与 API 文档

- [x] 5.1 在 `br-server/app/api/routes/auth.py` 新增 `POST /api/v1/auth/wechat-login`，注入 DB、Redis、settings 和微信认证服务。
- [x] 5.2 在微信登录路由中沿用现有 refresh token cookie 设置逻辑，保持前端 token 处理一致。
- [x] 5.3 在 `br-server/app/api/routes/auth.py` 新增 `POST /api/v1/auth/wechat/bind-phone`，要求 Bearer Token，处理微信手机号授权绑定。
- [x] 5.4 在 `br-server/app/api/routes/auth.py` 新增 `POST /api/v1/auth/wechat/bind-phone/sms`，要求 Bearer Token，处理短信备用绑定。
- [x] 5.5 更新 `docs/api.md`：补充三个新接口的认证方式、请求体、成功响应、400/401/403/409/503 错误示例和回滚说明。
- [x] 5.6 新增或更新 API 路由测试，覆盖 cookie 设置、认证缺失、错误码映射、合并后返回主账号 token。

## 6. 前端微信快速登录

- [x] 6.1 在 `br-app/src/api/auth.js` 新增 `wechatLogin(data)`、`bindWechatPhone(data)`、`bindPhoneBySms(data)` API 方法。
- [x] 6.2 在 `br-app/src/store/modules/user.js` 新增 `wechatLogin(code)` action，复用现有 token 保存、refresh token 保存和 `fetchUserInfo()`。
- [x] 6.3 在 `br-app/src/store/modules/user.js` 新增手机号绑定 action，支持绑定成功后刷新用户资料。
- [x] 6.4 在绑定接口返回新 token 时，store 需要替换本地 token、refresh token，并重新拉取主账号资料。
- [x] 6.5 更新 `br-app/src/pages/login/login.vue`：微信入口调用 `uni.login({ provider: 'weixin' })`，不再显示“暂未开放”。
- [x] 6.6 登录页微信流程必须处理协议未勾选、不支持环境、微信 code 获取失败、后端失败、加载态和重复点击。
- [x] 6.7 保持手机号密码登录、注册、Apple/QQ 占位入口行为不变。

## 7. 前端手机号绑定体验

- [x] 7.1 在设置页或个人资料页展示手机号未绑定状态，当前用户 `phone = null` 时提供绑定入口。
- [x] 7.2 优先实现微信手机号授权绑定入口，提交授权 code 到 `POST /api/v1/auth/wechat/bind-phone`。
- [x] 7.3 微信手机号授权失败或用户拒绝时，提供短信备用绑定表单。
- [x] 7.4 短信备用绑定需要支持发送验证码、填写手机号和验证码、提交 `POST /api/v1/auth/wechat/bind-phone/sms`。
- [x] 7.5 绑定成功后刷新当前用户资料，并清除绑定表单状态。
- [x] 7.6 账号合并成功且后端返回主账号 token 时，前端替换登录态并展示绑定成功。
- [x] 7.7 绑定失败时按错误码展示明确文案：授权过期、验证码无效、手机号已绑定其他微信、临时账号有资产不能自动合并、登录已过期。

## 8. OpenSpec 同步与回归验证

- [x] 8.1 如实现中确认接口路径、响应字段或合并规则发生变化，同步更新 `proposal.md`、`design.md` 和 `specs/**/*.md`。
- [x] 8.2 运行 `openspec validate add-wechat-quick-login-frontend`，确保规格仍有效。
- [x] 8.3 运行后端定向测试：微信 client、微信认证服务、手机号绑定、认证路由、现有登录/注册/refresh/logout 回归。
- [x] 8.4 运行前端构建或检查命令，优先使用 `br-app/package.json` 中已有脚本。
- [ ] 8.5 使用微信小程序工具、mock `uni.login` 或可用预览工具验证微信登录、缺手机号提示、微信手机号授权绑定、短信备用绑定、冲突提示和 token 切换。（当前 CLI 环境未连接微信开发者工具；已完成小程序构建验证）
- [x] 8.6 审查 Clean Architecture 分层：路由只处理 HTTP，service 拥有微信认证和合并规则，client 封装微信 API，前端页面只处理交互，store 统一处理登录态。
- [x] 8.7 重构实现中发现的重复 token 签发、重复 toast 文案、重复绑定流程或过大的页面逻辑。
- [x] 8.8 最终只在对应实现和验证完成后勾选本 `tasks.md` 任务。
