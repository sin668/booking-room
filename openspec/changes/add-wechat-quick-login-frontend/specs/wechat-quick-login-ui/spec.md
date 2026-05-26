## ADDED Requirements

### Requirement: WeChat quick login entry
小程序登录页 SHALL 提供微信快速登录入口，并启动真实的微信小程序登录流程，而不是展示占位提示。

#### Scenario: Start WeChat login from login page
- **GIVEN** 用户停留在登录页且已勾选用户协议
- **WHEN** 用户点击“微信”登录入口
- **THEN** 小程序 SHALL 调用微信登录能力获取登录 code
- **AND** 微信登录入口 SHALL 在流程完成前进入加载或禁用状态

#### Scenario: Block WeChat login without agreement
- **GIVEN** 用户停留在登录页且未勾选用户协议
- **WHEN** 用户点击“微信”登录入口
- **THEN** 小程序 SHALL NOT 调用微信登录能力
- **AND** 页面 SHALL 展示“请先同意用户协议”

#### Scenario: Unsupported runtime
- **GIVEN** 当前运行环境不支持微信小程序登录
- **WHEN** 用户点击“微信”登录入口
- **THEN** 页面 SHALL 展示明确的不支持提示
- **AND** 手机号密码登录 SHALL 保持可用

### Requirement: WeChat login session persistence
小程序 SHALL 通过认证 API 模块换取微信登录 code，并使用现有用户 store 的 token 处理逻辑保存认证会话。

#### Scenario: Successful WeChat token exchange
- **GIVEN** 微信登录能力返回有效登录 code
- **WHEN** 前端调用微信登录换取接口并收到 token 响应
- **THEN** 用户 store SHALL 保存 `access_token`
- **AND** 用户 store SHALL 在响应包含 `refresh_token` 时保存它
- **AND** 用户 store SHALL 拉取当前用户资料
- **AND** 页面 SHALL 使用与手机号密码登录一致的登录后跳转行为

#### Scenario: WeChat login returns user without phone
- **GIVEN** 微信快速登录成功
- **AND** 当前用户资料中的 `phone` 为 null
- **WHEN** 前端展示登录后的个人资料或设置页
- **THEN** 页面 SHALL 展示手机号未绑定状态
- **AND** 页面 SHALL 提供手机号绑定入口

#### Scenario: Backend exchange fails
- **GIVEN** 后端拒绝微信登录 code 或返回认证错误
- **WHEN** 前端收到失败 API 响应
- **THEN** 前端 SHALL NOT 保存新 token
- **AND** 页面 SHALL 优先展示后端返回的错误详情
- **AND** 手机号密码登录 SHALL 保持可用

### Requirement: WeChat phone binding UI
小程序 SHALL 提供手机号绑定交互，优先使用微信手机号授权，并在失败时允许短信备用绑定。

#### Scenario: Bind phone by WeChat authorization
- **GIVEN** 当前用户已登录且手机号未绑定
- **WHEN** 用户点击手机号绑定入口并同意微信手机号授权
- **THEN** 小程序 SHALL 提交微信手机号授权 code 到后端
- **AND** 绑定成功后 SHALL 刷新当前用户资料

#### Scenario: Fall back to SMS binding
- **GIVEN** 微信手机号授权失败或用户拒绝授权
- **WHEN** 用户选择短信备用绑定
- **THEN** 小程序 SHALL 展示手机号和短信验证码输入流程
- **AND** 绑定成功后 SHALL 刷新当前用户资料

#### Scenario: Account merge returns new token
- **GIVEN** 手机号绑定触发账号合并
- **WHEN** 后端返回主账号的新 token 响应
- **THEN** 用户 store SHALL 替换本地 token
- **AND** 用户 store SHALL 拉取主账号当前用户资料
- **AND** 页面 SHALL 展示绑定成功

### Requirement: WeChat login retry safety
小程序 SHALL 在微信登录请求进行中阻止重复提交。

#### Scenario: Duplicate tap during loading
- **GIVEN** 微信登录请求正在进行中
- **WHEN** 用户再次点击微信登录入口
- **THEN** 前端 SHALL 忽略重复点击
- **AND** 只 SHALL 提交一次后端 code 换取请求
