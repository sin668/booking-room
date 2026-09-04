# API 文档

Base URL: `http://localhost:8000`

## 认证

用户端接口使用 Bearer Token (JWT)，通过 `Authorization` header 传递。
管理端接口使用固定 Token，通过 `X-Admin-Token` header 传递。

---

## 消息通知

以下接口均为用户端接口，必须携带 Bearer Token。服务端从认证上下文确定当前用户，不接受客户端传入 `user_id` 作为查询或更新范围。

### GET /api/v1/notifications

获取当前用户的通知分页列表，按 `created_at` 倒序返回。

**认证：** Bearer Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string | - | 可选通知类型：`booking` / `activity` / `report` / `arrival` |
| page | integer | 1 | 页码，最小 1 |
| page_size | integer | 20 | 每页数量，最大 50 |

**响应 200：**

```json
{
  "items": [
    {
      "id": "11111111-2222-3333-4444-555555555555",
      "type": "booking",
      "title": "预约成功",
      "content": "您的预约已确认",
      "target_url": "/pages/booking/detail?id=1",
      "target_type": "booking",
      "target_id": "1",
      "is_read": false,
      "created_at": "2026-05-28T09:00:00",
      "read_at": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20
}
```

**失败行为：**

- 401: 未认证或 Token 无效
- 422: `type` 不在允许范围内，或分页参数不合法
- 客户端传入 `user_id` 时不得改变查询范围，响应仍只包含当前用户通知

### GET /api/v1/notifications/unread-summary

获取当前用户未读摘要。各类型字段返回该类型未读数；`total_unread` 只统计用户偏好中已开启的通知类型。

**认证：** Bearer Token

**响应 200：**

```json
{
  "total_unread": 3,
  "booking_count": 1,
  "activity_count": 0,
  "report_count": 1,
  "arrival_count": 1
}
```

**失败行为：**

- 401: 未认证或 Token 无效
- 已关闭类型的未读数仍可在对应 `*_count` 字段中返回，但不得计入 `total_unread`

### POST /api/v1/notifications/{id}/read

将当前用户拥有的一条通知标记为已读，并设置 `read_at`。

**认证：** Bearer Token

**路径参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| id | string | 是 | 通知 UUID |

**响应 200：**

```json
{
  "id": "11111111-2222-3333-4444-555555555555",
  "type": "booking",
  "title": "预约成功",
  "content": "您的预约已确认",
  "target_url": "/pages/booking/detail?id=1",
  "target_type": "booking",
  "target_id": "1",
  "is_read": true,
  "created_at": "2026-05-28T09:00:00",
  "read_at": "2026-05-28T09:05:00"
}
```

**失败行为：**

- 401: 未认证或 Token 无效
- 404 或 403: 通知不存在，或通知不属于当前用户
- 跨用户通知 ID 不得被读取、标记或泄露详情

### POST /api/v1/notifications/read-all

批量将当前用户未读通知标记为已读。传入 `type` 时只处理该类型；未传入时处理当前用户全部类型。

**认证：** Bearer Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string | - | 可选通知类型：`booking` / `activity` / `report` / `arrival` |

**响应 200：**

```json
{
  "updated_count": 3
}
```

**失败行为：**

- 401: 未认证或 Token 无效
- 422: `type` 不在允许范围内
- 只更新当前用户通知，不得修改其他用户通知

### GET /api/v1/notifications/preferences

获取当前用户通知偏好。没有偏好记录时返回默认值，四类通知均开启；服务端可同时创建默认偏好记录。

**认证：** Bearer Token

**响应 200：**

```json
{
  "booking_enabled": true,
  "activity_enabled": true,
  "report_enabled": true,
  "arrival_enabled": true,
  "updated_at": "2026-05-28T09:00:00"
}
```

**失败行为：**

- 401: 未认证或 Token 无效
- 客户端传入 `user_id` 时不得改变读取范围

### PUT /api/v1/notifications/preferences

更新当前用户通知偏好。请求体包含四类开关；服务端必须保存到当前认证用户。

**认证：** Bearer Token

**请求体：**

