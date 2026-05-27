## Purpose
Define WeChat phone authorization, SMS fallback binding, and safe temporary WeChat account merge behavior.

## Requirements

### Requirement: WeChat phone authorization binding
系统 SHALL 支持已登录用户通过微信手机号授权绑定手机号。

#### Scenario: Bind unused phone from WeChat authorization
- **GIVEN** 用户已登录且当前账号未绑定手机号
- **AND** 微信手机号授权 code 有效并换取到手机号 `13800138000`
- **AND** 该手机号未被任何用户占用
- **WHEN** 用户提交手机号绑定请求
- **THEN** 系统 SHALL 将该手机号写入当前用户 `phone`
- **AND** 系统 SHALL 返回当前用户新的 token 响应

#### Scenario: Reject invalid WeChat phone code
- **GIVEN** 用户已登录
- **AND** 微信手机号授权 code 无效、过期或被微信接口拒绝
- **WHEN** 用户提交手机号绑定请求
- **THEN** 系统 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 提示“手机号授权已过期，请重试”

### Requirement: SMS fallback phone binding
系统 SHALL 支持已登录用户通过手机号和短信验证码作为备用路径绑定手机号。

#### Scenario: Bind unused phone by SMS
- **GIVEN** 用户已登录且当前账号未绑定手机号
- **AND** 手机号 `13800138000` 未被占用
- **AND** 短信验证码校验通过
- **WHEN** 用户提交短信绑定请求
- **THEN** 系统 SHALL 将该手机号写入当前用户 `phone`

#### Scenario: Reject invalid SMS code
- **GIVEN** 用户已登录
- **AND** 短信验证码无效或已过期
- **WHEN** 用户提交短信绑定请求
- **THEN** 系统 SHALL 返回 HTTP 400
- **AND** 响应 SHALL 使用现有短信验证码错误语义

### Requirement: Merge temporary WeChat user into existing phone user
系统 SHALL 在手机号已属于现有账号时，允许将无手机号微信临时账号合并到已有手机号账号。

#### Scenario: Merge temporary WeChat user into phone user
- **GIVEN** 当前登录用户 `phone` 为 null
- **AND** 当前登录用户 `wechat_openid` 非空
- **AND** 绑定手机号已属于另一个 app 用户
- **AND** 该手机号用户尚未绑定其他 `wechat_openid`
- **AND** 当前临时微信用户没有余额、订单、优惠券等资产
- **WHEN** 用户提交手机号绑定请求
- **THEN** 系统 SHALL 将当前 `wechat_openid` 写入已有手机号用户
- **AND** 系统 SHALL 失效当前临时微信用户的 refresh token
- **AND** 系统 SHALL 使当前临时微信用户不可继续登录
- **AND** 系统 SHALL 为已有手机号用户签发新的 token 响应

#### Scenario: Reject merge when phone user has another OpenID
- **GIVEN** 当前登录用户为无手机号微信临时账号
- **AND** 绑定手机号已属于另一个用户
- **AND** 该手机号用户已绑定不同 `wechat_openid`
- **WHEN** 用户提交手机号绑定请求
- **THEN** 系统 SHALL 返回 HTTP 409
- **AND** 系统 SHALL NOT 覆盖已有 `wechat_openid`

#### Scenario: Reject merge when temporary user has assets
- **GIVEN** 当前登录用户为无手机号微信临时账号
- **AND** 当前临时微信用户已有余额、订单、优惠券或其他资产
- **WHEN** 用户尝试绑定一个已属于现有账号的手机号
- **THEN** 系统 SHALL 返回 HTTP 409
- **AND** 系统 SHALL NOT 自动迁移资产

#### Scenario: Reject binding existing phone for non-temporary user
- **GIVEN** 当前登录用户已有手机号
- **AND** 目标手机号已属于另一个用户
- **WHEN** 用户提交手机号绑定请求
- **THEN** 系统 SHALL 返回 HTTP 409
- **AND** 系统 SHALL NOT 合并账号
