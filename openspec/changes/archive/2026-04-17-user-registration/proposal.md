## Why

用户注册是小程序的核心入口流程，目前系统缺少用户身份管理能力。没有注册功能，后续的预约、支付、会员体系、学习记录等业务功能均无法落地。需要优先实现手机号注册，作为微信授权登录的补充方式，确保覆盖不使用微信快捷登录的用户场景。

## What Changes

- 新增手机号 + 短信验证码注册流程（核心方式）
- 新增密码设置与确认密码校验（bcrypt 加密存储）
- 新增邀请码机制（可选，用于裂变拉新）
- 新增用户协议与隐私政策确认（合规要求）
- 新增注册接口的防刷与限流（Redis 滑动窗口，60s/次，同一手机号每日上限 5 次，阿里云验证码 2.0 前置）
- 新增注册后的自动登录（返回 JWT Token）
- 新增昵称初始化（默认随机昵称，支持自定义）

## Capabilities

### New Capabilities
- `sms-verification`: 短信验证码发送与校验（阿里云短信服务，含阿里云验证码 2.0 图形验证码前置、生成、存储、过期、防刷）
- `user-registration`: 用户注册（手机号+验证码+密码，含邀请码、协议确认）
- `user-auth`: 用户认证（JWT 签发、刷新、自动登录、微信 OAuth ）

### Modified Capabilities
<!-- 无已有 spec，无需修改 -->

## Impact

- **后端 br-server**:
  - 新增模块：`api/routes/auth.py`（注册/登录/刷新 Token 接口）
  - 新增模块：`services/sms_service.py`（短信发送与校验逻辑）
  - 新增模块：`services/auth_service.py`（注册/认证业务逻辑）
  - 新增模型：`models/user.py`（用户表、Token 黑名单表）
  - 新增依赖：`python-jose[cryptography]`（JWT）、`passlib[bcrypt]`（密码哈希）、`httpx`（短信网关调用）
  - 数据库迁移：新建 `users` 表（phone, nickname, password_hash, invite_code, wechat_openid, status, created_at）
- **前端 br-app**:
  - 新增页面：`pages/login/login.vue`（登录/注册双 Tab 页面）
  - 新增 API 调用：`api/auth.js`（register, login, sendSmsCode）
  - 新增状态管理：`store/modules/user.js`（用户信息、Token 持久化）
  - 修改入口逻辑：未登录跳转登录页，Token 过期自动刷新
- **管理后台 br-admin**:
  - 暂不涉及，用户管理模块在后续迭代中实现
- **回滚方案**：数据库迁移支持 down 回滚；新增 API 路由可通过 feature flag 关闭；前端登录页可通过路由配置禁用
