# API 文档

Base URL: `http://localhost:8000`

## 认证

用户端接口使用 Bearer Token (JWT)，通过 `Authorization` header 传递。
管理端接口使用固定 Token，通过 `X-Admin-Token` header 传递。

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

## 二、用户信息

### GET /api/v1/users/me

获取当前登录用户信息。与 `/auth/me` 功能相同。

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
  "nickname": "学习达人",
  "status": "active",
  "wechat_openid": null,
  "invite_code": null,
  "created_at": "2026-04-17T00:00:00"
}
```

**错误码：**
- 401: 未认证
- 404: 用户不存在

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
| city_id | integer | - | 城市 ID；不传时返回全部城市的自习室 |

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
      "cover_image": "https://example.com/activity.jpg",
      "participant_count": 326,
      "sort_order": 1,
      "is_active": true,
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
  "cover_image": "https://example.com/activity.jpg",
  "participant_count": 0,
  "sort_order": 1,
  "is_active": true
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| title | string | 是 | 活动标题，最大100字 |
| description | string | 否 | 活动描述，最大500字 |
| cover_image | string | 否 | 封面图 URL，最大512字符 |
| participant_count | integer | 否 | 参与人数，默认 0，最小 0 |
| sort_order | integer | 否 | 排序值，默认 0 |
| is_active | boolean | 否 | 是否上架，默认 true |

**响应 201：**
```json
{
  "id": 1,
  "title": "沉浸式学习挑战赛",
  "description": "累计学习24小时赢好礼",
  "cover_image": "https://example.com/activity.jpg",
  "participant_count": 0,
  "sort_order": 1,
  "is_active": true,
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
  "cover_image": "https://example.com/activity.jpg",
  "participant_count": 326,
  "sort_order": 1,
  "is_active": true,
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
  "cover_image": "https://example.com/new-cover.jpg",
  "participant_count": 400,
  "sort_order": 2,
  "is_active": false
}
```

| 字段 | 类型 | 说明 |
|------|------|------|
| title | string | 活动标题，最大100字 |
| description | string \| null | 活动描述，最大500字 |
| cover_image | string \| null | 封面图 URL，最大512字符 |
| participant_count | integer | 参与人数，最小 0 |
| sort_order | integer | 排序值 |
| is_active | boolean | 是否上架 |

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

## 五、管理端 - 文件上传

### POST /admin/upload

上传图片文件。

**认证：** X-Admin-Token

**请求：** `multipart/form-data`

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| file | File | 是 | 图片文件 |

**限制：**
- 支持格式：`.jpg`、`.jpeg`、`.png`、`.gif`、`.webp`
- 最大文件大小：5MB

**响应 200：**
```json
{
  "url": "/uploads/2026/04/24/a1b2c3d4e5f6.png"
}
```

**错误码：**
- 401: 管理员凭证无效
- 422: 缺少文件 / 仅支持图片文件 / 文件大小不能超过5MB

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
    "seat_zone": null
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
| scope | string | all / first_booking / seat_zone |
| status | string | available / used / expired |
| discount_amount | decimal \| null | 固定抵扣金额 |
| discount_percent | integer \| null | 折扣比例，80 表示 8 折 |
| min_order_amount | decimal | 使用门槛 |
| valid_from | datetime | 生效时间 |
| expires_at | datetime | 过期时间 |
| used_at | datetime \| null | 使用时间 |
| used_booking_id | integer \| null | 使用该券的预约 ID |
| seat_zone | string \| null | 指定座位类型范围 |

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
      "payable_amount": "42.00"
    }
  ]
}
```

不可用卡券会被过滤，包括：不属于当前用户、已使用、未生效、已过期、模板停用、未达到满减门槛、不满足首次预约限制、座位类型不匹配。

**错误码：**
- 401: 未认证
- 404: 座位不存在
- 422: 查询参数格式无效

---

## 八、钱包

所有钱包接口需要通过 `Authorization` header 传递 Bearer Token。

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
  "balance_after": null
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
  "balance_after": "386.00"
}
```

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
  "coupon_id": 12
}
```

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| seat_id | integer | 是 | 座位 ID |
| date | string | 是 | 预约日期，格式 YYYY-MM-DD |
| start_time | string | 是 | 开始时间，格式 HH:MM |
| end_time | string | 是 | 结束时间，格式 HH:MM |
| coupon_id | integer \| null | 否 | 用户卡券 ID，每个订单最多使用 1 张卡券 |

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
  "status": "confirmed",
  "original_price": "18.00",
  "discount_amount": "3.00",
  "total_price": "15.00",
  "coupon_id": 12,
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

**错误码：**
- 401: 未认证
- 404: 座位不存在
- 409: 该座位该时段已被预约
- 422: 结束时间必须晚于开始时间
- 400: 该座位正在维护中
- 400: 卡券不可用，请重新选择（不存在、不属于当前用户、已使用、未生效、已过期、停用、门槛不足或适用范围不匹配）

---

### GET /api/v1/bookings/

获取当前用户的预约列表。

**认证：** Bearer Token

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码（从 1 开始） |
| page_size | integer | 10 | 每页数量（最大 50） |
| status | string | - | 状态筛选：confirmed / cancelled / completed |

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
      "status": "confirmed",
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

**响应 200：** 同创建预约的响应格式。

**错误码：**
- 401: 未认证
- 404: 预约不存在 / 无权查看

---

### POST /api/v1/bookings/{booking_id}/cancel

取消预约。仅 `confirmed` 状态的预约可取消。若该预约使用了卡券，取消成功后对应用户卡券恢复为 `available`，并清空 `used_booking_id` 和 `used_at`。

**认证：** Bearer Token

**路径参数：**

| 字段 | 类型 | 说明 |
|------|------|------|
| booking_id | integer | 预约 ID |

**响应 200：** 返回更新后的预约对象，`status` 变为 `"cancelled"`。若订单使用过卡券，该卡券已恢复为可使用状态。

**错误码：**
- 401: 未认证
- 400: 该预约已取消（非 confirmed 状态）
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
  "status": "confirmed",
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
- `status` (optional, string): Filter by status — `confirmed`, `cancelled`, `completed`

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

### POST /api/v1/bookings/{booking_id}/cancel/

Cancel a confirmed booking. Requires authentication.

Response (200): Returns the updated booking with `status: "cancelled"`.

Error Responses:
- `404` — Booking not found
- `400` — Booking already cancelled

---

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
    "status": "confirmed",
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
    "status": "confirmed",
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

管理员或工作人员确认到店核销。只有 `confirmed` 预约可更新为 `completed`。

**认证：** X-Admin-Token

**核销窗口：** 服务端会再次校验当天预约、开始前 30 分钟至 `end_time` 的时间窗口；确认核销使用条件更新，只有 `status=confirmed` 的预约能原子转换为 `completed`。

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
