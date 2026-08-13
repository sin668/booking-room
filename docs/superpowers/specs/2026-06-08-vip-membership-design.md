# VIP 会员开通功能设计

日期：2026-06-08

## 概述

在 br-app "我的"页面提供 VIP 会员开通入口。用户单次充值 ≥ 100 元即可成为 VIP（永久有效），首次开通时自动赠送一张有效期 1 个月的 VIP 专属 8 折折扣券。VIP 用户可使用 `scope=vip_only` 的专享卡券。

## 数据模型变更

### User 模型

新增字段：

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| `membership_level` | String(20) | `"none"` | 会员等级枚举：`none`/`vip`/`svip`（预留） |

- 需要 Alembic 迁移
- 非空，默认 `none`
- SVIP 为预留值，本次不实现开通逻辑

### UserCoupon.source_type 扩展

新增值：

| 值 | 说明 |
|----|------|
| `activity` | 活动领取（已有） |
| `vip_welcome` | VIP 开通赠送（新增） |

### VIP 欢迎券 Coupon 模板

首次升级 VIP 时自动创建：

| 字段 | 值 |
|------|-----|
| `name` | `"VIP专属8折券-{用户昵称}"` |
| `type` | `percentage_off` |
| `discount_percent` | `80` |
| `min_order_amount` | `0` |
| `scope` | `vip_only` |
| `valid_from` | 开通时间（now） |
| `expires_at` | 开通时间 + 30 天 |
| `is_active` | `true` |

每个 VIP 用户独享各自的券实例（非公共模板）。

## 后端设计

### VIP 升级触发机制

**方案**：在充值确认回调中内嵌 VIP 升级逻辑（方案 A）

**触发点**：`WalletService.confirm_payment()` 充值确认成功后

**升级判断条件（需同时满足）：**
1. 本次充值金额 `transaction.amount >= 100`
2. 用户当前 `membership_level == "none"`

**执行流程（同一 DB 事务）：**
1. 更新 `User.membership_level` 为 `"vip"`
2. 创建 VIP 欢迎券 Coupon 记录
3. 创建 UserCoupon 记录（`source_type=vip_welcome`）
4. 返回增强的 RechargeResponse：新增 `membership_upgraded: bool` 和 `vip_coupon_id: int | None`

**不升级场景：**
- 用户已是 VIP/SVIP → 正常充值
- 充值金额 < 100 → 正常充值
- `membership_level` 为 `svip`（预留）→ 不降级

### VIP 卡券查询过滤

抽取 `_check_scope(user, coupon)` 统一方法，处理所有 scope 校验：

| scope 值 | 校验规则 |
|----------|----------|
| `all` | 所有用户可用 |
| `first_booking` | 无 confirmed/completed 预约历史 |
| `vip_only` | `membership_level` 为 `vip` 或 `svip` |
| `<seat_zone>` | 匹配座位区域 |

**用户卡券列表**（`GET /api/v1/coupons`）：
- `status=available`：过滤掉非 VIP 用户的 `vip_only` 券
- `status=expired`：不受 VIP 限制影响

**预约可用卡券**（`GET /api/v1/coupons/available-for-booking`）：
- 仅 VIP/SVIP 用户返回 `vip_only` 券

## 前端 br-app 设计

### 页面流转

```
我的页面（会员卡片）→ VIP权益介绍页 → 充值页 → 充值成功 → 升级提示 → 返回我的页面
```

### 我的页面（profile/index.vue）

**会员卡片状态：**

| 用户状态 | 卡片内容 |
|----------|----------|
| 非 VIP | 标题"升级超级会员"，说明"享8折优惠+专属座位+优先预约"，按钮"立即开通" |
| VIP | 标题"超级会员"，显示 VIP 标识，按钮隐藏或变为"已是会员"（禁用态） |

- 非 VIP：点击"立即开通"跳转 `/pages/membership/index`
- VIP：点击不跳转

### VIP 权益介绍页（新增 pages/membership/index.vue）

- 展示 VIP 权益列表：8折优惠、专属座位、优先预约
- 底部按钮"立即开通 - 充值100元起"
- 点击跳转 `/pages/recharge/index?amount=100&source=vip`

### 充值页（修改 pages/recharge/index.vue）

- 检测 URL 参数 `source=vip` 时，预填充金额 100 元
- 充值成功后检查 RechargeResponse 的 `membership_upgraded` 字段
- 若为 true，弹出"恭喜成为超级会员"提示（含赠券信息）
- 用户确认后返回我的页面

### VIP 欢迎券

- 自动出现在卡券包（`/pages/coupon/index`）的"可使用"标签下
- 名称："VIP专属8折券"
- 类型标签："折扣券"
- 有效期：开通日起 1 个月

## 管理后台 br-admin

- 用户列表新增 `membership_level` 列（标签展示）
- 卡券管理列表适用范围列支持"VIP专享"显示
- 创建卡券时适用范围下拉新增"VIP专享"选项

## 回滚方案

1. Alembic 迁移回滚移除 `membership_level` 列
2. 删除 VIP 权益介绍页面
3. 从充值确认流程中移除 VIP 升级逻辑
4. 从充值页移除 VIP 参数处理
5. 恢复我的页面会员卡片为原始状态
