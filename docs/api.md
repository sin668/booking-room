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

---

## 首页相关接口

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
| cover_image | string \| null | 封面图 URL |
| participant_count | integer | 参与人数 |

---

### GET /api/v1/rooms

获取自习室分页列表。无需认证。

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| page_size | integer | 10 | 每页数量（最大 50） |

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
      "min_price": "8.00"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```

仅返回 `status=open` 的自习室。

| 字段 | 类型 | 说明 |
|------|------|------|
| id | integer | 自习室 ID |
| name | string | 名称 |
| description | string \| null | 描述 |
| cover_image | string \| null | 封面图 URL |
| address | string | 地址 |
| business_hours | string \| null | 营业时间（如 "08:00-22:00"） |
| status | string | 状态：open / closed |
| min_price | decimal | 最低价格（单位：元） |

**错误码：**
- 422: page_size 超过最大值 50
