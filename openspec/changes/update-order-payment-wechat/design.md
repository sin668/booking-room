## Context

当前订单确认页（`pages/booking/confirm.vue`）硬编码 `payment_method: 'wallet'`，仅支持账户余额支付。用户需先通过钱包充值页（已接入微信支付）充值，再用余额预约，流程冗长。

现有微信支付基础设施：
- `wechat_pay_client.py`：封装微信支付 JSAPI 下单、查询、证书管理
- `wallet_service.py`：充值订单 + 微信回调处理
- `POST /api/v1/wallet/recharge`：创建充值订单，返回 JSAPI `payment_params`
- `POST /api/v1/wallet/wechat/notify`：微信异步通知，回调入账

约束：微信小程序只能通过 `uni.requestPayment` 调用微信支付，必须由后端预下单获取 `prepay_id`。

## Goals / Non-Goals

**Goals:**
- 订单确认页整体 UI 对齐 `prototype/order-confirm.html` 原型，包括 5 个区域改造
- 门店信息显示楼层（替代地址）、卡券区改为简洁行样式、支付方式 radio 选择、成功弹窗简化、视觉风格对齐
- 后端 booking API 支持 `balance` 和 `wechat` 两种支付方式
- 微信支付订单支付成功后通过回调自动确认预约
- 复用现有 `wechat_pay_client.py` 基础设施

**Non-Goals:**
- 不接入支付宝等其他支付方式
- 不改变钱包充值流程
- 不实现订单退款功能
- 不改变管理后台相关功能

## Decisions

### D1: Booking 模型增加支付字段

`bookings` 表新增：`payment_method`（VARCHAR(20)，默认 'balance'）、`payment_status`（VARCHAR(20)，默认 'paid'）、`payment_provider`（VARCHAR(20)，可空）、`prepay_id`（VARCHAR(64)，可空）、`transaction_id`（VARCHAR(64)，可空）、`paid_at`（TIMESTAMP，可空）。

**Why**: 需要区分余额支付（即时）和微信支付（异步回调），现有 booking 模型无支付状态字段。余额支付时 `payment_status` 直接为 'paid'，微信支付时先为 'pending'，回调成功后更新为 'paid'。

**Alternative**: 在 `wallet_transactions` 表中关联 booking 支付记录 → 但混合充值和订单支付语义不清，且需额外 JOIN 查询。

### D2: 余额支付保持即时扣款，微信支付为两阶段

余额支付：创建 booking 时原子扣款，`payment_status='paid'`，逻辑与当前一致。

微信支付：创建 booking 时仅占座（状态 `confirmed`，`payment_status='pending'`），返回 JSAPI 支付参数。前端唤起微信支付 → 微信回调成功 → `payment_status='paid'`，`paid_at` 更新。若 15 分钟内未支付，通过定时任务或下次访问时检测超时自动取消并释放座位。

**Why**: 余额支付无需第三方参与，即时完成。微信支付依赖异步回调，需要占座防冲突但允许支付超时。

**Alternative**: 微信支付先不占座，回调成功再创建 booking → 可能出现支付成功但座位已被抢的情况。

### D3: 复用 wechat_pay_client.py 创建订单支付

新增 `booking_payment_service.py`，复用 `wechat_pay_client.create_order()` 方法，传入 booking 相关参数（description 含座位/门店信息，out_trade_no 格式 `BK-{booking_id}`）。回调处理参考充值回调，但更新 booking 而非 wallet。

**Why**: 现有 `wechat_pay_client` 已封装签名、证书、HTTP 调用，直接复用减少代码量。订单号前缀区分充值（`RC-`）和预约（`BK-`）。

### D4: 前端支付方式默认选择余额

默认选中"账户余额"，余额不足时 UI 提示但仍允许切换到"微信支付"。

**Why**: 余额支付体验更好（即时确认），符合原型图默认状态。余额不足时引导切换而非强制。

### D5: 新增 booking 微信支付回调 endpoint

`POST /api/v1/bookings/wechat/notify`，与充值回调 `POST /api/v1/wallet/wechat/notify` 结构一致，处理逻辑不同（更新 booking 而非 wallet）。

**Why**: 单独 endpoint 保持职责清晰，订单号前缀区分来源，避免回调路由混乱。

### D6: 卡券区改为原型简洁行样式

现有内联展开的卡券 radio 列表替换为原型中的简洁行：一行显示"优惠券"标签 + 已选卡券折扣金额 + 右箭头。点击后弹出底部弹窗（bottom sheet）展示可用卡券列表，用户在弹窗中选择。选择后简洁行显示"-¥X.XX"，未选择时显示箭头引导点击。

**Why**: 匹配原型设计，减少页面视觉复杂度，同时保留卡券选择功能。弹窗选择比内联列表更适合小屏设备。

### D7: 门店信息显示楼层替代地址

门店信息卡片中，将第二行从 `roomAddress`（完整地址）改为 `floor`（如"3楼"），匹配原型设计。

**Why**: 原型中门店卡片仅显示楼层，地址信息在门店详情页已完整展示，确认页保持简洁。

### D8: 成功弹窗简化为 4 行摘要

现有成功弹窗展示 7 个字段（订单编号、门店、座位、时间、原价、优惠抵扣、实付金额），简化为原型中的 4 行：门店、座位、时间、支付金额。

**Why**: 匹配原型设计，支付成功后用户关注核心信息即可，原价和抵扣金额在支付前已确认。

## Risks / Trade-offs

**[Risk] 微信支付超时占座** → 微信支付后 15 分钟内未完成支付，座位被锁定无法预约。**Mitigation**: 后端定时任务扫描 `payment_status='pending'` 且超时的 booking，自动取消并释放座位。

**[Risk] 并发占座冲突** → 微信支付模式下，占座到回调期间其他用户可能冲突。**Mitigation**: 与现有 booking 创建逻辑一致，使用数据库唯一约束 + 事务保证。

**[Risk] 回调丢失** → 微信支付成功但回调未到达。**Mitigation**: 前端支付成功后轮询 booking 状态，超时提示用户。后端提供查询充值订单类似的 `GET /api/v1/bookings/{id}/payment-status` 接口。

## Payment Flow Sequence

```
用户选择"余额支付":
  前端 → POST /api/v1/bookings/ (payment_method=balance)
  后端 → 扣余额 + 创建 booking(payment_status=paid) → 201
  前端 → 显示成功弹窗

用户选择"微信支付":
  前端 → POST /api/v1/bookings/ (payment_method=wechat)
  后端 → 创建 booking(payment_status=pending) + 调用微信JSAPI下单 → 201 + payment_params
  前端 → uni.requestPayment(payment_params)
  微信 → 用户完成支付 → 微信回调 POST /api/v1/bookings/wechat/notify
  后端 → 更新 booking(payment_status=paid, paid_at=now, transaction_id=X) → 释放座位锁定
  前端 → 轮询 GET /api/v1/bookings/{id}/payment-status 直到 paid → 显示成功弹窗
```
