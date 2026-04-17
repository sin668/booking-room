## Context

当前系统为全新共享自习室预约平台，尚无用户身份管理能力。项目采用 Python 3.12 + FastAPI 后端、uni-app (Vue3) 小程序前端、PostgreSQL 18 数据库。

核心约束：
- 微信小程序移动端优先设计
- RBAC 权限控制在后端强制执行
- 同一手机号不可重复注册
- 核心逻辑单元测试覆盖率 > 90%
- API 需要集成测试
- RESTful API 风格

## Goals / Non-Goals

**Goals:**
- 实现手机号 + 短信验证码注册流程，作为微信授权登录的补充
- 实现 JWT 认证体系（签发、刷新、Token 黑名单）
- 短信验证码防刷（Redis 滑动窗口限流）
- 注册后自动登录，返回有效 Token
- 支持邀请码裂变拉新
- 用户协议确认（合规）

**Non-Goals:**
- 微信 OAuth 登录（后续迭代，本次仅预留 `wechat_openid` 字段）
- 管理后台用户管理界面
- 用户信息修改（昵称、头像等在后续迭代中实现）
- 多因素认证（MFA）
- 第三方账号绑定（QQ、Apple 等）

## Decisions

### D1: 认证方案 — JWT (Access + Refresh Token)

**选择**: 双 Token 方案（Access Token 15min + Refresh Token 7d），Refresh Token 存 Redis。

**替代方案**:
- 单 Token 方案：简单但安全性不足，无法主动失效
- Session + Redis：强依赖 Redis，不适合无状态水平扩展

**理由**: Access Token 短有效期降低泄露风险；Refresh Token 存 Redis 支持主动吊销；FastAPI 依赖注入天然支持中间件验证。

### D2: 短信验证码 — Redis 存储 + 6 位随机数字

**选择**: 6 位数字验证码，Redis key `sms:verify:{phone}`，TTL 5 分钟。

**替代方案**:
- 4 位验证码：安全性不足
- 算术验证码：用户体验差
- 第三方验证服务：增加外部依赖

**理由**: 6 位数字是行业标准，平衡安全与体验；Redis TTL 自动过期无需清理。

### D3: 密码加密 — bcrypt (passlib)

**选择**: `passlib[bcrypt]`，cost factor = 12。

**替代方案**:
- argon2：更安全但 Python 生态支持不如 bcrypt
- PBKDF2：标准但不如 bcrypt 抗 GPU 暴力破解

**理由**: bcrypt 是 Python/FastAPI 社区主流选择，passlib 提供统一 API，cost=12 在安全性与性能间平衡（~250ms/次）。

### D4: 防刷策略 — Redis 滑动窗口

**选择**: 同一手机号 60 秒内限 1 次，每日上限 10 次。使用 Redis `INCR` + `EXPIRE` 实现。

**替代方案**:
- 固定窗口：边界问题（窗口末尾+开头可发 2 次）
- Token Bucket：实现复杂，当前场景不需要

**理由**: 滑动窗口用 `INCR` + `EXPIRE` 即可实现，简洁且无边界问题。

### D5: 用户表设计 — 单表 + 软删除

**选择**: 单 `users` 表，`status` 字段（active/inactive/banned），不物理删除。

**替代方案**:
- 用户表 + 用户详情表分拆：过早优化，当前字段少
- 物理删除：丢失关联数据（订单、学习记录等）

**理由**: 单表满足 V1 需求，软删除保留数据完整性，后续字段增多时再拆分。

## Risks / Trade-offs

| 风险 | 缓解措施 |
|------|----------|
| 短信网关故障导致无法注册 | 实现短信服务商降级策略；提供微信授权登录作为备选 |
| Redis 宕机导致验证码丢失 | 验证码 Redis key 设置短 TTL；Redis 宕机时降级为全量验证 |
| JWT 泄露 | Access Token 15min 短有效期；提供 Token 吊销接口（加入黑名单）；HTTPS 传输 |
| 手机号被恶意注册 | 每日发送上限 + 图形验证码前置 + 手机号唯一约束 |
| 并发注册同一手机号 | 数据库 UNIQUE 约束 + 乐观锁 |
| 图形验证码被绕过 | 使用服务端校验（阿里云验证码 2.0），前端仅渲染；结合 IP 限流 |

## Migration Plan

### 部署步骤
1. 执行数据库迁移：创建 `users` 表
2. 部署后端代码：新增 auth 路由、sms_service、auth_service、captcha_service
3. 部署前端代码：新增登录/注册页面（含图形验证码组件）
4. 配置 Redis（验证码存储 + Refresh Token + 图形验证码校验缓存）
5. 配置阿里云短信服务（AccessKey、签名、模板）
6. 配置阿里云验证码 2.0（Scene ID、AccessKey）

### 回滚方案
1. 数据库迁移支持 `downgrade`：DROP `users` 表
2. 后端通过 feature flag 关闭注册接口：`settings.REGISTRATION_ENABLED = False`
3. 前端登录页通过路由配置禁用：`pages.json` 中注释注册路由
4. Redis 数据自然过期，无需清理

## Resolved Decisions

- **短信服务商**：阿里云短信服务（Dysms API），已确认
- **图形验证码**：集成阿里云验证码 2.0（滑块验证），发送短信前强制校验，已确认