```json
{
  "booking_enabled": true,
  "activity_enabled": false,
  "report_enabled": true,
  "arrival_enabled": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| booking_enabled | boolean | 是 | 预约提醒开关 |
| activity_enabled | boolean | 是 | 活动通知开关 |
| report_enabled | boolean | 是 | 学习报告开关 |
| arrival_enabled | boolean | 是 | 到店提醒开关 |

**响应 200：**

```json
{
  "booking_enabled": true,
  "activity_enabled": false,
  "report_enabled": true,
  "arrival_enabled": true,
  "updated_at": "2026-05-28T09:05:00"
}
```

**失败行为：**

- 401: 未认证或 Token 无效
- 422: 请求体字段缺失或类型错误
- 请求体或查询参数中的 `user_id` 不得改变更新目标

---

## 一、用户认证

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
| nickname | string | 否 | 昵称 |
| captcha_token | string | 是 | 图形验证码 token |
| agree_terms | boolean | 是 | 是否同意用户协议 |
| invite_code | string | 否 | 邀请码 |

**响应 201：**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

同时通过 HttpOnly Cookie 设置 `refresh_token`（有效期 7 天）。注册流程会自动生成全局唯一用户名；客户端可在注册成功后请求 `GET /api/v1/users/me` 获取 `username` 和 `username_updated_at`。

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
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

同时通过 HttpOnly Cookie 设置 `refresh_token`。

**错误码：**
- 401: 手机号或密码错误
- 403: 账号已被禁用

---

### POST /api/v1/auth/wechat-login

微信快速登录。小程序端提交 `uni.login` 获取的微信登录 code，后端通过微信接口换取 OpenID，并签发与现有用户登录一致的 `TokenResponse`。

**认证：** 无需 Bearer Token

**请求体：**
```json
{
  "code": "wx-login-code"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 微信登录 code；有效期较短，客户端应在每次登录时重新获取 |

**响应 200：**
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

同时通过 HttpOnly Cookie 设置 `refresh_token`。若 OpenID 已绑定用户，响应为该用户的登录会话；若 OpenID 未绑定用户，后端创建 `phone = null` 的 app 用户，写入 `wechat_openid`，生成全局唯一 username 和默认昵称后签发 token。响应不得包含微信 `session_key`。

**错误码：**
- 400: 微信登录 code 无效、过期或被微信接口拒绝；客户端应提示“微信登录已过期，请重试”
- 401: 不适用；该接口不要求 Bearer Token，认证失败通过微信 code 校验错误返回 400
- 403: OpenID 已绑定的用户不可登录或账号不可用
- 409: 不适用；该接口只做 OpenID 登录或创建微信用户，不执行手机号绑定或账号合并
- 503: 微信登录配置缺失或微信服务不可用；客户端可引导用户使用手机号登录
- 422: 参数校验失败

**错误示例：**

HTTP 400：
```json
{
  "detail": "微信登录已过期，请重试"
}
```

HTTP 401：不适用。该接口无需 Bearer Token。

HTTP 403：
```json
{
  "detail": "账号不可用"
}
```

HTTP 409：不适用。该接口不处理手机号冲突或账号合并冲突。

HTTP 503：
```json
{
  "detail": "微信登录暂不可用"
}
```

---

### POST /api/v1/auth/wechat/bind-phone

通过微信手机号授权绑定手机号。适用于已登录但尚未绑定手机号的微信用户；手机号已属于已有账号时，按受限合并规则处理。

**认证：** Bearer Token

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "code": "wx-phone-code"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 微信手机号授权 code，用于后端向微信换取手机号 |

**响应 200：**

成功统一返回 `TokenResponse`；未触发账号合并时 token 属于当前用户，触发账号合并时 token 属于已有手机号主账号：
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

手机号未占用时，后端将手机号绑定到当前用户并签发新的 `TokenResponse`。手机号已属于已有 app 用户时，仅当当前用户是 `phone = null` 且 `wechat_openid` 非空的微信临时账号、目标手机号账号未绑定其他 OpenID、且临时账号没有余额、订单、优惠券等资产，才允许把当前 `wechat_openid` 合并到已有手机号账号，并为主账号签发新的 `TokenResponse`。

**错误码：**
- 400: 微信手机号授权 code 无效、过期或被微信接口拒绝；客户端应提示“手机号授权已过期，请重试”
- 401: 未认证 / Token 已过期或失效
- 403: 当前用户不可登录或账号不可用
- 409: 目标手机号已被其他账号占用且不满足合并条件 / 目标手机号账号已绑定不同 OpenID / 临时账号存在资产，拒绝自动合并
- 503: 微信手机号授权服务不可用
- 422: 参数校验失败

**错误示例：**

HTTP 400：
```json
{
  "detail": "手机号授权已过期，请重试"
}
```

HTTP 401：
```json
{
  "detail": "Not authenticated"
}
```

HTTP 403：
```json
{
  "detail": "账号不可用"
}
```

HTTP 409：
```json
{
  "detail": "该手机号已绑定其他微信账号，无法合并"
}
```

HTTP 503：
```json
{
  "detail": "微信手机号授权暂不可用"
}
```

---

### POST /api/v1/auth/wechat/bind-phone/sms

通过短信验证码绑定手机号，作为微信手机号授权失败或不可用时的备用路径。绑定和账号合并规则与微信手机号授权绑定一致，手机号来源改为短信验证码校验。

**认证：** Bearer Token

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "phone": "13800138000",
  "sms_code": "123456"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| phone | string | 是 | 待绑定手机号，11 位，以 1 开头 |
| sms_code | string | 是 | 6 位短信验证码 |

**响应 200：**

成功统一返回 `TokenResponse`；未触发账号合并时 token 属于当前用户，触发账号合并时 token 属于已有手机号主账号：
```json
{
  "access_token": "eyJhbG...",
  "refresh_token": "eyJhbG...",
  "token_type": "bearer",
  "expires_in": 900
}
```

手机号未占用时，后端将手机号绑定到当前用户并签发新的 `TokenResponse`。手机号已属于已有 app 用户时，仅当当前用户是无手机号微信临时账号且满足受限合并条件，才允许把当前 `wechat_openid` 绑定到已有手机号账号，并为主账号签发新的 `TokenResponse`。

**错误码：**
- 400: 短信验证码无效或已过期 / 验证码校验失败
- 401: 未认证 / Token 已过期或失效
- 403: 当前用户不可登录或账号不可用
- 409: 目标手机号已被其他账号占用且不满足合并条件 / 目标手机号账号已绑定不同 OpenID / 临时账号存在资产，拒绝自动合并
- 503: 短信验证码服务不可用
- 422: 手机号格式不正确 / 参数校验失败

**错误示例：**

HTTP 400：
```json
{
  "detail": "短信验证码无效或已过期"
}
```

HTTP 401：
```json
{
  "detail": "Not authenticated"
}
```

HTTP 403：
```json
{
  "detail": "账号不可用"
}
```

HTTP 409：
```json
{
  "detail": "临时微信账号存在资产，无法自动合并"
}
```

HTTP 503：
```json
{
  "detail": "短信验证码服务暂不可用"
}
```

---

### 微信快速登录回滚说明

回滚微信快速登录能力时，应关闭小程序微信登录入口和后端微信登录、微信手机号绑定、短信备用绑定接口；已写入的 `users.wechat_openid` 数据应保留，不作为回滚清理对象，避免破坏已经建立的微信绑定关系。手机号登录、密码登录和 refresh/logout 流程继续按原认证接口使用。

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
  "refresh_token": "eyJhbG...",
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
  "username": "Luna48392",
  "username_updated_at": null,
  "nickname": "学习达人",
  "avatar": null,
  "status": "active",
  "user_type": "app",
  "wechat_openid": null,
  "invite_code": null,
  "created_at": "2026-04-17T00:00:00"
}
```

**错误码：**
- 401: 未认证 / Token 已过期或失效
- 404: 用户不存在

---

## 二、用户信息

### GET /api/v1/users/me

获取当前登录用户资料。该接口是小程序和 App 读取个人资料的首选接口；`/api/v1/auth/me` 仅保留为认证兼容接口。

**认证：** Bearer Token

**请求头：**
```
Authorization: Bearer <access_token>
```

**响应 200：**
```json
{
  "id": "uuid-string",
  "phone": "13800138000",
  "username": "Luna48392",
  "username_updated_at": "2026-04-17T08:30:00",
  "nickname": "学习达人",
  "avatar": "https://example.com/avatar.png",
  "status": "active",
  "user_type": "app",
  "created_at": "2026-04-17T00:00:00"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 用户 ID |
| phone | string | 当前用户手机号 |
| username | string | 全局唯一用户名 |
| username_updated_at | string \| null | 最近一次成功修改用户名的时间；未修改过时为 null |
| nickname | string \| null | 昵称 |
| avatar | string \| null | 头像 URL |
| status | string | 用户状态 |
| user_type | string | 用户类型，用户端为 `app` |
| created_at | string | 创建时间 |

**错误码：**
- 401: 未认证
- 404: 用户不存在

---

### PATCH /api/v1/users/me

更新当前登录用户资料。仅允许更新安全资料字段：`username`、`nickname`、`avatar`。不能通过该接口修改 `phone`、`status`、`user_type`、`roles`、`balance`、密码或 Token 相关字段。

**认证：** Bearer Token

**请求头：**
```
Authorization: Bearer <access_token>
```

**请求体：**
```json
{
  "username": "LunaStudy01",
  "nickname": "学习达人",
  "avatar": "https://example.com/avatar.png"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| username | string | 否 | 用户名，6-32 位字母、数字或下划线 |
| nickname | string | 否 | 昵称 |
| avatar | string | 否 | 头像 URL |

**响应 200：**
```json
{
  "id": "uuid-string",
  "phone": "13800138000",
  "username": "LunaStudy01",
  "username_updated_at": "2026-04-17T08:30:00",
  "nickname": "学习达人",
  "avatar": "https://example.com/avatar.png",
  "status": "active",
  "user_type": "app",
  "created_at": "2026-04-17T00:00:00"
}
```

**错误响应示例：**

HTTP 401 未认证：
```json
{
  "detail": "Not authenticated"
}
```

HTTP 409 用户名重复：
```json
{
  "detail": "该用户名已存在"
}
```

HTTP 422 用户名格式无效或提交受保护字段：
```json
{
  "detail": "用户名仅支持 6-32 位字母、数字或下划线"
}
```

HTTP 429 用户名修改冷却中：
```json
{
  "detail": "用户名修改后 24 小时内不可再次修改",
  "retry_after_seconds": 43200
}
```

**用户名规则：**
- 注册时默认生成用户名，格式为随机英文名 + 5 位数字，例如 `Luna48392`。
- 用户主动修改用户名时，只允许 6-32 位英文字母、数字或下划线，正则为 `^[A-Za-z0-9_]{6,32}$`。
- 用户名在所有用户类型中全局唯一。
- 每次成功修改用户名后进入滚动 24 小时冷却期；冷却期内再次修改用户名返回 HTTP 429，并在响应中包含 `retry_after_seconds`。

---

### GET /api/v1/users/me/security

获取当前用户账号安全摘要，用于设置页展示手机号、微信绑定、实名认证和注销风险状态。

**认证：** Bearer Token

**响应 200：**
```json
{
  "phone_bound": true,
  "phone_masked": "138****8000",
  "wechat_bound": true,
  "identity_status": "verified",
  "identity_masked": "110105********002X",
  "account_status": "active",
  "deactivation_blocked": false,
  "deactivation_risks": []
}
```

账号安全摘要只返回脱敏手机号、脱敏身份证号和状态，不返回完整身份证号、完整 OpenID、密码哈希或 refresh token。

**错误码：**
- 401: 未认证
- 404: 用户不存在

---

### POST /api/v1/users/me/password

修改当前用户密码。成功后撤销该用户所有 refresh token，当前 access token 可继续使用到自然过期。

**认证：** Bearer Token

**请求体：**
```json
{
  "old_password": "oldpass123",
  "new_password": "newpass123",
  "confirm_password": "newpass123"
}
```

**响应 200：**
```json
{
  "message": "密码已更新"
}
```

**错误码：**
- 400: 旧密码不正确
- 401: 未认证
- 403: 账号已注销
- 422: 新密码格式不合法或确认密码不一致

---

### POST /api/v1/users/me/identity-verification

提交实名认证资料。本期无外部核验和后台审核，合法资料提交后直接返回 `verified`。服务端仅保存身份证哈希和脱敏号，不保存完整身份证号。

**认证：** Bearer Token

**请求体：**
```json
{
  "real_name": "张三",
  "id_card_number": "11010519491231002X"
}
```

**响应 200：**
```json
{
  "status": "verified",
  "real_name": "张三",
  "id_card_masked": "110105********002X"
}
```

**错误码：**
- 401: 未认证
- 403: 账号已注销
- 409: 已完成实名认证，不能覆盖为不同实名资料
- 422: 姓名或身份证号格式不正确

---

### POST /api/v1/users/me/deactivation

注销当前用户账号。接口保留 `deactivation` 路径命名，但本期行为是直接逻辑删除：服务统一检查余额、未完成预约、待处理支付/退款和未用卡券风险；无风险时设置 `users.status='deleted'`，撤销 refresh token，不新增注销申请表，不物理删除用户。

**认证：** Bearer Token

**响应 200：**
```json
{
  "status": "deleted",
  "message": "账号已注销",
  "blocked": false,
  "risks": []
}
```

**响应 409：**
```json
{
  "detail": {
    "message": "账号存在未处理事项，暂不能注销",
    "risks": [
      {
        "code": "wallet_balance",
        "message": "钱包余额需清零后才能注销",
        "count": 0,
        "amount": "8.00"
      }
    ]
  }
}
```

**风险 code：**
- `wallet_balance`: 钱包余额未清零
- `unfinished_booking`: 存在未完成预约
- `pending_booking_payment`: 存在待处理预约支付
- `pending_wallet_transaction`: 存在待处理支付或退款
- `available_coupon`: 存在未使用卡券

**错误码：**
- 401: 未认证
- 403: 账号已注销
- 404: 用户不存在
- 409: 存在注销阻断风险

---

## 三、首页

### GET /api/v1/banners

获取当前生效的轮播图列表。无需认证。

**响应 200：**
```json
[
  {
    "id": 1,
    "image_url": "https://example.com/banner.jpg",
    "title": "新用户首单立减20元",
    "subtitle": "限时优惠，先到先得",
    "cta_text": "立即领取",
    "link_type": "page",
    "link_value": "/pages/coupon/index",
    "sort_order": 1
  }
]
```

仅返回 `is_active=true` 的轮播图，按 `sort_order` 升序排列。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 轮播图 ID |
| image_url | string | 图片 URL |
| title | string | 标题文字 |
| subtitle | string \| null | 副标题 |
| cta_text | string \| null | CTA 按钮文案 |
| link_type | string | 跳转类型：none / page / room / url |
| link_value | string \| null | 跳转目标 |
| sort_order | integer | 排序权重（升序） |

---

### GET /api/v1/activities

获取热门活动列表。无需认证。

**响应 200：**
```json
[
  {
    "id": 1,
    "title": "沉浸式学习挑战赛",
    "description": "累计学习24小时赢好礼",
    "content_html": "<p>完成学习挑战后可领取专属卡券。</p>",
    "cover_image": "https://example.com/activity.jpg",
    "participant_count": 326
  }
]
```

仅返回 `is_active=true` 的活动，按 `sort_order` 升序排列。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 活动 ID |
| title | string | 活动标题 |
| description | string \| null | 活动描述 |
| content_html | string | 活动详情富文本正文，已由后端清洗 |
| cover_image | string \| null | 封面图 URL |
| participant_count | integer | 参与人数 |

---

### GET /api/v1/activities/{activity_id}

获取活动详情。无需认证；登录用户访问时会返回当前用户对每个活动卡券的领取状态。

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_id | integer | 活动 ID |

**响应 200：**
```json
{
  "id": 1,
  "title": "沉浸式学习挑战赛",
  "description": "累计学习24小时赢好礼",
  "content_html": "<p>完成学习挑战后可领取专属卡券。</p>",
  "cover_image": "https://example.com/activity.jpg",
  "participant_count": 326,
  "is_active": true,
  "activity_coupons": [
    {
      "id": 10,
      "coupon_id": 3,
      "display_title": "挑战奖励券",
      "display_description": "完成活动即可领取",
      "coupon": {
        "id": 3,
        "name": "满20减3",
        "description": "全场通用",
        "type": "threshold_amount_off",
        "discount_amount": "3.00",
        "discount_percent": null,
        "min_order_amount": "20.00",
        "scope": "all",
        "seat_zone": null,
        "valid_from": "2026-05-01T00:00:00",
        "expires_at": "2026-05-31T23:59:59",
        "is_active": true
      },
      "total_quantity": 100,
      "claimed_quantity": 12,
      "remaining_quantity": 88,
      "per_user_limit": 1,
      "remaining_user_claims": 1,
      "claim_starts_at": "2026-05-01T00:00:00",
      "claim_ends_at": "2026-05-31T23:59:59",
      "claim_status": "available",
      "is_claimable": true
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_coupons[].claim_status | string | available / claimed / limit_reached / not_started / ended / sold_out / disabled |
| activity_coupons[].is_claimable | boolean | 当前用户或游客视角下是否可领取 |
| activity_coupons[].remaining_user_claims | integer \| null | 登录用户剩余可领取数量；游客为 null |

**错误码：**
- 404: 活动不存在或未上架

---

### POST /api/v1/activities/{activity_id}/coupons/{activity_coupon_id}/claim

领取活动关联卡券。需要登录。

**认证：** Bearer Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_id | integer | 活动 ID |
| activity_coupon_id | integer | 活动卡券配置 ID |

**响应 201：**
```json
{
  "user_coupon": {
    "id": 12,
    "coupon_id": 3,
    "status": "available",
    "source_type": "activity",
    "source_activity_id": 1,
    "source_activity_coupon_id": 10
  },
  "activity_coupon": {
    "id": 10,
    "coupon_id": 3,
    "display_title": "挑战奖励券",
    "display_description": "完成活动即可领取",
    "total_quantity": 100,
    "claimed_quantity": 13,
    "remaining_quantity": 87,
    "per_user_limit": 1,
    "remaining_user_claims": 0,
    "claim_starts_at": "2026-05-01T00:00:00",
    "claim_ends_at": "2026-05-31T23:59:59",
    "claim_status": "claimed",
    "is_claimable": false
  }
}
```

**错误码：**
- 401: 未认证
- 404: 活动或活动卡券不存在
- 409: 已抢光、超出限领数量、未到领取时间、已结束或活动卡券已停用

---

### GET /api/v1/rooms

获取自习室分页列表。无需认证。

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| page_size | integer | 10 | 每页数量（最大 50） |
| city_id | integer | - | 城市 ID；不传时返回全部城市的自习室 |
| room_type | string | - | 房间类型：`study` / `training` / `comprehensive`；不传时返回全部类型 |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "安静自习室·油城店",
      "description": "宽敞明亮的沉浸式自习空间",
      "cover_image": "https://example.com/room.jpg",
      "address": "茂名市茂南区油城三路88号",
      "business_hours": "07:00-23:00",
      "status": "open",
      "room_type": "study",
      "min_price": "8.00",
      "city_id": 1,
      "city_name": "茂名市"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```

仅返回 `status=open` 的自习室。传入 `city_id` 时，仅返回该城市的自习室；不传时返回全部城市的自习室。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 自习室 ID |
| name | string | 名称 |
| description | string \| null | 描述 |
| cover_image | string \| null | 封面图 URL |
| address | string | 地址 |
| business_hours | string \| null | 营业时间（如 "08:00-22:00"） |
| status | string | 状态：open / closed |
| room_type | string | 房间类型：study / training / comprehensive |
| min_price | decimal | 最低价格（单位：元） |
| city_id | integer \| null | 城市 ID |
| city_name | string \| null | 城市名称 |

当 `page_size` 超过 50 时，服务端会按 50 返回。

---

### GET /api/v1/cities/

获取可用城市列表。无需认证。

**响应 200：**
```json
[
  {
    "id": 1,
    "name": "茂名市",
    "province": "广东省"
  },
  {
    "id": 2,
    "name": "广州市",
    "province": "广东省"
  }
]
```

仅返回 `status=active` 的城市，按 `sort_order` 升序排列。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 城市 ID |
| name | string | 城市名称 |
| province | string | 省份名称 |

---

## 培训课程

### GET /api/v1/training/rooms

获取培训室分页列表（含热门课程），返回 `room_type` 为 `training` 或 `comprehensive` 且 `status` 为 `open` 的培训室。无需认证。

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| page_size | integer | 10 | 每页数量（最大 50） |
| city_id | integer | - | 可选城市 ID 过滤 |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "去K书培训中心",
      "description": "名师一对一辅导",
      "cover_image": "https://...",
      "address": "茂名市茂南区光谷大道88号3楼",
      "city_id": 1,
      "city_name": "茂名市",
      "business_hours": "08:00-22:00",
      "status": "open",
      "room_type": "training",
      "min_price": "50.00",
      "hot_courses": [
        {
          "id": 1,
          "name": "考研政治冲刺班",
          "cover_image": "https://...",
          "teacher": {
            "id": 1,
            "name": "李明华",
            "avatar": "https://...",
            "title": "考研政治名师",
            "rating": "4.9"
          },
          "price": "80.00",
          "enrollment_count": 328
        }
      ]
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10
}
```

每间培训室附带最多 3 条热门课程（`is_hot=true` 且 `status=active`），按 `sort_order` 升序排列。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 培训室 ID |
| name | string | 名称 |
| description | string \| null | 描述 |
| cover_image | string \| null | 封面图 URL |
| address | string | 地址 |
| city_id | integer \| null | 城市 ID |
| city_name | string \| null | 城市名称 |
| business_hours | string \| null | 营业时间 |
| status | string | 状态：open / closed |
| room_type | string | 房间类型：training / comprehensive |
| min_price | decimal | 最低价格 |
| hot_courses | array | 热门课程列表（最多 3 条） |
| hot_courses[].id | integer | 课程 ID |
| hot_courses[].name | string | 课程名称 |
| hot_courses[].cover_image | string \| null | 课程封面图 |
| hot_courses[].teacher | object \| null | 教师信息 |
| hot_courses[].teacher.id | integer | 教师 ID |
| hot_courses[].teacher.name | string | 教师姓名 |
| hot_courses[].teacher.avatar | string \| null | 教师头像 |
| hot_courses[].teacher.title | string \| null | 教师职称 |
| hot_courses[].teacher.rating | decimal | 教师评分 |
| hot_courses[].price | decimal | 课程价格 |
| hot_courses[].enrollment_count | integer | 报名人数 |

---

### GET /api/v1/training/courses

获取培训课程分页列表，仅返回 `status` 为 `active` 的课程。无需认证。

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| page_size | integer | 10 | 每页数量（最大 50） |
| category | string | - | 可选分类：`primaryschool` / `middleschool` / `postgraduate` / `civil_service` / `language` / `skills` / `professional` |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "考研政治冲刺班",
      "cover_image": "https://...",
      "teacher": {
        "id": 1,
        "name": "李明华",
        "avatar": "https://...",
        "title": "考研政治名师",
        "rating": "4.9"
      },
      "category": "postgraduate",
      "price": "80.00",
      "rating": "4.9",
      "enrollment_count": 328,
      "schedule": "周六 9:00-12:00",
      "tags": ["考研", "政治"],
      "status": "active",
      "room_id": 1,
      "room_name": "去K书培训中心"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```

按 `sort_order` 升序、`id` 升序排列。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 课程 ID |
| name | string | 课程名称 |
| cover_image | string \| null | 课程封面图 |
| teacher | object \| null | 教师信息（无关联教师时为 null） |
| teacher.id | integer | 教师 ID |
| teacher.name | string | 教师姓名 |
| teacher.avatar | string \| null | 教师头像 |
| teacher.title | string \| null | 教师职称 |
| teacher.rating | decimal | 教师评分 |
| category | string | 分类：primaryschool / middleschool / postgraduate / civil_service / language / skills / professional |
| price | decimal | 课程价格 |
| rating | decimal | 课程评分 |
| enrollment_count | integer | 报名人数 |
| schedule | string \| null | 上课时间 |
| tags | array | 标签列表（从逗号分隔字符串解析） |
| status | string | 状态：active |
| room_id | integer | 所属培训室 ID |
| room_name | string | 所属培训室名称 |

---

### GET /api/v1/training/rooms/{room_id}

获取培训室（或综合室）的详细信息，包含教室概况统计、名师团队、课程列表。仅返回 `room_type` 为 `training` 或 `comprehensive` 的房间。无需认证。

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| room_id | integer | 是 | 培训室 ID |

**响应 200：**
```json
{
  "id": 1,
  "name": "去K书培训中心",
  "description": "专业培训环境",
  "cover_image": "https://...",
  "address": "茂南区光谷大道88号3楼",
  "business_hours": "09:00 - 21:00",
  "status": "open",
  "room_type": "training",
  "min_price": "50.00",
  "city_id": 1,
  "city_name": "茂名市",
  "rating": "4.8",
  "classroom_count": 4,
  "class_capacity": "8-12",
  "teacher_count": 2,
  "total_students": 335,
  "teachers": [
    {
      "id": 1,
      "name": "李明华",
      "avatar": "https://...",
      "title": "考研政治 · 8年教龄",
      "rating": "4.9"
    }
  ],
  "courses": [
    {
      "id": 1,
      "name": "考研政治冲刺班",
      "cover_image": "https://...",
      "teacher": { "id": 1, "name": "李明华", "avatar": "https://...", "title": "考研政治名师", "rating": "4.9" },
      "category": "postgraduate",
      "price": "80.00",
      "rating": "4.9",
      "enrollment_count": 120,
      "schedule": "每周二 14:00",
      "tags": ["热销", "小班"],
      "status": "active",
      "room_id": 1,
      "room_name": "去K书培训中心"
    }
  ]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 房间 ID |
| name | string | 房间名称 |
| description | string \| null | 房间描述 |
| cover_image | string \| null | 封面图 |
| address | string | 地址 |
| business_hours | string \| null | 营业时间 |
| status | string | 状态：open / closed |
| room_type | string | 房间类型：training / comprehensive |
| min_price | decimal | 最低价格 |
| city_id | integer \| null | 城市 ID |
| city_name | string \| null | 城市名称 |
| rating | decimal | 评分 |
| classroom_count | integer | 培训教室数（该房间下 active 课程总数） |
| class_capacity | string | 小班容量（固定值 "8-12"） |
| teacher_count | integer | 认证讲师数（去重教师数） |
| total_students | integer | 累计学员数（所有课程 enrollment_count 之和） |
| teachers | array | 名师团队列表（关联该房间课程的教师去重后） |
| courses | array | 课程列表（该房间下所有 active 课程，按 sort_order 排序） |

**错误响应：**

| 状态码 | 说明 |
|--------|------|
| 404 | 培训室不存在或 room_type 不是 training/comprehensive |

---

## 四、管理端 - 活动管理

所有管理端接口需要通过 `X-Admin-Token` header 传递管理员 Token。

### GET /admin/activities

获取活动分页列表，支持关键词搜索和状态筛选。

**认证：** X-Admin-Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 10 | 每页数量 |
| keyword | string | - | 搜索关键词（匹配标题） |
| is_active | boolean | - | 是否上架 |

**响应 200：**
```json
{
  "total": 25,
  "page": 1,
  "page_size": 10,
  "items": [
    {
      "id": 1,
      "title": "沉浸式学习挑战赛",
      "description": "累计学习24小时赢好礼",
      "content_html": "<p>完成学习挑战后可领取专属卡券。</p>",
      "cover_image": "https://example.com/activity.jpg",
      "participant_count": 326,
      "sort_order": 1,
      "is_active": true,
      "activity_coupon_count": 1,
      "activity_coupon_claimed_count": 12,
      "created_at": "2026-04-20T10:00:00",
      "updated_at": "2026-04-22T15:30:00"
    }
  ]
}
```

**错误码：**
- 401: 管理员凭证无效

---

### POST /admin/activities

创建活动。

**认证：** X-Admin-Token

**请求体：**
```json
{
  "title": "沉浸式学习挑战赛",
  "description": "累计学习24小时赢好礼",
  "content_html": "<p>完成学习挑战后可领取专属卡券。</p>",
  "cover_image": "https://example.com/activity.jpg",
  "participant_count": 0,
  "sort_order": 1,
  "is_active": true,
  "activity_coupons": [
    {
      "coupon_id": 3,
      "total_quantity": 100,
      "per_user_limit": 1,
      "claim_starts_at": "2026-05-01T00:00:00",
      "claim_ends_at": "2026-05-31T23:59:59",
      "is_active": true,
      "sort_order": 1,
      "display_title": "挑战奖励券",
      "display_description": "完成活动即可领取"
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 活动标题，最大100字 |
| description | string | 否 | 活动描述，最大500字 |
| content_html | string | 否 | 活动详情富文本正文；后端会清洗不安全标签和属性 |
| cover_image | string | 否 | 封面图 URL，最大512字符 |
| participant_count | integer | 否 | 参与人数，默认 0，最小 0 |
| sort_order | integer | 否 | 排序值，默认 0 |
| is_active | boolean | 否 | 是否上架，默认 true |
| activity_coupons | array | 否 | 活动关联卡券配置；发布活动时可同时发布 |
| activity_coupons[].coupon_id | integer | 是 | 卡券模板 ID |
| activity_coupons[].total_quantity | integer | 是 | 活动总可领取库存，0 表示无库存 |
| activity_coupons[].per_user_limit | integer | 否 | 每人限领数量，默认 1 |
| activity_coupons[].claim_starts_at | datetime \| null | 否 | 领取开始时间，按 Asia/Shanghai 业务时间处理 |
| activity_coupons[].claim_ends_at | datetime \| null | 否 | 领取结束时间，按 Asia/Shanghai 业务时间处理 |
| activity_coupons[].is_active | boolean | 否 | 是否启用该活动卡券 |
| activity_coupons[].sort_order | integer | 否 | 卡券展示排序 |
| activity_coupons[].display_title | string \| null | 否 | 活动页展示标题 |
| activity_coupons[].display_description | string \| null | 否 | 活动页展示说明 |

**响应 201：**
```json
{
  "id": 1,
  "title": "沉浸式学习挑战赛",
  "description": "累计学习24小时赢好礼",
  "content_html": "<p>完成学习挑战后可领取专属卡券。</p>",
  "cover_image": "https://example.com/activity.jpg",
  "participant_count": 0,
  "sort_order": 1,
  "is_active": true,
  "activity_coupons": [],
  "activity_coupon_count": 0,
  "activity_coupon_claimed_count": 0,
  "created_at": "2026-04-20T10:00:00",
  "updated_at": "2026-04-20T10:00:00"
}
```

**错误码：**
- 401: 管理员凭证无效
- 422: 参数校验失败

---

### GET /admin/activities/{activity_id}

获取单个活动详情。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_id | integer | 活动 ID |

**响应 200：**
```json
{
  "id": 1,
  "title": "沉浸式学习挑战赛",
  "description": "累计学习24小时赢好礼",
  "content_html": "<p>完成学习挑战后可领取专属卡券。</p>",
  "cover_image": "https://example.com/activity.jpg",
  "participant_count": 326,
  "sort_order": 1,
  "is_active": true,
  "activity_coupons": [
    {
      "id": 10,
      "activity_id": 1,
      "coupon_id": 3,
      "total_quantity": 100,
      "claimed_quantity": 12,
      "remaining_quantity": 88,
      "per_user_limit": 1,
      "claim_starts_at": "2026-05-01T00:00:00",
      "claim_ends_at": "2026-05-31T23:59:59",
      "is_active": true,
      "sort_order": 1,
      "display_title": "挑战奖励券",
      "display_description": "完成活动即可领取",
      "coupon": {
        "id": 3,
        "name": "满20减3",
        "description": "全场通用",
        "type": "threshold_amount_off",
        "discount_amount": "3.00",
        "discount_percent": null,
        "min_order_amount": "20.00",
        "scope": "all",
        "seat_zone": null,
        "valid_from": "2026-05-01T00:00:00",
        "expires_at": "2026-05-31T23:59:59",
        "is_active": true
      }
    }
  ],
  "activity_coupon_count": 1,
  "activity_coupon_claimed_count": 12,
  "created_at": "2026-04-20T10:00:00",
  "updated_at": "2026-04-22T15:30:00"
}
```

**错误码：**
- 401: 管理员凭证无效
- 404: 活动不存在

---

### PUT /admin/activities/{activity_id}

更新活动。仅更新请求体中传递的字段。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_id | integer | 活动 ID |

**请求体（所有字段均可选）：**
```json
{
  "title": "更新后的标题",
  "description": "更新后的描述",
  "content_html": "<p>更新后的富文本正文</p>",
  "cover_image": "https://example.com/new-cover.jpg",
  "participant_count": 400,
  "sort_order": 2,
  "is_active": false,
  "activity_coupons": []
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 活动标题，最大100字 |
| description | string \| null | 活动描述，最大500字 |
| content_html | string \| null | 活动详情富文本正文；传入时会整体替换 |
| cover_image | string \| null | 封面图 URL，最大512字符 |
| participant_count | integer | 参与人数，最小 0 |
| sort_order | integer | 排序值 |
| is_active | boolean | 是否上架 |
| activity_coupons | array \| null | 活动关联卡券配置；传入时按列表整体同步，缺失的旧配置会删除或停用 |

**响应 200：** 返回更新后的活动对象（同 GET 单个活动）。

**错误码：**
- 401: 管理员凭证无效
- 404: 活动不存在
- 422: 参数校验失败

---

### DELETE /admin/activities/{activity_id}

删除活动。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_id | integer | 活动 ID |

**响应 204：** 无响应体。

**错误码：**
- 401: 管理员凭证无效
- 404: 活动不存在

---

### PATCH /admin/activities/{activity_id}/status

切换活动上架/下架状态。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| activity_id | integer | 活动 ID |

**请求体：**
```json
{
  "is_active": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| is_active | boolean | 是 | 目标状态 |

**响应 200：** 返回更新后的活动对象（同 GET 单个活动）。

**错误码：**
- 401: 管理员凭证无效
- 404: 活动不存在

---

## 五、图片上传

### POST /api/v1/admin/upload

管理端上传图片文件。服务端校验图片后上传到阿里 OSS；生产环境响应 URL 使用 `OSS_PUBLIC_BASE_URL` 配置的 CDN/自定义公开域名。开发或回滚模式可通过 `UPLOAD_STORAGE_DRIVER=local` 返回 `/uploads/...` 本地路径。

**认证：** Bearer 管理员 Token；兼容 legacy `X-Admin-Token`；必须具备 `upload:create` 权限。

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |
| scope | string | 否 | 图片业务范围，允许值：`avatar`、`activity-cover`、`room-cover`、`common`；默认 `common` |

**限制：**
- 支持格式：`.jpg`、`.jpeg`、`.png`、`.gif`、`.webp`
- `avatar` 最大 2MB
- `activity-cover`、`room-cover`、`common` 最大 5MB

**响应 200：**
```json
{
  "url": "https://cdn.example.com/images/activity-cover/2026/05/29/a1b2c3d4e5f6.png",
  "object_key": "images/activity-cover/2026/05/29/a1b2c3d4e5f6.png",
  "size": 123456,
  "content_type": "image/png"
}
```

**错误码：**
- 401: 管理员凭证无效
- 403: 缺少 `upload:create` 权限
- 422: 缺少文件 / scope 不受支持 / 仅支持图片文件 / 文件大小超过当前 scope 限制
- 503: 图片上传服务暂不可用，例如 OSS 必填配置缺失或 OSS 上传失败

### POST /api/v1/upload/image

用户端上传图片文件。当前用于 br-app 用户头像上传，服务端同样上传到阿里 OSS 并返回公开 URL。

**认证：** Bearer Token

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |
| scope | string | 否 | 图片业务范围。用户端当前仅允许 `avatar`；默认 `avatar` |

**限制：**
- 支持格式：`.jpg`、`.jpeg`、`.png`、`.gif`、`.webp`
- `avatar` 最大 2MB

**响应 200：**
```json
{
  "url": "https://cdn.example.com/images/avatar/2026/05/29/a1b2c3d4e5f6.png",
  "object_key": "images/avatar/2026/05/29/a1b2c3d4e5f6.png",
  "size": 123456,
  "content_type": "image/png"
}
```

**错误码：**
- 401: 未认证或 Token 无效
- 422: 缺少文件 / 非 `avatar` scope / 仅支持图片文件 / 文件大小超过 2MB
- 503: 图片上传服务暂不可用，例如 OSS 必填配置缺失或 OSS 上传失败

---

## 六、座位

### GET /api/v1/rooms/{room_id}/seats/

获取指定自习室的座位列表。无需认证。

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| date | string | - | 日期，格式 YYYY-MM-DD |
| start_time | string | - | 开始时间，格式 HH:MM |
| end_time | string | - | 结束时间，格式 HH:MM |

三个时间参数必须同时提供才会返回 `is_available` 字段。

**响应 200（不带时间参数）：**
```json
[
  {
    "id": 1,
    "room_id": 1,
    "seat_number": "A1-01",
    "zone": "quiet",
    "position": "靠窗",
    "floor": 3,
    "price_per_hour": "6.00",
    "status": "available",
    "row": 0,
    "col": 0
  }
]
```

**响应 200（带时间参数）：**
```json
[
  {
    "id": 1,
    "room_id": 1,
    "seat_number": "A1-01",
    "zone": "quiet",
    "position": "靠窗",
    "floor": 3,
    "price_per_hour": "6.00",
    "status": "available",
    "row": 0,
    "col": 0,
    "is_available": true
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 座位 ID |
| room_id | integer | 所属自习室 ID |
| seat_number | string | 座位编号，如 "A1-01" |
| zone | string | 区域：quiet / keyboard / vip |
| position | string \| null | 位置描述：靠窗 / 中间 / 独立 |
| floor | integer | 楼层，默认 3 |
| price_per_hour | decimal | 每小时价格（单位：元） |
| status | string | 状态：available / maintenance |
| row | integer | 座位图行号 |
| col | integer | 座位图列号 |
| is_available | boolean | 该时段是否可预约（仅带时间参数时返回） |

**错误码：**
- 404: 自习室不存在

---

## 七、卡券

所有卡券接口需要通过 `Authorization` header 传递 Bearer Token。

### GET /api/v1/coupons

获取当前登录用户持有的卡券列表，支持按动态状态过滤。

**认证：** Bearer Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| status | string | - | 状态筛选：available / used / expired |

`expired` 为动态状态：未使用但未到生效时间、已过期或模板停用的卡券不会作为可用券返回。

**响应 200：**
```json
[
  {
    "id": 12,
    "coupon_id": 3,
    "name": "满20减3",
    "description": "全场通用",
    "type": "threshold_amount_off",
    "scope": "all",
    "status": "available",
    "discount_amount": "3.00",
    "discount_percent": null,
    "min_order_amount": "20.00",
    "valid_from": "2026-05-01T00:00:00Z",
    "expires_at": "2026-05-31T23:59:59Z",
    "used_at": null,
    "used_booking_id": null,
    "seat_zone": null,
    "source_type": "activity",
    "source_activity_id": 1,
    "source_activity_coupon_id": 10
  }
]
```

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 用户卡券 ID，创建预约时传入 `coupon_id` |
| coupon_id | integer | 卡券模板 ID |
| name | string | 卡券名称 |
| description | string | 展示说明 |
| type | string | amount_off / threshold_amount_off / percentage_off |
| scope | string | all / first_booking / vip_only / seat_zone |
| status | string | available / used / expired |
| discount_amount | decimal \| null | 固定抵扣金额 |
| discount_percent | integer \| null | 折扣比例，80 表示 8 折 |
| min_order_amount | decimal | 使用门槛 |
| valid_from | datetime | 生效时间 |
| expires_at | datetime | 过期时间 |
| used_at | datetime \| null | 使用时间 |
| used_booking_id | integer \| null | 使用该券的预约 ID |
| seat_zone | string \| null | 指定座位类型范围 |
| source_type | string \| null | 卡券来源：activity 表示活动领取，空值表示其他来源 |
| source_activity_id | integer \| null | 来源活动 ID |
| source_activity_coupon_id | integer \| null | 来源活动卡券配置 ID |

**错误码：**
- 401: 未认证
- 422: status 参数值无效

---

### GET /api/v1/coupons/available-for-booking

根据预约参数返回当前用户可用于该订单的卡券，并返回每张券的抵扣金额和预计实付金额。

**认证：** Bearer Token

**查询参数：**

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| seat_id | integer | 是 | 座位 ID |
| date | string | 是 | 预约日期，格式 YYYY-MM-DD |
| start_time | string | 是 | 开始时间，格式 HH:MM |
| end_time | string | 是 | 结束时间，格式 HH:MM |

**响应 200：**
```json
{
  "original_price": "45.00",
  "items": [
    {
      "id": 12,
      "coupon_id": 3,
      "name": "满20减3",
      "description": "全场通用",
      "type": "threshold_amount_off",
      "scope": "all",
      "status": "available",
      "discount_amount": "3.00",
      "discount_percent": null,
      "min_order_amount": "20.00",
      "valid_from": "2026-05-01T00:00:00Z",
      "expires_at": "2026-05-31T23:59:59Z",
      "used_at": null,
      "used_booking_id": null,
      "seat_zone": null,
      "source_type": "activity",
      "source_activity_id": 1,
      "source_activity_coupon_id": 10,
      "payable_amount": "42.00"
    }
  ]
}
```

不可用卡券会被过滤，包括：不属于当前用户、已使用、未生效、已过期、模板停用、未达到满减门槛、不满足首次预约限制、非 VIP 用户使用 `vip_only` 卡券、座位类型不匹配。

**错误码：**
- 401: 未认证
- 404: 座位不存在
- 422: 查询参数格式无效

---

## 八、钱包

所有钱包接口需要通过 `Authorization` header 传递 Bearer Token。

### WeChat Pay recharge contract

Wallet recharge now uses WeChat Pay JSAPI for real payment. The client creates a
recharge order, calls `uni.requestPayment` with backend-signed JSAPI parameters,
then confirms the final wallet result by querying the backend order status.
Wallet crediting happens only after the backend receives a WeChat Pay callback,
verifies the signature, decrypts the notification resource, and validates the
business fields against the local order. Client-side payment success is not a
trusted source for balance changes.

#### POST /api/v1/wallet/recharge

Create a wallet recharge order and return WeChat Mini Program payment
parameters.

**Auth:** Bearer Token

**Request body:**
```json
{
  "amount": 100,
  "payment_method": "wechat",
  "promo_code": "SAVE30"
}
```

| Field | Type | Required | Notes |
|------|------|------|------|
| amount | number | yes | Recharge amount, greater than 0 and not more than 9999 |
| payment_method | string | yes | `wechat`; `alipay` is rejected until implemented |
| promo_code | string | no | Optional promo code |

**Response 201:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "100.00",
  "bonus_amount": "30.00",
  "status": "pending",
  "balance_after": null,
  "payment_provider": "wechat",
  "payment_status": "pending",
  "payment_params": {
    "timeStamp": "1778912580",
    "nonceStr": "random-nonce",
    "package": "prepay_id=wx201410272009395522657a690389285100",
    "signType": "RSA",
    "paySign": "signed-jsapi-parameters"
  }
}
```

`payment_params` maps directly to `uni.requestPayment`. The frontend must not
refresh or locally increase the wallet balance from `uni.requestPayment`
success. It should poll `GET /api/v1/wallet/recharge/{order_id}` and refresh
the balance only after the backend reports `status="completed"`.

**Errors:**
- 401: unauthenticated
- 404: user not found
- 422: invalid parameters, unsupported payment method, invalid promo code, or promo-code minimum not met
- 503: WeChat Pay disabled or missing required configuration

#### GET /api/v1/wallet/recharge/{order_id}

Return the authenticated user's recharge order status. Orders owned by another
user must return 404.

**Auth:** Bearer Token

**Response 200:**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "100.00",
  "bonus_amount": "30.00",
  "status": "pending",
  "payment_provider": "wechat",
  "payment_status": "pending",
  "balance_after": null,
  "membership_upgraded": false,
  "vip_coupon_id": null
}
```

After a verified callback is processed, `status` becomes `completed`,
`payment_status` becomes `paid`, and `balance_after` contains the post-credit
wallet balance. If the recharge amount is at least 100 and the user was not
already a member, `membership_upgraded` becomes `true` and `vip_coupon_id`
contains the issued VIP welcome user-coupon ID. Time fields such as `paid_at`
and `notify_processed_at`, when exposed, should be serialized consistently.
Avoid mixing timezone-aware and timezone-naive `DateTime` values in database
persistence.

**Errors:**
- 401: unauthenticated
- 404: order not found or belongs to another user

#### POST /api/v1/wallet/wechat/notify

Receive WeChat Pay API v3 asynchronous notifications. This endpoint does not use
user Bearer authentication because the caller is WeChat Pay. Its trust boundary
is the WeChat Pay signature headers, successful API v3 resource decryption, and
business validation against the local pending order.

**Auth:** WeChat Pay API v3 signature verification

**Required headers:**

| Header | Required | Notes |
|------|------|------|
| Wechatpay-Signature | yes | WeChat Pay request signature |
| Wechatpay-Timestamp | yes | Signature timestamp; reject stale or invalid values |
| Wechatpay-Nonce | yes | Signature nonce |
| Wechatpay-Serial | yes | Platform certificate serial number |

**Request body:** WeChat Pay API v3 notification JSON, including encrypted
`resource`.

**Processing requirements:**
- Verify the signature before decrypting or mutating state.
- Decrypt `resource` with `WECHAT_PAY_API_V3_KEY`.
- Validate `appid`, `mchid`, `out_trade_no`, `trade_state="SUCCESS"`, amount,
  and currency against the local pending recharge order.
- Handle duplicate notifications idempotently. A completed/paid order returns
  success without crediting the balance again.
- Save only sanitized callback details needed for audit/debugging.
- Reject malformed callbacks, signature/decrypt failures, amount mismatches, and
  unexpected app/merchant IDs without changing wallet balances.

**Success response 200:**
```json
{
  "code": "SUCCESS",
  "message": "OK"
}
```

**Failure response:**
```json
{
  "code": "FAIL",
  "message": "invalid notification"
}
```

Failure messages must not include API v3 keys, private-key content, decrypted
sensitive payloads, or certificate material.

**Errors:**
- 400: malformed callback, decrypted payload validation failed, amount or currency mismatch
- 401/403: invalid WeChat Pay signature or certificate serial
- 503: WeChat Pay disabled or misconfigured

#### WeChat Pay operational configuration

Required environment variables when `WECHAT_PAY_ENABLED=true`:

| Variable | Purpose |
|------|------|
| WECHAT_PAY_ENABLED | Enables real WeChat Pay integration; keep `false` for local/dev without real payment |
| WECHAT_PAY_APPID | Mini Program AppID used for JSAPI payment |
| WECHAT_PAY_MCHID | WeChat Pay merchant ID |
| WECHAT_PAY_API_V3_KEY | API v3 key used to decrypt notification resources |
| WECHAT_PAY_PRIVATE_KEY_PATH | Filesystem path to the merchant private key |
| WECHAT_PAY_CERT_SERIAL_NO | Merchant certificate serial number used for request signing |
| WECHAT_PAY_PLATFORM_CERT_SERIAL_NO | WeChat Pay platform certificate/public-key serial expected on notify headers |
| WECHAT_PAY_PLATFORM_PUBLIC_KEY_PATH | Filesystem path to the WeChat Pay platform public key used to verify notify signatures |
| WECHAT_PAY_NOTIFY_URL | Public HTTPS callback URL routed to `/api/v1/wallet/wechat/notify` |
| WECHAT_PAY_BOOKING_NOTIFY_URL | Public HTTPS callback URL routed to `/api/v1/bookings/wechat/notify`; falls back to `WECHAT_PAY_NOTIFY_URL` if unset |
| WECHAT_PAY_API_BASE_URL | WeChat Pay API base URL; use the official production URL unless testing against a controlled mock |

Operational cautions:
- Do not hardcode or commit real AppIDs, merchant IDs, API v3 keys, private keys,
  certificate contents, or platform certificates. Store secrets in deployment
  secret management or environment variables, and keep examples to variable
  names only.
- `WECHAT_PAY_NOTIFY_URL` must be publicly reachable by WeChat over HTTPS and
  must route to this backend deployment. Localhost or private intranet URLs will
  not receive production callbacks.
- To disable WeChat Pay safely, set `WECHAT_PAY_ENABLED=false` and ensure the
  frontend blocks new WeChat recharge attempts. Existing pending orders should
  remain pending unless a verified callback is later processed.
- When storing callback timestamps such as `paid_at` and `notify_processed_at`,
  keep the same timezone policy used by the wallet transaction model. Avoid
  writing timezone-aware datetimes into timezone-naive database columns.
- Frontend polling must handle races: payment UI success can arrive before the
  backend callback, duplicate taps can create multiple orders, and delayed
  callbacks can complete after the first poll window. Keep separate UI states for
  order creation, WeChat payment, and backend confirmation.

The older simulated confirm endpoint below is for local/test flows only and
must not be used by production recharge crediting.

---

### POST /api/v1/wallet/recharge

创建充值订单。当前为模拟支付流程，创建订单后调用确认接口完成入账。

**认证：** Bearer Token

**请求体：**
```json
{
  "amount": 100,
  "payment_method": "wechat",
  "promo_code": "SAVE30"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| amount | number | 是 | 充值金额，必须 >0 且 <=9999 |
| payment_method | string | 是 | 支付方式：wechat / alipay |
| promo_code | string | 否 | 优惠码 |

**响应 201：**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "100.00",
  "bonus_amount": "30.00",
  "status": "pending",
  "balance_after": null,
  "membership_upgraded": false,
  "vip_coupon_id": null
}
```

**错误码：**
- 401: 未认证
- 404: 用户不存在
- 422: 参数校验失败 / 优惠码无效 / 优惠码已过期 / 未达到优惠码最低充值金额

---

### POST /api/v1/wallet/recharge/{order_id}/confirm

确认充值订单并更新账户余额。

**认证：** Bearer Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| order_id | uuid | 充值订单 ID |

**响应 200：**
```json
{
  "order_id": "550e8400-e29b-41d4-a716-446655440000",
  "amount": "100.00",
  "bonus_amount": "30.00",
  "status": "completed",
  "balance_after": "386.00",
  "membership_upgraded": true,
  "vip_coupon_id": 18
}
```

当单笔充值金额 `>= 100` 且用户 `membership_level` 为 `none` 时，确认入账会在同一数据库事务内升级用户为 VIP，并发放 `scope=vip_only` 的欢迎券。`membership_upgraded` 表示该笔订单是否触发升级，`vip_coupon_id` 为发放后的用户卡券 ID。

**错误码：**
- 401: 未认证
- 404: 订单不存在
- 409: 订单已处理

---

### GET /api/v1/wallet/balance

获取当前账户余额和累计充值金额。

**认证：** Bearer Token

**响应 200：**
```json
{
  "balance": "256.00",
  "total_recharged": "1200.00"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| balance | decimal | 当前账户余额 |
| total_recharged | decimal | 累计成功充值金额 |

**错误码：**
- 401: 未认证
- 404: 用户不存在

---

### GET /api/v1/wallet/transactions

返回当前认证用户的钱包流水列表。后端必须按 Bearer Token 解析出的当前用户过滤流水记录，客户端不得传递 `user_id`。结果按 `created_at` 倒序返回，并使用稳定的次级排序避免同时间记录顺序漂移。

**认证：** Bearer Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码，最小值为 1 |
| page_size | integer | 20 | 每页数量，最小值为 1，最大值为 50 |
| type | string | all | 流水类型筛选：all / recharge / consume / refund / booking_refund |

**响应 200：**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "recharge",
      "title": "充值到账",
      "amount": "100.00",
      "bonus_amount": "30.00",
      "direction": "income",
      "status": "completed",
      "payment_method": "wechat",
      "balance_after": "386.00",
      "created_at": "2026-05-17T10:00:00",
      "completed_at": "2026-05-17T10:01:30",
      "order_id": "550e8400-e29b-41d4-a716-446655440000",
      "booking_id": null
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 20,
  "has_more": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 当前用户的钱包流水记录 |
| total | integer | 当前筛选条件下的总记录数 |
| page | integer | 当前页码 |
| page_size | integer | 当前每页数量 |
| has_more | boolean | 是否还有下一页 |

**items 字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 流水记录 ID |
| type | string | 流水类型：recharge / consume / refund / booking_refund |
| title | string | 展示标题，例如 `充值到账`、`充值待支付`、`充值失败`、`取消退款` |
| amount | decimal string | 流水金额；客户端不得用浮点数参与资金计算 |
| bonus_amount | decimal string | 赠送金额，无赠送时为 `0.00` |
| direction | string | 金额方向，例如 `income` |
| status | string | 流水状态，例如 pending / completed / failed |
| payment_method | string \| null | 支付方式，例如 wechat / alipay |
| balance_after | decimal string \| null | 交易后余额；待支付或失败记录可以为 null |
| created_at | datetime | 流水创建时间 |
| completed_at | datetime \| null | 支付完成时间或等价完成时间 |
| order_id | string \| null | 关联充值/订单 ID |
| booking_id | integer \| null | 预约取消退款关联的预约 ID；非预约退款为空 |

当 `type=consume`、`type=refund` 或 `type=booking_refund` 暂无匹配记录时，接口仍返回 200，`items` 为空数组，`total` 为 0，并返回请求对应的分页元数据。`booking_refund` 流水表示预约取消退款，方向为 `income`，状态为 `completed`，钱包流水标题展示为“取消退款”。

**错误码：**
- 401: 未认证 / Token 已过期或失效
- 422: `page < 1` / `page_size < 1` / `page_size > 50` / `type` 参数不支持

---

### POST /api/v1/wallet/promo-code

校验充值优惠码并返回可赠送金额。

**认证：** Bearer Token

**请求体：**
```json
{
  "code": "SAVE30"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| code | string | 是 | 优惠码 |

**响应 200：**
```json
{
  "code": "SAVE30",
  "description": "充值100送30",
  "bonus_amount": "30.00"
}
```

**错误码：**
- 401: 未认证
- 422: 优惠码无效 / 优惠码已过期

---

## 九、管理端 - 卡券管理

管理端卡券接口支持 Bearer Token 或 `X-Admin-Token` 管理员认证，并需要对应 RBAC 权限。

### GET /api/v1/admin/coupons

分页查询卡券模板。

**权限：** `coupon:view`

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码 |
| page_size | integer | 10 | 每页数量，最大 100 |
| keyword | string | - | 搜索名称或描述 |
| type | string | - | threshold_amount_off / amount_off / percentage_off |
| scope | string | - | all / first_booking / vip_only / seat_zone |
| is_active | boolean | - | 是否启用 |

**响应 200：**
```json
{
  "total": 1,
  "page": 1,
  "page_size": 10,
  "items": [
    {
      "id": 3,
      "name": "VIP专享8折券",
      "description": "VIP 用户可用",
      "type": "percentage_off",
      "discount_amount": null,
      "discount_percent": 80,
      "min_order_amount": "0.00",
      "scope": "vip_only",
      "seat_zone": null,
      "valid_from": "2026-06-08T00:00:00",
      "expires_at": "2026-07-08T00:00:00",
      "is_active": true,
      "created_at": "2026-06-08T10:00:00",
      "updated_at": "2026-06-08T10:00:00"
    }
  ]
}
```

### POST /api/v1/admin/coupons

创建卡券模板。

**权限：** `coupon:create`

**请求体：**
```json
{
  "name": "满100减20",
  "description": "全场通用",
  "type": "threshold_amount_off",
  "discount_amount": "20.00",
  "discount_percent": null,
  "min_order_amount": "100.00",
  "scope": "all",
  "seat_zone": null,
  "valid_from": "2026-06-08T00:00:00",
  "expires_at": "2026-07-08T00:00:00",
  "is_active": true
}
```

优惠规则：

| type | 规则 |
|------|------|
| threshold_amount_off | `discount_amount` 必填，`min_order_amount > 0` |
| amount_off | `discount_amount` 必填 |
| percentage_off | `discount_percent` 必填，取值 1-99，80 表示 8 折 |

`scope=seat_zone` 时 `seat_zone` 表示指定座位区域；其他 scope 会忽略 `seat_zone`。时间字段按 Asia/Shanghai 业务时间写入数据库。

**响应 201：** 返回创建后的卡券对象。

### GET /api/v1/admin/coupons/{coupon_id}

获取卡券模板详情。

**权限：** `coupon:view`

### PUT /api/v1/admin/coupons/{coupon_id}

更新卡券模板。已关联活动的卡券禁止修改 `type`。

**权限：** `coupon:update`

### PATCH /api/v1/admin/coupons/{coupon_id}/status

启用或停用卡券模板。

**权限：** `coupon:update`

**请求体：**
```json
{ "is_active": false }
```

已过期卡券禁止重新启用。

### DELETE /api/v1/admin/coupons/{coupon_id}

删除未关联、未发放的卡券模板。

**权限：** `coupon:delete`

已关联活动或已发放给用户的卡券禁止删除。

**错误码：**
- 401: 未认证
- 403: 缺少对应 `coupon:*` 权限
- 404: 卡券不存在
- 422: 参数校验失败或业务规则不允许

---

## 十、管理端 - 钱包管理

管理端钱包接口支持 Bearer Token 或 `X-Admin-Token` 管理员认证，并需要对应 RBAC 权限。

### GET /api/v1/admin/wallet/transactions

分页查询钱包交易流水。

**权限：** `wallet:view`

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码，最小值为 1 |
| page_size | integer | 10 | 每页数量 |
| type | string | - | 流水类型筛选：recharge / consume / refund |
| status | string | - | 流水状态筛选：pending / completed / failed / cancelled |
| user_id | string | - | 用户 ID |
| date_start | date | - | 起始日期，格式 YYYY-MM-DD |
| date_end | date | - | 截止日期，格式 YYYY-MM-DD |

**响应 200：**
```json
{
  "items": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "type": "recharge",
      "title": "充值到账",
      "amount": "100.00",
      "bonus_amount": "30.00",
      "direction": "income",
      "status": "completed",
      "payment_method": "wechat",
      "balance_after": "386.00",
      "created_at": "2026-05-17T10:00:00",
      "completed_at": "2026-05-17T10:01:30",
      "order_id": "550e8400-e29b-41d4-a716-446655440000",
      "user_id": "11111111-2222-3333-4444-555555555555",
      "user_nickname": "学习达人",
      "user_phone": "13800138000"
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10,
  "has_more": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| items | array | 当前筛选条件下的钱包流水记录 |
| total | integer | 总记录数 |
| page | integer | 当前页码 |
| page_size | integer | 当前每页数量 |
| has_more | boolean | 是否还有下一页 |

**items 字段：**

| 字段 | 类型 | 说明 |
|------|------|------|
| id | string | 流水记录 ID |
| type | string | 流水类型：recharge / consume / refund |
| title | string | 展示标题 |
| amount | decimal string | 流水金额 |
| bonus_amount | decimal string | 赠送金额 |
| direction | string | 金额方向，例如 income / outcome |
| status | string | 流水状态 |
| payment_method | string \| null | 支付方式 |
| balance_after | decimal string \| null | 交易后余额 |
| created_at | datetime | 流水创建时间 |
| completed_at | datetime \| null | 完成时间 |
| order_id | string \| null | 关联充值/订单 ID |
| user_id | string | 用户 ID |
| user_nickname | string \| null | 用户昵称 |
| user_phone | string \| null | 用户手机号 |

**错误码：**
- 401: 未认证
- 403: 缺少 `wallet:view` 权限
- 422: 查询参数格式无效

---

### GET /api/v1/admin/wallet/statistics

查询钱包财务统计。

**权限：** `wallet:view`

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| date_start | date | - | 起始日期，格式 YYYY-MM-DD |
| date_end | date | - | 截止日期，格式 YYYY-MM-DD |

**响应 200：**
```json
{
  "total_recharge": "1200.00",
  "total_consume": "860.00",
  "total_refund": "40.00",
  "net_income": "820.00",
  "active_users": 18,
  "total_transactions": 96
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| total_recharge | decimal string | 充值总额 |
| total_consume | decimal string | 消费总额 |
| total_refund | decimal string | 退款总额 |
| net_income | decimal string | 净收入 |
| active_users | integer | 有交易记录的去重用户数 |
| total_transactions | integer | 交易总数 |

**错误码：**
- 401: 未认证
- 403: 缺少 `wallet:view` 权限
- 422: 查询参数格式无效

---

### GET /api/v1/admin/wallet/transactions/export

按筛选条件导出钱包交易流水 CSV。导出不分页，单次最多 10000 条记录，超过上限会返回 400，需缩小筛选范围。

**权限：** `wallet:export`

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| type | string | - | 流水类型筛选：recharge / consume / refund |
| status | string | - | 流水状态筛选：pending / completed / failed / cancelled |
| user_id | string | - | 用户 ID |
| date_start | date | - | 起始日期，格式 YYYY-MM-DD |
| date_end | date | - | 截止日期，格式 YYYY-MM-DD |

**响应 200：** CSV 文件下载。

响应头：

| Header | 说明 |
|------|------|
| Content-Type | `text/csv; charset=utf-8-sig` |
| Content-Disposition | `attachment; filename="wallet_transactions_{date}.csv"` |

CSV 列：交易时间、用户ID、用户昵称、手机号、交易类型、金额、余额、状态、支付方式。

**错误码：**
- 400: 导出数据超过 10000 条上限
- 401: 未认证
- 403: 缺少 `wallet:export` 权限
- 422: 查询参数格式无效

### RBAC 操作说明

`wallet:view` 和 `wallet:export` 权限需要通过管理后台「系统设置 → 菜单权限」或等价数据库运维流程手动配置。建议新增「钱包管理」菜单和「钱包流水」子菜单，将 `wallet:view` 绑定到页面访问权限，并将 `wallet:export` 分配给允许导出 CSV 的角色。

---

## 九、预约

所有预约接口需要通过 `Authorization` header 传递 Bearer Token。

### POST /api/v1/bookings/

创建座位预约。

**认证：** Bearer Token

**请求体：**
```json
{
  "seat_id": 1,
  "date": "2026-05-01",
  "start_time": "09:00",
  "end_time": "12:00",
  "payment_method": "balance",
  "coupon_id": 12
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| seat_id | integer | 是 | 座位 ID |
| date | string | 是 | 预约日期，格式 YYYY-MM-DD |
| start_time | string | 是 | 开始时间，格式 HH:MM |
| end_time | string | 是 | 结束时间，格式 HH:MM |
| payment_method | string | 否 | 支付方式：`balance` 账户余额支付（默认）/ `wechat` 微信支付 |
| coupon_id | integer \| null | 否 | 用户卡券 ID，每个订单最多使用 1 张卡券 |

当 `payment_method="balance"` 时，后端使用账户余额即时扣款，创建成功后预约 `payment_status="paid"`。

当 `payment_method="wechat"` 时，后端创建待支付预约并调用微信 JSAPI 预下单，响应额外返回 `payment_params`。客户端应将 `payment_params` 原样传给 `uni.requestPayment`。若微信支付配置不可用或预下单失败，后端不会创建预约记录。

**响应 201：**
```json
{
  "id": 1,
  "seat_id": 1,
  "user_id": "11111111-2222-3333-4444-555555555555",
  "room_id": 1,
  "date": "2026-05-01",
  "start_time": "09:00:00",
  "end_time": "12:00:00",
  "status": "pending_start",
  "original_price": "18.00",
  "discount_amount": "3.00",
  "total_price": "15.00",
  "coupon_id": 12,
      "payment_method": "balance",
      "payment_status": "paid",
      "payment_provider": null,
      "paid_at": "2026-05-01T08:00:00",
      "cancelled_at": null,
      "penalty_amount": "0.00",
      "refund_amount": "0.00",
      "cancel_policy": null,
      "refund_transaction_id": null,
      "can_cancel": true,
      "created_at": "2026-05-01T08:00:00",
  "seat": {
    "id": 1,
    "seat_number": "A1-01",
    "zone": "quiet",
    "position": "靠窗",
    "price_per_hour": "6.00"
  },
  "room": {
    "id": 1,
    "name": "安静自习室·油城店",
    "address": "茂名市茂南区油城三路88号"
  }
}
```

微信支付创建成功时，响应中的支付字段示例：

```json
{
  "id": 2,
  "seat_id": 1,
  "user_id": "11111111-2222-3333-4444-555555555555",
  "room_id": 1,
  "date": "2026-05-01",
  "start_time": "09:00:00",
  "end_time": "12:00:00",
  "status": "pending_start",
  "original_price": "18.00",
  "discount_amount": "3.00",
  "total_price": "15.00",
  "coupon_id": 12,
  "payment_method": "wechat",
  "payment_status": "pending",
  "payment_provider": "wechat",
  "paid_at": null,
  "payment_params": {
    "timeStamp": "1777603200",
    "nonceStr": "c1f7b8d9e0a2",
    "package": "prepay_id=wx201410272009395522657a690389285100",
    "signType": "RSA",
    "paySign": "base64-signature"
  },
  "created_at": "2026-05-01T08:00:00",
  "seat": {
    "id": 1,
    "seat_number": "A1-01",
    "zone": "quiet",
    "position": "靠窗",
    "price_per_hour": "6.00"
  },
  "room": {
    "id": 1,
    "name": "安静自习室·油城店",
    "address": "茂名市茂南区油城三路88号"
  }
}
```

| 响应字段 | 类型 | 说明 |
|------|------|------|
| payment_method | string | 支付方式：`balance` / `wechat` |
| payment_status | string | 支付状态：`pending` / `paid` / `failed` |
| payment_provider | string \| null | 第三方支付渠道；余额支付为 `null`，微信支付为 `wechat` |
| paid_at | string \| null | 支付完成时间；待支付时为 `null` |
| payment_params | object \| null | 仅微信支付创建成功时返回，供小程序端调用 `uni.requestPayment` |
| payment_params.timeStamp | string | 微信 JSAPI 支付时间戳 |
| payment_params.nonceStr | string | 微信 JSAPI 支付随机串 |
| payment_params.package | string | 微信 JSAPI 支付包，格式为 `prepay_id=...` |
| payment_params.signType | string | 签名类型，通常为 `RSA` |
| payment_params.paySign | string | 微信 JSAPI 支付签名 |

**错误码：**
- 401: 未认证
- 404: 座位不存在
- 402: 余额不足
- 409: 该座位该时段已被预约
- 422: 结束时间必须晚于开始时间
- 400: 该座位正在维护中
- 400: 卡券不可用，请重新选择（不存在、不属于当前用户、已使用、未生效、已过期、停用、门槛不足或适用范围不匹配）
- 503: 微信支付暂不可用 / 微信预下单失败

---

### GET /api/v1/bookings/

获取当前用户的预约列表。

**认证：** Bearer Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| page_size | integer | 10 | 每页数量（最大 50） |
| status | string | - | 状态筛选：pending_start / in_progress / cancelled / completed |

> **状态词表（BREAKING，已翻转）**：DB `status` 真实值由旧 `pending`/`confirmed` 统一为 `pending_start`/`in_progress`（详见 `docs/booking-rules.md`）。C 端 `?status=` 查询契约**保持稳定**：`?status=pending_start` 为派生筛选（返回 `status IN ('pending_start','pending_confirm') AND payment_status='paid'`）；`?status=in_progress` 为派生筛选（返回 `status='in_progress' AND payment_status='paid'`，课程订单附加 `start_date <= today` 后置过滤，座位订单不做二次过滤）。响应体 `status` 字段返回 DB 真实值，前端不再做展示态派生。

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "seat_id": 1,
      "user_id": "uuid-string",
      "room_id": 1,
      "date": "2026-05-01",
      "start_time": "09:00:00",
      "end_time": "12:00:00",
      "status": "pending_start",
      "original_price": "18.00",
      "discount_amount": "0.00",
      "total_price": "18.00",
      "coupon_id": null,
      "created_at": "2026-05-01T08:00:00",
      "seat": { "id": 1, "seat_number": "A1-01", "zone": "quiet", "position": "靠窗", "price_per_hour": "6.00" },
      "room": { "id": 1, "name": "安静自习室", "address": "茂名市茂南区油城三路88号" }
    }
  ],
  "total": 1,
  "page": 1,
  "page_size": 10
}
```

**错误码：**
- 401: 未认证
- 422: status 参数值无效

---

### GET /api/v1/bookings/{booking_id}

获取预约详情。仅能查看自己的预约。

**认证：** Bearer Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| booking_id | integer | 预约 ID |

**响应 200：** 同创建预约的响应格式。列表和详情都会返回 `can_cancel`、`cancelled_at`、`penalty_amount`、`refund_amount`、`cancel_policy`、`refund_transaction_id` 等取消相关字段。后端会在列表/详情返回前把已到开始时间的已支付确认预约同步为 `completed`，因此这类订单 `can_cancel=false`。

**错误码：**
- 401: 未认证
- 404: 预约不存在 / 无权查看

---

### GET /api/v1/bookings/{booking_id}/payment-status

查询预约支付状态。微信支付成功后，客户端可轮询该接口确认异步回调是否已完成。仅能查询自己的预约；查询他人预约时返回 404。

**认证：** Bearer Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| booking_id | integer | 预约 ID |

**响应 200：**
```json
{
  "booking_id": 2,
  "payment_status": "paid",
  "paid_at": "2026-05-01T08:03:12",
  "transaction_id": "4200002401202605011234567890"
}
```

待支付时：
```json
{
  "booking_id": 2,
  "payment_status": "pending",
  "paid_at": null,
  "transaction_id": null
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| booking_id | integer | 预约 ID |
| payment_status | string | 支付状态：`pending` / `paid` / `failed` |
| paid_at | string \| null | 支付完成时间 |
| transaction_id | string \| null | 微信支付交易号；未支付或余额支付无微信交易号时为 `null` |

**错误码：**
- 401: 未认证
- 404: 预约不存在 / 无权查看

---

### POST /api/v1/bookings/wechat/notify

微信支付 API v3 异步通知回调，用于预约直接微信支付。该接口由微信支付平台调用，不要求 Bearer Token；后端必须校验微信支付签名并解密通知资源，只有签名有效、`trade_state="SUCCESS"` 且金额匹配时才更新预约支付状态。

**认证：** 微信支付回调签名

**请求头：**

| Header | 说明 |
|------|------|
| Wechatpay-Timestamp | 微信支付通知时间戳 |
| Wechatpay-Nonce | 微信支付通知随机串 |
| Wechatpay-Signature | 微信支付通知签名 |
| Wechatpay-Serial | 微信支付平台证书序列号 |

**请求体：**
```json
{
  "id": "EV-2018022511223320873",
  "create_time": "2026-05-01T08:03:12+08:00",
  "event_type": "TRANSACTION.SUCCESS",
  "resource_type": "encrypt-resource",
  "summary": "支付成功",
  "resource": {
    "algorithm": "AEAD_AES_256_GCM",
    "ciphertext": "base64-ciphertext",
    "associated_data": "transaction",
    "nonce": "resource-nonce",
    "original_type": "transaction"
  }
}
```

解密后的资源应包含微信交易信息，关键字段如下：

```json
{
  "out_trade_no": "BK-2",
  "transaction_id": "4200002401202605011234567890",
  "trade_state": "SUCCESS",
  "amount": {
    "total": 1500,
    "payer_total": 1500,
    "currency": "CNY",
    "payer_currency": "CNY"
  },
  "success_time": "2026-05-01T08:03:12+08:00"
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| out_trade_no | string | 商户订单号，预约支付格式为 `BK-{booking_id}` |
| transaction_id | string | 微信支付交易号 |
| trade_state | string | 仅 `SUCCESS` 会确认预约支付 |
| amount.total | integer | 订单金额，单位为分；必须与预约 `total_price` 匹配 |
| success_time | string | 微信支付完成时间 |

**成功响应 200：**
```json
{
  "code": "SUCCESS",
  "message": "成功"
}
```

**失败响应：**
```json
{
  "code": "FAIL",
  "message": "签名校验失败"
}
```

**处理说明：**
- 通知是预约微信支付确认的可信来源；前端支付成功回调只用于触发轮询。
- 重复成功通知必须幂等处理：若预约已是 `payment_status="paid"`，仍返回成功响应，不重复更新。
- 金额不匹配、签名无效、解密失败或预约不存在时，不更新预约状态，并返回失败响应。
- 回调仅处理商户订单号前缀为 `BK-` 的预约支付；钱包充值回调继续使用 `POST /api/v1/wallet/wechat/notify`。

---

### POST /api/v1/bookings/{booking_id}/cancel/

取消预约。仅当前用户自己的、`status` 为 `pending_start`/`in_progress`、`payment_status="paid"`、且尚未到预约开始时间的预约可取消。若该预约使用了卡券，取消成功后对应用户卡券恢复为 `available`，并清空 `used_booking_id` 和 `used_at`。余额支付和微信支付预约取消后均退回钱包，不做微信原路退款。

**认证：** Bearer Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| booking_id | integer | 预约 ID |

**扣费规则：**

| 距预约开始时间 | 扣费 | 退款 |
|------|------|------|
| 大于 48 小时 | 0% | 全额退回钱包 |
| 大于 24 小时且小于等于 48 小时 | 10% | 剩余 90% 退回钱包 |
| 大于 2 小时且小于等于 24 小时 | 20% | 剩余 80% 退回钱包 |
| 大于 0 且小于等于 2 小时 | 50% | 剩余 50% 退回钱包 |
| 已到预约开始时间 | 不允许取消 | 订单同步为已完成 |

**响应 200：** 返回更新后的预约对象，`status` 变为 `"cancelled"`。响应包含 `cancelled_at`、`penalty_amount`、`refund_amount`、`cancel_policy`、`refund_transaction_id`、`can_cancel=false`。后端会增加用户钱包余额，并创建一条 `type="booking_refund"` 的钱包流水，标题展示为“取消退款”，`booking_id` 关联被取消的预约。

**错误码：**
- 401: 未认证
- 400: 该预约已取消
- 400: 未支付预约不可取消
- 400: 预约已开始不可取消（订单会同步为 `completed`，不创建退款流水）
- 400: 该预约不可取消
- 404: 预约不存在 / 无权操作

## 九、学习记录

所有学习记录接口需要通过 `Authorization` header 传递 Bearer Token。

### GET /api/v1/study-records/summary

Get monthly study summary.

**Authentication:** Bearer Token

**Query Parameters:**

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| month | string | Yes | Month in YYYY-MM format |

**Response 200:**
```json
{
  "monthly_hours": 32.0,
  "monthly_bookings": 15,
  "max_streak_days": 7,
  "total_hours": 128.0,
  "calendar_mark": [
    { "date": "2026-05-01", "studied": true },
    { "date": "2026-05-02", "studied": false }
  ]
}
```

| Field | Type | Description |
|-------|------|-------------|
| monthly_hours | float | Monthly study hours |
| monthly_bookings | int | Monthly booking count |
| max_streak_days | int | Longest consecutive study days |
| total_hours | float | Total study hours (all time) |
| calendar_mark | array | Daily study marks for the month |
| calendar_mark[].date | date | Date |
| calendar_mark[].studied | bool | Whether studied that day |

**Error codes:**
- 401: Not authenticated
- 422: Invalid month format

### GET /api/v1/study-records

Get paginated study record list.

**Authentication:** Bearer Token

**Query Parameters:**

| Field | Type | Default | Description |
|-------|------|---------|-------------|
| page | integer | 1 | Page number (from 1) |
| page_size | integer | 10 | Items per page (max 50) |
| month | string | - | Optional month filter (YYYY-MM) |

**Response 200:**
```json
{
  "items": [
    {
      "id": 1,
      "room_name": "光谷自习室",
      "seat_number": "A-12",
      "date": "2026-05-16",
      "start_time": "10:00:00",
      "end_time": "12:00:00",
      "hours": 2.0,
      "total_price": "12.00"
    }
  ],
  "total": 30,
  "page": 1,
  "page_size": 10
}
```

| Field | Type | Description |
|-------|------|-------------|
| id | integer | Record ID |
| room_name | string | Study room name |
| seat_number | string | Seat number |
| date | date | Study date |
| start_time | time | Start time |
| end_time | time | End time |
| hours | float | Study duration in hours |
| total_price | decimal | Total price |

**Error codes:**
- 401: Not authenticated
- 422: Invalid parameter values

## Seats API

### GET /api/v1/rooms/{room_id}/seats/

List seats for a room, with optional availability check for a time slot.

Query Parameters:
- `date` (optional, string): Filter by date in YYYY-MM-DD format
- `start_time` (optional, string): Filter by start time in HH:MM format
- `end_time` (optional, string): Filter by end time in HH:MM format

Response (200):
```json
[
  {
    "id": 1,
    "room_id": 1,
    "seat_number": "A-01",
    "zone": "quiet",
    "position": "靠窗",
    "floor": 3,
    "price_per_hour": "6.00",
    "status": "available",
    "row": 0,
    "col": 0,
    "is_available": true
  }
]
```

Note: `is_available` is only meaningful when `date`, `start_time`, and `end_time` are all provided.

## Bookings API

### POST /api/v1/bookings/

Create a new booking. Requires authentication (Bearer token).

Request Body:
```json
{
  "seat_id": 1,
  "date": "2026-05-01",
  "start_time": "09:00",
  "end_time": "12:00"
}
```

Response (201):
```json
{
  "id": 1,
  "seat_id": 1,
  "user_id": "...",
  "room_id": 1,
  "date": "2026-05-01",
  "start_time": "09:00",
  "end_time": "12:00",
  "status": "pending_start",
  "total_price": "18.00",
  "created_at": "2026-05-01T09:00:00",
  "seat": { "id": 1, "seat_number": "A-01", "zone": "quiet", "position": "靠窗", "price_per_hour": "6.00" },
  "room": { "id": 1, "name": "光谷自习室", "address": "茂名市茂南区光谷大道88号" }
}
```

Error Responses:
- `401` — Not authenticated
- `404` — Seat not found
- `409` — Time conflict (seat already booked for this slot)
- `422` — Invalid time range (end_time <= start_time)

### GET /api/v1/bookings/

List current user's bookings. Requires authentication.

Query Parameters:
- `page` (int, default 1)
- `page_size` (int, default 10, max 50)
- `status` (optional, string): Filter by status — `pending_start`, `in_progress`, `cancelled`, `completed`

Response (200):
```json
{
  "items": [ ... ],
  "total": 15,
  "page": 1,
  "page_size": 10
}
```

### GET /api/v1/bookings/{booking_id}/

Get a single booking detail. Requires authentication. Only returns bookings belonging to the current user.

## 九、管理端 - 自习室管理

所有管理端接口需要通过 `X-Admin-Token` header 传递管理员 Token。

### POST /api/v1/admin/rooms

创建自习室。

**认证：** X-Admin-Token

**请求体：**
```json
{
  "name": "安静自习室·油城店",
  "address": "茂名市茂南区油城三路88号",
  "description": "宽敞明亮的沉浸式自习空间",
  "cover_image": "https://example.com/room.jpg",
  "business_hours": "07:00-23:00",
  "min_price": 8.00
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| name | string | 是 | 自习室名称，最大100字 |
| address | string | 是 | 地址，最大255字 |
| description | string | 否 | 描述，最大1000字 |
| cover_image | string | 否 | 封面图 URL，最大512字符 |
| business_hours | string | 否 | 营业时间，如 "07:00-23:00"，最大50字 |
| min_price | decimal | 否 | 最低价格（单位：元），默认 0 |

**响应 201：**
```json
{
  "id": 1,
  "name": "安静自习室·油城店",
  "description": "宽敞明亮的沉浸式自习空间",
  "cover_image": "https://example.com/room.jpg",
  "address": "茂名市茂南区油城三路88号",
  "business_hours": "07:00-23:00",
  "status": "open",
  "min_price": "8.00",
  "created_at": "2026-05-06T10:00:00",
  "updated_at": "2026-05-06T10:00:00",
  "seat_count": 0,
  "available_seat_count": 0
}
```

**错误码：**
- 401: 管理员凭证无效
- 422: 参数校验失败

---

### GET /api/v1/admin/rooms

获取自习室分页列表，支持状态筛选。

**认证：** X-Admin-Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| page_size | integer | 10 | 每页数量（最大 50） |
| status | string | - | 状态筛选：open / closed |

**响应 200：**
```json
{
  "items": [
    {
      "id": 1,
      "name": "安静自习室·油城店",
      "description": "宽敞明亮的沉浸式自习空间",
      "cover_image": "https://example.com/room.jpg",
      "address": "茂名市茂南区油城三路88号",
      "business_hours": "07:00-23:00",
      "status": "open",
      "min_price": "8.00",
      "created_at": "2026-05-06T10:00:00",
      "updated_at": "2026-05-06T10:00:00",
      "seat_count": 50,
      "available_seat_count": 48
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```

**错误码：**
- 401: 管理员凭证无效

---

### GET /api/v1/admin/rooms/{room_id}

获取自习室详情。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**响应 200：** 同创建自习室的响应格式。

**错误码：**
- 401: 管理员凭证无效
- 404: 自习室不存在

---

### PUT /api/v1/admin/rooms/{room_id}

更新自习室。仅更新请求体中传递的字段。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**请求体（所有字段均可选）：**
```json
{
  "name": "更新后的名称",
  "address": "更新后的地址",
  "description": "更新后的描述",
  "cover_image": "https://example.com/new-cover.jpg",
  "business_hours": "08:00-22:00",
  "min_price": 10.00
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| name | string | 自习室名称，最大100字 |
| address | string | 地址，最大255字 |
| description | string \| null | 描述，最大1000字 |
| cover_image | string \| null | 封面图 URL，最大512字符 |
| business_hours | string \| null | 营业时间，最大50字 |
| min_price | decimal | 最低价格（单位：元） |

**响应 200：** 返回更新后的自习室对象（同 GET 单个自习室）。

**错误码：**
- 401: 管理员凭证无效
- 404: 自习室不存在
- 422: 参数校验失败

---

### DELETE /api/v1/admin/rooms/{room_id}

删除自习室。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**响应 204：** 无响应体。

**错误码：**
- 401: 管理员凭证无效
- 404: 自习室不存在
- 409: 该自习室存在活跃预约，无法删除

---

### PATCH /api/v1/admin/rooms/{room_id}/status/

切换自习室营业/关闭状态。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**请求体：**
```json
{
  "status": "closed"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 目标状态：open / closed |

**响应 200：** 返回更新后的自习室对象（同 GET 单个自习室）。

**错误码：**
- 401: 管理员凭证无效
- 404: 自习室不存在

---

## 十、管理端 - 座位管理

### POST /api/v1/admin/rooms/{room_id}/seats

创建座位。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**请求体：**
```json
{
  "seat_number": "A1-01",
  "zone": "quiet",
  "position": "靠窗",
  "floor": 3,
  "price_per_hour": 6.00,
  "row": 1,
  "col": 1
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| seat_number | string | 是 | 座位编号，最大10字 |
| zone | string | 是 | 区域：quiet / keyboard / vip |
| position | string | 否 | 位置描述，如 "靠窗"、"中间"，最大20字 |
| floor | integer | 否 | 楼层，默认 3，最小 1 |
| price_per_hour | decimal | 是 | 每小时价格（单位：元） |
| row | integer | 是 | 座位图行号 |
| col | integer | 是 | 座位图列号 |

**响应 201：**
```json
{
  "id": 1,
  "room_id": 1,
  "seat_number": "A1-01",
  "zone": "quiet",
  "position": "靠窗",
  "floor": 3,
  "price_per_hour": "6.00",
  "status": "available",
  "row": 1,
  "col": 1,
  "created_at": "2026-05-06T10:00:00",
  "updated_at": "2026-05-06T10:00:00",
  "room_name": "安静自习室·油城店"
}
```

**错误码：**
- 401: 管理员凭证无效
- 404: 自习室不存在
- 409: 该房间已存在相同编号的座位
- 422: 参数校验失败

---

### POST /api/v1/admin/rooms/{room_id}/seats/bulk/

批量创建座位。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**请求体：**
```json
{
  "seats": [
    {
      "zone": "quiet",
      "rows": 5,
      "cols": 8,
      "prefix": "A",
      "start_number": 1,
      "price_per_hour": 6.00,
      "floor": 3
    },
    {
      "zone": "keyboard",
      "rows": 3,
      "cols": 6,
      "prefix": "B",
      "start_number": 1,
      "price_per_hour": 8.00,
      "floor": 3
    }
  ]
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| seats | array | 是 | 区域配置数组 |
| seats[].zone | string | 是 | 区域：quiet / keyboard / vip |
| seats[].rows | integer | 是 | 行数 |
| seats[].cols | integer | 是 | 列数 |
| seats[].prefix | string | 是 | 编号前缀，最大5字 |
| seats[].start_number | integer | 否 | 起始编号，默认 1 |
| seats[].price_per_hour | decimal | 是 | 每小时价格（单位：元） |
| seats[].floor | integer | 否 | 楼层，默认 3 |

座位编号生成规则：`{prefix}-{编号}`，编号从 start_number 开始自动递增。例如：prefix="A"，start_number=1，rows=2，cols=2 生成 A-01, A-02, A-03, A-04。

**响应 201：**
```json
{
  "created": 58
}
```

**错误码：**
- 401: 管理员凭证无效
- 404: 自习室不存在
- 409: 以下座位编号已存在：A-05, B-03
- 422: 参数校验失败

---

### GET /api/v1/admin/rooms/{room_id}/seats

获取指定自习室的座位列表，支持区域和状态筛选。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| room_id | integer | 自习室 ID |

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| zone | string | - | 区域筛选：quiet / keyboard / vip |
| status | string | - | 状态筛选：available / maintenance |

**响应 200：**
```json
[
  {
    "id": 1,
    "room_id": 1,
    "seat_number": "A1-01",
    "zone": "quiet",
    "position": "靠窗",
    "floor": 3,
    "price_per_hour": "6.00",
    "status": "available",
    "row": 1,
    "col": 1,
    "created_at": "2026-05-06T10:00:00",
    "updated_at": "2026-05-06T10:00:00",
    "room_name": "安静自习室·油城店"
  }
]
```

**错误码：**
- 401: 管理员凭证无效
- 404: 自习室不存在

---

### GET /api/v1/admin/seats/{seat_id}

获取座位详情。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| seat_id | integer | 座位 ID |

**响应 200：** 同创建座位的响应格式。

**错误码：**
- 401: 管理员凭证无效
- 404: 座位不存在

---

### PUT /api/v1/admin/seats/{seat_id}

更新座位。仅更新请求体中传递的字段。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| seat_id | integer | 座位 ID |

**请求体（所有字段均可选）：**
```json
{
  "seat_number": "A1-02",
  "zone": "vip",
  "position": "独立",
  "floor": 4,
  "price_per_hour": 10.00,
  "row": 2,
  "col": 2
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| seat_number | string \| null | 座位编号，最大10字 |
| zone | string \| null | 区域：quiet / keyboard / vip |
| position | string \| null | 位置描述，最大20字 |
| floor | integer \| null | 楼层，最小 1 |
| price_per_hour | decimal \| null | 每小时价格（单位：元） |
| row | integer \| null | 座位图行号 |
| col | integer \| null | 座位图列号 |

**响应 200：** 返回更新后的座位对象（同 GET 单个座位）。

**错误码：**
- 401: 管理员凭证无效
- 404: 座位不存在
- 409: 该房间已存在相同编号的座位
- 422: 参数校验失败

---

### DELETE /api/v1/admin/seats/{seat_id}

删除座位。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| seat_id | integer | 座位 ID |

**响应 204：** 无响应体。

**错误码：**
- 401: 管理员凭证无效
- 404: 座位不存在
- 409: 该座位存在活跃预约，无法删除

---

### PATCH /api/v1/admin/seats/{seat_id}/status/

切换座位可用/维护状态。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| seat_id | integer | 座位 ID |

**请求体：**
```json
{
  "status": "maintenance"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| status | string | 是 | 目标状态：available / maintenance |

**响应 200：** 返回更新后的座位对象（同 GET 单个座位）。

**错误码：**
- 401: 管理员凭证无效
- 404: 座位不存在

---

## 十一、Booking Verification / 到店核销

### POST /api/v1/booking-verifications/token

为当前登录用户的可核销预约签发 5 分钟有效的动态核销 token。

**认证：** Bearer Token

**核销窗口：** 仅为当天预约签发；允许预约开始前 30 分钟至 `end_time` 之间核销，未来预约和已过结束时间的预约不会签发核销码。

**Token 类型：** token 使用后端 JWT 签名，包含 `purpose=booking_verification`，不能使用普通登录 JWT 替代。

**配置：** 必须设置 `FRONTEND_BASE_URL` 为公开 H5 域名，例如 `https://booking.example.com`。服务端只使用该配置拼接二维码链接，不接受用户请求传入外部域名。未配置时接口返回 500，避免生成无法被微信扫一扫打开的相对 URL。`BOOKING_TIMEZONE` 控制核销业务时区，默认 `Asia/Shanghai`。

**响应 200：**
```json
{
  "token": "eyJhbGciOiJIUzI1NiIs...",
  "expires_at": "2026-05-09T08:35:00Z",
  "verify_url": "https://booking.example.com/#/pages/verify-booking/index?token=eyJhbGciOiJIUzI1NiIs...",
  "booking": {
    "id": 101,
    "user_id": "11111111-1111-1111-1111-111111111111",
    "user_nickname": "Study User",
    "user_phone": "13800138000",
    "room_id": 1,
    "room_name": "安静自习室·油城店",
    "room_address": "茂名市茂南区油城三路88号",
    "seat_id": 12,
    "seat_number": "A-01",
    "seat_zone": "quiet",
    "seat_position": "window",
    "date": "2026-05-10",
    "start_time": "09:00:00",
    "end_time": "12:00:00",
    "total_price": "45.00",
    "status": "in_progress",
    "can_verify": true
  }
}
```

**错误码：**
- 401: 未认证
- 404: 暂无可核销预约
- 500: 核销码服务未配置

---

### GET /api/v1/booking-verifications/{token}

管理员或工作人员解析核销 token，查看预约核销信息。

**认证：** X-Admin-Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | 用户端二维码中的动态核销 token |

**响应 200：**
```json
{
  "booking": {
    "id": 101,
    "user_id": "11111111-1111-1111-1111-111111111111",
    "user_nickname": "Study User",
    "user_phone": "13800138000",
    "room_id": 1,
    "room_name": "安静自习室·油城店",
    "room_address": "茂名市茂南区油城三路88号",
    "seat_id": 12,
    "seat_number": "A-01",
    "seat_zone": "quiet",
    "seat_position": "window",
    "date": "2026-05-10",
    "start_time": "09:00:00",
    "end_time": "12:00:00",
    "total_price": "45.00",
    "status": "in_progress",
    "can_verify": true
  }
}
```

**错误码：**
- 401: 无管理员权限
- 400: 无效 token
- 404: 暂无可核销预约
- 410: token 已过期

---

### POST /api/v1/booking-verifications/{token}/confirm

管理员或工作人员确认到店核销。可核销预约为 `status='in_progress'`，或 `status='pending_start'` 且 `payment_status='paid'`；核销成功后未过 `date + end_time` 置 `in_progress`，已过则置 `completed`。

**认证：** X-Admin-Token

**核销窗口：** 服务端会再次校验当天预约、开始前 30 分钟至 `end_time` 的时间窗口；确认核销使用条件更新（原子转换），仅命中上述可核销状态的预约，避免并发重复核销。

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| token | string | 用户端二维码中的动态核销 token |

**响应 200：**
```json
{
  "booking": {
    "id": 101,
    "user_id": "11111111-1111-1111-1111-111111111111",
    "user_nickname": "Study User",
    "user_phone": "13800138000",
    "room_id": 1,
    "room_name": "安静自习室·油城店",
    "room_address": "茂名市茂南区油城三路88号",
    "seat_id": 12,
    "seat_number": "A-01",
    "seat_zone": "quiet",
    "seat_position": "window",
    "date": "2026-05-10",
    "start_time": "09:00:00",
    "end_time": "12:00:00",
    "total_price": "45.00",
    "status": "completed",
    "can_verify": false
  }
}
```

**错误码：**
- 401: 无管理员权限
- 400: 无效 token
- 404: 暂无可核销预约
- 409: 已核销或不可核销状态
- 410: token 已过期

---

## 十二、数据模型

### RoomAdminResponse

管理端自习室响应对象。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 自习室 ID |
| name | string | 名称 |
| description | string \| null | 描述 |
| cover_image | string \| null | 封面图 URL |
| address | string | 地址 |
| business_hours | string \| null | 营业时间 |
| status | string | 状态：open / closed |
| min_price | decimal | 最低价格（单位：元） |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| seat_count | integer | 座位总数 |
| available_seat_count | integer | 可用座位数 |

### SeatAdminResponse

管理端座位响应对象。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 座位 ID |
| room_id | integer | 所属自习室 ID |
| seat_number | string | 座位编号 |
| zone | string | 区域：quiet / keyboard / vip |
| position | string \| null | 位置描述 |
| floor | integer | 楼层 |
| price_per_hour | decimal | 每小时价格（单位：元） |
| status | string | 状态：available / maintenance |
| row | integer | 座位图行号 |
| col | integer | 座位图列号 |
| created_at | datetime | 创建时间 |
| updated_at | datetime | 更新时间 |
| room_name | string | 所属自习室名称 |

---

## 十三、管理端 - 用户管理

统一管理 App 用户和 Admin 用户。所有接口需要管理员认证。

### GET /api/v1/admin/users

获取用户分页列表。

**认证：** Bearer Token 或 X-Admin-Token（需 `system:user:view` 权限）

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| user_type | string | - | 用户类型筛选：app / admin |
| keyword | string | - | 搜索关键词（匹配手机号/昵称/用户名） |
| status | string | - | 状态筛选：active / banned / disabled |
| page | integer | 1 | 页码 |
| page_size | integer | 20 | 每页数量（最大 100） |

**响应 200：**
```json
{
  "items": [
    {
      "id": "uuid-string",
      "phone": "13800138000",
      "nickname": "学习达人",
      "user_type": "app",
      "status": "active",
      "avatar": null,
      "created_at": "2026-04-17T00:00:00",
      "roles": [{ "id": 1, "name": "注册用户", "code": "app_register_user" }],
      "booking_count": 5,
      "coupon_count": 2
    }
  ],
  "total": 100,
  "page": 1,
  "page_size": 20
}
```

**错误码：**
- 401: 未认证
- 403: 无 `system:user:view` 权限

---

### POST /api/v1/admin/users

创建用户。

**认证：** 需 `system:user:create` 权限

**请求体：**
```json
{
  "user_type": "app",
  "phone": "13800138000",
  "password": "Abc123456",
  "nickname": "新用户"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| user_type | string | 是 | 用户类型：app / admin |
| phone | string | 条件必填 | 手机号（app 用户必填），需匹配 `^1[3-9]\d{9}$` |
| username | string | 条件必填 | 用户名（admin 用户必填） |
| password | string | 是 | 密码，6-128 位 |
| nickname | string | 否 | 昵称 |

App 用户创建后自动分配 `app_register_user` 角色。

**响应 201：** 返回 `AdminUserDetail` 对象。

**错误码：**
- 400: app 用户需要手机号 / admin 用户需要用户名
- 409: 该手机号已注册 / 该用户名已存在
- 422: 参数校验失败

---

### GET /api/v1/admin/users/{user_id}

获取用户详情。

**认证：** 需 `system:user:view` 权限

**响应 200：**
```json
{
  "id": "uuid-string",
  "phone": "13800138000",
  "nickname": "学习达人",
  "user_type": "app",
  "username": null,
  "email": null,
  "mobile": null,
  "avatar": null,
  "status": "active",
  "balance": 0,
  "is_super_admin": false,
  "wechat_openid": null,
  "invite_code": null,
  "created_at": "2026-04-17T00:00:00",
  "updated_at": "2026-04-17T00:00:00",
  "roles": [{ "id": 1, "name": "注册用户", "code": "app_register_user" }],
  "booking_count": 5,
  "coupon_count": 2
}
```

**错误码：**
- 401: 未认证
- 403: 无权限
- 404: 用户不存在

---

### PUT /api/v1/admin/users/{user_id}

更新用户信息。

**认证：** 需 `system:user:update` 权限

**请求体（所有字段均可选）：**
```json
{
  "nickname": "新昵称",
  "email": "user@example.com",
  "role_ids": [1, 2]
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| nickname | string | 昵称 |
| email | string | 邮箱 |
| mobile | string | 手机号 |
| avatar | string | 头像 URL |
| balance | decimal | 余额 |
| role_ids | integer[] | 角色ID列表 |

**响应 200：** 返回更新后的 `AdminUserDetail`。

**错误码：**
- 401: 未认证
- 403: 无权限
- 404: 用户不存在

---

### DELETE /api/v1/admin/users/{user_id}

删除用户及其角色关联。

**认证：** 需 `system:user:delete` 权限

**响应 204：** 无响应体。

**错误码：**
- 401: 未认证
- 403: 无权限
- 404: 用户不存在

---

### PUT /api/v1/admin/users/{user_id}/reset-password

重置用户密码。

**认证：** 需 `system:user:reset-password` 权限

**请求体：**
```json
{
  "new_password": "NewPass123"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| new_password | string | 是 | 新密码，6-128 位 |

**响应 200：** 返回更新后的 `AdminUserDetail`。

**错误码：**
- 401: 未认证
- 403: 无权限
- 404: 用户不存在
- 422: 密码长度不合法

---

### PUT /api/v1/admin/users/{user_id}/status

切换用户状态。

**认证：** 需 `system:user:status` 权限

**请求体：**
```json
{
  "target_status": "banned"
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| target_status | string | 是 | 目标状态：active / banned / disabled |

**响应 200：** 返回更新后的 `AdminUserDetail`。

**错误码：**
- 400: 无效的状态值
- 401: 未认证
- 403: 无权限
- 404: 用户不存在
