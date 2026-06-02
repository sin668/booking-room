## ADDED Requirements

### Requirement: Settings page WeChat binding status
系统 SHALL 支持设置页展示当前用户微信绑定状态，并允许未绑定用户从设置页发起绑定。

#### Scenario: Display bound WeChat status
- **GIVEN** 用户已登录且账号已绑定微信 OpenID
- **WHEN** 用户打开“我的设置”页面
- **THEN** “微信绑定”入口 SHALL 展示“已绑定”
- **AND** 用户点击后 SHALL 展示已绑定说明，不重复发起绑定请求

#### Scenario: Display unbound WeChat status
- **GIVEN** 用户已登录且账号未绑定微信 OpenID
- **WHEN** 用户打开“我的设置”页面
- **THEN** “微信绑定”入口 SHALL 展示“未绑定”
- **AND** 用户点击后 SHALL 可发起微信手机号授权绑定流程

### Requirement: Settings page WeChat binding feedback
设置页微信绑定流程 SHALL 复用现有微信手机号授权绑定和短信兜底能力，并提供清晰错误反馈。

#### Scenario: Bind WeChat phone from settings
- **GIVEN** 用户已登录且账号未绑定手机号或微信
- **AND** 微信手机号授权 code 有效
- **WHEN** 用户从设置页提交微信绑定请求
- **THEN** 系统 SHALL 绑定手机号或安全合并临时微信账号
- **AND** 小程序 SHALL 刷新账号安全摘要

#### Scenario: Show WeChat service unavailable
- **GIVEN** 微信登录或手机号授权配置不可用
- **WHEN** 用户从设置页发起微信绑定
- **THEN** 系统 SHALL 返回 HTTP 503
- **AND** 小程序 SHALL 展示“微信绑定暂不可用”
- **AND** 小程序 SHALL 提供短信验证码绑定兜底入口（如当前场景支持）

#### Scenario: Show WeChat binding conflict
- **GIVEN** 目标手机号已绑定其他微信账号或当前账号不允许自动合并
- **WHEN** 用户从设置页提交微信绑定请求
- **THEN** 系统 SHALL 返回 HTTP 409
- **AND** 小程序 SHALL 展示冲突原因
- **AND** 系统 SHALL NOT 覆盖已有微信绑定
