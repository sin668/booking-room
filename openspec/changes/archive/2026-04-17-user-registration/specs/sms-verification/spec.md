## ADDED Requirements

### Requirement: Captcha verification before SMS
系统 SHALL 在发送短信验证码前要求用户完成图形验证码（阿里云验证码 2.0 滑块验证），防止自动化脚本恶意调用。

#### Scenario: Captcha passed, send SMS
- **GIVEN** 用户手机号 13800138000
- **WHEN** 用户完成滑块验证并提交有效的 captcha_token
- **THEN** 系统通过阿里云服务端 API 校验 captcha_token，校验通过后发送短信验证码

#### Scenario: Invalid or expired captcha token
- **GIVEN** 用户提交 captcha_token "invalid_token_123"
- **WHEN** 系统向阿里云校验该 token
- **THEN** 校验失败，系统拒绝发送短信，返回 HTTP 400，提示"请完成图形验证"

#### Scenario: Captcha token reused
- **GIVEN** 一个 captcha_token 已被使用过
- **WHEN** 用户使用该 token 再次请求发送短信
- **THEN** 系统拒绝请求，返回 HTTP 400，提示"验证码已使用，请重新验证"

#### Scenario: Missing captcha token
- **GIVEN** 用户请求发送短信但未携带 captcha_token
- **WHEN** 系统检查请求参数
- **THEN** 系统拒绝请求，返回 HTTP 422，提示"请先完成图形验证"

### Requirement: Send SMS verification code
系统 SHALL 支持向指定手机号发送 6 位数字验证码，验证码有效期 5 分钟，存储于 Redis。发送前 MUST 通过图形验证码校验。

#### Scenario: Successfully send verification code
- **GIVEN** 用户手机号 13800138000 且已通过图形验证码校验
- **WHEN** 用户请求发送验证码
- **THEN** 系统生成 6 位随机数字验证码，存入 Redis key `sms:verify:13800138000`（TTL 300s），返回成功

#### Scenario: Rate limit per minute
- **GIVEN** 用户手机号 13800138000 在 60 秒内已发送过验证码
- **WHEN** 用户再次请求发送验证码
- **THEN** 系统拒绝请求，返回 HTTP 429，提示"发送过于频繁，请60秒后重试"

#### Scenario: Daily limit exceeded
- **GIVEN** 用户手机号 13800138000 当日已发送 10 次验证码
- **WHEN** 用户再次请求发送验证码
- **THEN** 系统拒绝请求，返回 HTTP 429，提示"今日发送次数已达上限"

#### Scenario: Invalid phone number format
- **GIVEN** 用户输入手机号 "12345"
- **WHEN** 用户请求发送验证码
- **THEN** 系统拒绝请求，返回 HTTP 422，提示手机号格式错误

### Requirement: Verify SMS code
系统 SHALL 支持校验用户提交的验证码是否正确且未过期。

#### Scenario: Correct verification code
- **GIVEN** 系统已向 13800138000 发送验证码 "123456"
- **WHEN** 用户提交验证码 "123456"
- **THEN** 系统校验通过，删除 Redis 中该验证码 key，返回校验成功

#### Scenario: Incorrect verification code
- **GIVEN** 系统已向 13800138000 发送验证码 "123456"
- **WHEN** 用户提交验证码 "654321"
- **THEN** 系统校验失败，返回 HTTP 400，提示"验证码错误"，验证码不被删除（允许重试）

#### Scenario: Expired verification code
- **GIVEN** 验证码已超过 5 分钟有效期
- **WHEN** 用户提交已过期的验证码
- **THEN** 系统校验失败，返回 HTTP 400，提示"验证码已过期，请重新获取"
