## Why

小程序登录页已经展示“微信”第三方登录入口，但当前只提示“暂未开放”。实现微信快速登录、OpenID 绑定和手机号绑定闭环，可以降低首次登录门槛，并支撑依赖 `wechat_openid` 的钱包充值、支付和账号识别流程。

## What Changes

- 将微信登录从前端占位能力扩展为端到端认证能力。
- 后端新增微信 code 换取逻辑，调用微信 `jscode2session` 获取 `openid/session_key`。
- 微信新用户首次登录时创建 `phone = null` 的 app 用户，并把 `openid` 写入 `users.wechat_openid`。
- 已绑定 `openid` 的用户再次微信登录时直接签发与现有登录一致的 token。
- 新增手机号绑定流程：优先微信手机号授权，短信验证码绑定作为备用。
- 手机号已属于已有账号时，允许把无手机号微信临时账号合并到已有手机号账号，并把 `wechat_openid` 绑定到主账号。
- 前端微信入口调用真实登录流程，登录后如 `phone = null`，在设置页或需要手机号的业务点引导绑定。
- 更新 `docs/api.md` 和 OpenSpec 规格，覆盖微信登录、手机号绑定、账号合并、错误码和回滚方案。
- 回滚方案：关闭微信登录入口和后端微信接口，保留手机号登录；已写入的 `users.wechat_openid` 不删除，避免破坏已有绑定关系。

## Capabilities

### New Capabilities
- `wechat-quick-login-ui`: 覆盖小程序微信快速登录入口、登录后手机号缺失提示、手机号绑定入口、绑定成功后的资料刷新和错误反馈。
- `wechat-phone-binding`: 覆盖微信手机号授权绑定、短信备用绑定、手机号已存在时的账号合并、冲突处理和安全边界。

### Modified Capabilities
- `user-auth`: 增加微信 code 换取、OpenID 绑定、微信用户 token 签发、无手机号微信用户登录态和标准认证错误处理。
- `user-profile-api`: 当前用户资料需要允许 `phone = null`，并暴露前端判断手机号是否已绑定所需字段。

## Impact

- 后端模块：`br-server/app/api/routes/auth.py`、`br-server/app/services/auth_service.py` 或新增 `wechat_auth_service.py`、`br-server/app/schemas/user.py`、`br-server/app/core/config.py`、测试与 API 文档。
- 前端模块：`br-app/src/pages/login/login.vue`、`br-app/src/pages/settings/index.vue`、`br-app/src/api/auth.js`、`br-app/src/store/modules/user.js`。
- 数据模型：优先复用已有 `users.wechat_openid` 唯一字段和 `phone` nullable 设计；如需短期保存 `session_key`，使用 Redis，不新增数据库表。
- 外部依赖：微信小程序 `uni.login`、微信 `jscode2session`、微信手机号授权接口，以及现有短信验证码服务。
- 风险：账号合并必须限制在无手机号微信临时账号到已有手机号账号，避免误迁移钱包、订单、优惠券等资产。
