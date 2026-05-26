## 1. 后端微信认证基础

- [ ] 1.1 在 `br-server/app/core/config.py` 增加微信小程序登录所需配置：AppID、Secret、API base URL、开关和超时设置。
- [ ] 1.2 新增用户认证 schema：微信登录 code 请求、微信手机号授权请求、短信绑定请求、手机号绑定/合并响应。
- [ ] 1.3 新增 `WechatAuthService`，负责微信 `jscode2session`、手机号授权接口调用、错误码归一化和 Redis `session_key` 缓存。
- [ ] 1.4 抽取或复用现有 token 签发逻辑，避免 `AuthService` 和 `WechatAuthService` 重复创建 access/refresh token。
- [ ] 1.5 增加微信接口 HTTP client 的单元测试替身或注入点，确保测试不访问真实微信服务。

## 2. 后端微信快速登录

- [ ] 2.1 在 `WechatAuthService` 实现 `wechat_login(code)`：有效 code 换取 OpenID，OpenID 已绑定时签发该用户 token。
- [ ] 2.2 实现 OpenID 未绑定时创建 `phone = null` 的 app 用户，写入 `users.wechat_openid`，生成 username 和默认昵称。
- [ ] 2.3 登录时校验用户状态；`banned` 或不可登录用户返回 HTTP 403。
- [ ] 2.4 在 `br-server/app/api/routes/auth.py` 增加 `POST /api/v1/auth/wechat-login`，沿用 refresh token cookie 设置。
- [ ] 2.5 覆盖微信登录后端测试：首次登录、再次登录、无效 code、微信服务不可用、禁用用户、refresh cookie 设置。

## 3. 后端手机号绑定与账号合并

- [ ] 3.1 实现微信手机号授权绑定：后端用微信手机号 code 换取手机号，未占用时绑定到当前用户。
- [ ] 3.2 实现短信备用绑定：复用现有短信验证码校验，验证码通过后按同一绑定规则处理手机号。
- [ ] 3.3 实现受限账号合并：只允许无手机号微信临时账号合并到已有手机号账号。
- [ ] 3.4 合并前检查目标手机号账号是否已有不同 `wechat_openid`；如有则返回 HTTP 409。
- [ ] 3.5 合并前检查临时账号是否已有余额、订单、优惠券等资产；如有则返回 HTTP 409，不自动迁移。
- [ ] 3.6 合并成功后把 `wechat_openid` 写入已有手机号账号，撤销临时账号 refresh token，并让临时账号不可继续登录。
- [ ] 3.7 合并成功后签发主账号 token，前端可无缝切换到主账号登录态。
- [ ] 3.8 增加绑定和合并测试：绑定新手机号、微信授权失败、短信验证码失败、合并成功、OpenID 冲突、临时账号有资产、非临时账号绑定已有手机号。

## 4. 前端微信登录和绑定

- [ ] 4.1 在 `br-app/src/api/auth.js` 新增微信登录、微信手机号绑定、短信手机号绑定 API 方法。
- [ ] 4.2 在 `br-app/src/store/modules/user.js` 新增 `wechatLogin(code)` 和手机号绑定 action，复用 token 保存、refresh token 和 `fetchUserInfo()`。
- [ ] 4.3 更新 `br-app/src/pages/login/login.vue`：微信入口调用 `uni.login({ provider: 'weixin' })`，处理协议校验、加载态、不支持环境、失败提示和重复点击。
- [ ] 4.4 在设置页或个人资料页增加手机号未绑定提示和绑定入口，优先触发微信手机号授权，失败后提供短信备用绑定。
- [ ] 4.5 绑定接口返回主账号新 token 时，前端替换本地 token 并刷新当前用户资料。
- [ ] 4.6 保持手机号密码登录、注册、Apple/QQ 占位入口行为不变。

## 5. 文档和 OpenSpec 同步

- [ ] 5.1 更新 `docs/api.md`，补充 `POST /api/v1/auth/wechat-login`、`POST /api/v1/auth/wechat/bind-phone`、`POST /api/v1/auth/wechat/bind-phone/sms` 的请求、响应和错误码。
- [ ] 5.2 根据最终接口路径和响应字段同步更新本 change 的 `proposal.md`、`design.md` 和 `specs/**/*.md`。
- [ ] 5.3 确认 Open Questions 已全部落地：接口路径、先登录后绑定、手机号已存在时合并。

## 6. 验证和代码审查

- [ ] 6.1 运行后端定向测试：微信登录、手机号绑定、账号合并、现有手机号/密码登录和 refresh/logout 回归。
- [ ] 6.2 运行前端构建或检查命令，优先使用 `br-app` 中 `package.json` 定义的构建脚本。
- [ ] 6.3 使用微信小程序工具、mock `uni.login` 或可用预览工具验证微信登录、绑定手机号、短信备用、冲突提示和 token 切换。
- [ ] 6.4 审查 Clean Architecture 分层：路由只处理 HTTP，service 拥有微信认证和合并规则，前端页面只处理交互，store 统一处理登录态。
- [ ] 6.5 重构实现中发现的重复 token 签发、重复 toast 文案或重复绑定流程。
- [ ] 6.6 最终更新本 `tasks.md`，只在对应实现和验证完成后勾选任务。
