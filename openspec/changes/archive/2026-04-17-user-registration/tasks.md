## 1. 项目基础设施

- [x] 1.1 添加后端依赖：`python-jose[cryptography]`、`passlib[bcrypt]`、`httpx`
- [x] 1.2 配置 Redis 连接（验证码存储 + Refresh Token + Token 黑名单）
- [x] 1.3 添加 JWT 配置项（SECRET_KEY、ACCESS_TOKEN_EXPIRE_MINUTES=15、REFRESH_TOKEN_EXPIRE_DAYS=7）
- [x] 1.4 配置短信网关 API Key（预留配置项，使用 mock 实现先行开发）

## 2. 数据库模型与迁移

- [x] 2.1 创建 User SQLAlchemy 模型（phone UNIQUE、nickname、password_hash、invite_code、wechat_openid、status、created_at、updated_at）
- [x] 2.2 创建数据库迁移脚本（Alembic upgrade + downgrade 回滚）
- [x] 2.3 创建 User Pydantic Schema（UserCreate、UserResponse、UserLogin）

## 3. 短信验证码服务(使用阿里云的短信服务)

- [x] 3.1 实现 SMS 发送接口（抽象 SMSProvider，实现 AliyunSMSProvider，调用阿里云 Dysms API）
- [x] 3.2 实现验证码生成与 Redis 存储（key: `sms:verify:{phone}`，TTL 300s）
- [x] 3.3 实现发送频率限制（60s 滑动窗口，Redis INCR + EXPIRE）
- [x] 3.4 实现每日发送上限（Redis key: `sms:daily:{phone}:{date}`，上限 10 次）
- [x] 3.5 实现验证码校验（比对 + 一次性消费 + 过期检查）
- [x] 3.6 编写 sms_service 单元测试（发送、限流、校验、过期场景，覆盖率 > 90%）

## 3.5 图形验证码服务(使用阿里云验证码 2.0)

- [x] 3.5.1 集成阿里云验证码 2.0 服务端 SDK（captcha_service.py）
- [x] 3.5.2 实现验证码校验接口（接收 captcha_token，调用阿里云 API 验证，支持一次性使用）
- [x] 3.5.3 在发送短信接口中添加 captcha_token 前置校验（未通过则拒绝发送）
- [x] 3.5.4 编写 captcha_service 单元测试（校验通过、token 无效、token 重用、token 缺失场景）

## 4. 认证服务

- [x] 4.1 实现 JWT 工具函数（签发 Access Token、签发 Refresh Token、解码验证）
- [x] 4.2 实现 Refresh Token Rotation（签发新 RT + 旧 RT 失效 + 重用检测）
- [x] 4.3 实现 Token 黑名单（退出登录时 Access Token 加入 Redis，TTL = 剩余有效期）
- [x] 4.4 实现 JWT 认证中间件（FastAPI Depends，解析 Header、校验签名、检查黑名单、注入 user_id）
- [x] 4.5 编写 auth_service 单元测试（Token 签发、刷新、黑名单、重用检测，覆盖率 > 90%）

## 5. 业务逻辑服务

- [x] 5.1 实现注册逻辑（验证码校验 → 手机号去重 → 密码 bcrypt 加密 → 创建用户 → 签发 Token）
- [x] 5.2 实现登录逻辑（手机号查询 → 密码比对 → 状态检查 → 签发 Token）
- [x] 5.3 实现邀请码校验（验证邀请码有效性 → 标记邀请关系 → 发放奖励）
- [x] 5.4 实现默认昵称生成（"学习者" + 6 位随机数字）
- [x] 5.5 编写 service 层单元测试（注册成功/重复/密码不合规、登录成功/失败/封禁，覆盖率 > 90%）

## 6. API 路由

- [x] 6.1 POST /api/v1/auth/send-code — 发送验证码
- [x] 6.2 POST /api/v1/auth/register — 用户注册（手机号、验证码、密码、昵称、邀请码、协议确认）
- [x] 6.3 POST /api/v1/auth/login — 手机号 + 密码登录
- [x] 6.4 POST /api/v1/auth/refresh — 刷新 Token
- [x] 6.5 POST /api/v1/auth/logout — 退出登录（加入黑名单 + 清除 Cookie）
- [x] 6.6 GET /api/v1/users/me — 获取当前用户信息（受保护路由）
- [x] 6.7 编写 API 集成测试（每个接口正常/异常场景，覆盖率 > 90%）

## 7. 前端 - 登录/注册页面

- [x] 7.1 创建 login.vue 页面（登录/注册双 Tab 切换，参考 prototype/login.html）
- [x] 7.2 实现手机号输入组件（+86 区号选择、11 位手机号校验）
- [x] 7.3 实现验证码输入组件（发送按钮 60s 倒计时、6 位输入框）
- [x] 7.4 实现密码输入组件（显示/隐藏切换、强度指示条、确认密码校验）
- [x] 7.5 实现邀请码输入（选填，输入验证）
- [x] 7.6 实现用户协议勾选（链接跳转协议页面）
- [x] 7.7 实现第三方登录按钮（微信/Apple/QQ，预留点击事件，暂不实现逻辑）
- [x] 7.8 实现注册/登录交互逻辑（表单校验 → API 调用 → loading 状态 → 成功/失败提示 → 跳转）

## 8. 前端 - 认证状态管理

- [x] 8.1 创建 api/auth.js（sendCode、register、login、refresh、logout 接口封装）
- [x] 8.2 创建 store/modules/user.js（用户信息、Token 存储、自动登录、退出清理）
- [x] 8.3 实现 Token 自动刷新（axios 拦截器：401 → 调用 refresh → 重试原请求）
- [x] 8.4 实现路由守卫（未登录跳转登录页，登录后跳回原页面）
- [x] 8.5 配置 pages.json（登录页路由、全局路由拦截）

## 9. 集成与收尾

- [ ] 9.1 前后端联调（注册 → 登录 → Token 刷新 → 退出完整流程）
- [x] 9.2 API 文档更新（docs/api.md 补充 auth 相关接口）
- [x] 9.3 代码审查与重构（确保 Clean Architecture 分层、消除重复代码）
- [x] 9.4 全量测试通过（单元测试 + 集成测试，覆盖率 > 90%）
