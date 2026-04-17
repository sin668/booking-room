# API 文档

Base URL: `http://localhost:8000`

## 认证相关接口

### POST /api/v1/auth/send-code

发送短信验证码。

**请求体：**
```json
{
  "phone": "13800138000",
  "captcha_token": "string"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号，11位，以1开头 |
| captcha_token | string | 是 | 阿里云验证码 2.0 token |

**响应 200：**
```json
{
  "message": "验证码发送成功"
}
```

**错误码：**
- 400: 图形验证码校验失败 / 发送频率超限（60s） / 每日上限（10次）
- 422: 手机号格式不正确

---

### POST /api/v1/auth/register

用户注册。注册成功后自动登录。

**请求体：**
```json
{
  "phone": "13800138000",
  "sms_code": "123456",
  "password": "Abc123456",
  "nickname": "学习达人",
  "captcha_token": "string",
  "agree_terms": true,
  "invite_code": "INVITE2024"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 手机号 |
| sms_code | string | 是 | 6位短信验证码 |
| password | string | 是 | 密码，6-20位 |
| nickname | string | 否 | 昵称，2-20字，不填则自动生成 |
| captcha_token | string | 是 | 图形验证码 token |
| agree_terms | boolean | 是 | 是否同意用户协议 |
| invite_code | string | 否 | 邀请码 |

**响应 201：**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

同时通过 HttpOnly Cookie 设置 `refresh_token`（有效期 7 天）。

**错误码：**
- 400: 验证码无效 / 邀请码无效
- 409: 该手机号已注册
- 422: 参数校验失败（密码长度、未同意协议等）

---

### POST /api/v1/auth/login

用户登录（手机号 + 密码）。

**请求体：**
```json
{
  "phone": "13800138000",
  "password": "Abc123456"
}
```

**响应 200：**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

同时通过 HttpOnly Cookie 设置 `refresh_token`。

**错误码：**
- 401: 手机号或密码错误
- 403: 账号已被禁用

---

### POST /api/v1/auth/refresh

刷新 Access Token。支持从 HttpOnly Cookie 或请求体中获取 Refresh Token。

**请求体（可选）：**
```json
{
  "refresh_token": "eyJhbG..."
}
```

**响应 200：**
```json
{
  "access_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

**错误码：**
- 401: 未提供 Refresh Token / 登录已过期 / Refresh Token 重用检测（强制重新登录）

---

### POST /api/v1/auth/logout

退出登录。需要 Authorization Header。

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 200：**
```json
{
  "message": "退出成功"
}
```

**错误码：**
- 401: 未提供认证信息 / Token 已失效

---

### GET /api/v1/auth/me

获取当前登录用户信息。需要 Authorization Header。

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 200：**
```json
{
  "id": "uuid-string",
  "phone": "138****8000",
  "nickname": "学习达人",
  "status": "active",
  "wechat_openid": null,
  "invite_code": null,
  "created_at": "2026-04-17T00:00:00"
}
```

**错误码：**
- 401: 未认证 / Token 已过期或失效
- 404: 用户不存在
