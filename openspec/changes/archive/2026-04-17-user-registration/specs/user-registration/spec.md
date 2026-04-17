## ADDED Requirements

### Requirement: Register with phone and password
系统 SHALL 支持通过手机号 + 短信验证码 + 密码完成用户注册。注册成功后自动登录，返回 JWT Token。

#### Scenario: Successful registration
- **GIVEN** 用户手机号 13800138000 已通过图形验证码和短信验证码校验
- **WHEN** 用户提交注册信息（手机号、验证码、密码 "Abc123456"、昵称 "学习达人"）
- **THEN** 系统创建用户记录（手机号唯一），密码使用 bcrypt 加密存储，返回 JWT Access Token 和 Refresh Token

#### Scenario: Duplicate phone number
- **GIVEN** 手机号 13800138000 已被注册
- **WHEN** 用户尝试使用相同手机号注册
- **THEN** 系统拒绝注册，返回 HTTP 409，提示"该手机号已注册"

#### Scenario: Password too short
- **GIVEN** 用户提交密码 "12345"（少于 6 位）
- **WHEN** 用户提交注册信息
- **THEN** 系统拒绝注册，返回 HTTP 422，提示"密码长度不能少于6位"

#### Scenario: Password too long
- **GIVEN** 用户提交密码超过 20 位
- **WHEN** 用户提交注册信息
- **THEN** 系统拒绝注册，返回 HTTP 422，提示"密码长度不能超过20位"

#### Scenario: Invalid SMS code during registration
- **GIVEN** 用户提交的短信验证码未通过校验或已过期
- **WHEN** 用户提交注册信息
- **THEN** 系统拒绝注册，返回 HTTP 400，提示"验证码无效"

#### Scenario: Missing user agreement
- **GIVEN** 用户未勾选同意用户协议
- **WHEN** 用户提交注册信息
- **THEN** 系统拒绝注册，返回 HTTP 422，提示"请先同意用户服务协议和隐私政策"

### Requirement: Invite code support
系统 SHALL 支持可选的邀请码功能，用户注册时填写有效邀请码可获得额外权益。

#### Scenario: Valid invite code
- **GIVEN** 系统中存在有效邀请码 "INVITE2024"
- **WHEN** 用户注册时填写邀请码 "INVITE2024"
- **THEN** 注册成功，用户账户标记邀请关系，邀请人和被邀请人各获得 2 小时学习时长奖励

#### Scenario: Invalid invite code
- **GIVEN** 用户注册时填写邀请码 "INVALID"
- **WHEN** 邀请码 "INVALID" 不存在或已失效
- **THEN** 系统拒绝注册，返回 HTTP 400，提示"邀请码无效"

#### Scenario: Registration without invite code
- **GIVEN** 用户注册时不填写邀请码
- **WHEN** 用户提交注册信息（其他字段均有效）
- **THEN** 注册正常完成，无奖励发放

### Requirement: Default nickname generation
系统 SHALL 在用户未提供昵称时自动生成随机昵称。

#### Scenario: User provides nickname
- **GIVEN** 用户注册时填写昵称 "学习达人"
- **WHEN** 注册成功
- **THEN** 用户昵称设置为 "学习达人"

#### Scenario: User omits nickname
- **GIVEN** 用户注册时未填写昵称
- **WHEN** 注册成功
- **THEN** 系统自动生成昵称，格式为 "学习者" + 6 位随机数字，如 "学习者583921"
