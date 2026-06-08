# vip-membership Specification

## Purpose
TBD - created by archiving change coupon-management-admin. Update Purpose after archive.
## Requirements
### Requirement: 用户会员等级字段
系统 SHALL 在 User 模型中提供 `membership_level` 字符串枚举字段，值为 `none`（默认）、`vip`、`svip`（预留）。新增用户默认为 `none`。

#### Scenario: 新用户默认等级
- **GIVEN** 系统创建新用户
- **WHEN** 用户注册完成
- **THEN** 用户 `membership_level` 为 `none`

### Requirement: 充值触发 VIP 自动升级
系统 SHALL 在充值支付确认成功后自动检测并执行 VIP 升级。当充值金额 ≥ 100 且用户 `membership_level` 为 `none` 时，系统 MUST 在同一事务中将用户 `membership_level` 更新为 `vip`。

#### Scenario: 充值100元触发VIP升级
- **GIVEN** 用户 `membership_level` 为 `none`
- **WHEN** 用户完成一笔金额为 100 元的充值且支付确认成功
- **THEN** 用户 `membership_level` 更新为 `vip`
- **AND** 充值响应包含 `membership_upgraded=true`

#### Scenario: 充值金额不足不触发升级
- **GIVEN** 用户 `membership_level` 为 `none`
- **WHEN** 用户完成一笔金额为 50 元的充值且支付确认成功
- **THEN** 用户 `membership_level` 保持 `none`
- **AND** 充值响应包含 `membership_upgraded=false`

#### Scenario: 已是VIP充值不重复升级
- **GIVEN** 用户 `membership_level` 为 `vip`
- **WHEN** 用户完成一笔金额为 100 元的充值且支付确认成功
- **THEN** 用户 `membership_level` 保持 `vip`
- **AND** 充值响应包含 `membership_upgraded=false`

#### Scenario: SVIP用户充值不降级
- **GIVEN** 用户 `membership_level` 为 `svip`
- **WHEN** 用户完成充值且支付确认成功
- **THEN** 用户 `membership_level` 保持 `svip`

### Requirement: 首次开通 VIP 赠送欢迎券
系统 SHALL 在用户首次升级为 VIP 时自动赠送一张 VIP 专属 8 折折扣券。系统 MUST 创建 Coupon 模板记录（`scope=vip_only`、`type=percentage_off`、`discount_percent=80`、`valid_from` 为当前时间、`expires_at` 为当前时间 + 30 天）和 UserCoupon 记录（`source_type=vip_welcome`、`status=available`）。

#### Scenario: 首次升级赠送VIP欢迎券
- **GIVEN** 用户 `membership_level` 为 `none`
- **WHEN** 用户充值 100 元触发 VIP 升级
- **THEN** 系统创建一张 VIP 专属 8 折券（有效期 30 天）
- **AND** 创建一条 `source_type=vip_welcome` 的 UserCoupon 记录
- **AND** 充值响应包含 `vip_coupon_id`

#### Scenario: 已有VIP用户不再赠券
- **GIVEN** 用户 `membership_level` 为 `vip`
- **WHEN** 用户充值 100 元
- **THEN** 系统不创建新的欢迎券

### Requirement: 充值响应增强
系统 SHALL 在充值确认成功响应中包含 VIP 升级状态信息。RechargeResponse MUST 包含 `membership_upgraded` 布尔字段和 `vip_coupon_id` 可空整数字段。

#### Scenario: 升级成功响应包含升级信息
- **GIVEN** 用户充值 100 元触发 VIP 升级
- **WHEN** 充值确认成功
- **THEN** 响应包含 `membership_upgraded=true` 和 `vip_coupon_id`（赠送券的 UserCoupon ID）

#### Scenario: 未升级响应包含默认值
- **GIVEN** 用户充值 50 元未触发升级
- **WHEN** 充值确认成功
- **THEN** 响应包含 `membership_upgraded=false` 和 `vip_coupon_id=null`

### Requirement: 我的页面会员卡片
br-app SHALL 在我的页面展示会员状态卡片。非 VIP 用户显示"升级超级会员"入口和"立即开通"按钮；VIP 用户显示已激活状态和 VIP 标识。

#### Scenario: 非 VIP 用户显示开通入口
- **GIVEN** 用户 `membership_level` 为 `none`
- **WHEN** 用户访问我的页面
- **THEN** 会员卡片显示"升级超级会员"标题和"立即开通"按钮
- **AND** 点击按钮跳转到 VIP 权益介绍页

#### Scenario: VIP 用户显示已激活状态
- **GIVEN** 用户 `membership_level` 为 `vip`
- **WHEN** 用户访问我的页面
- **THEN** 会员卡片显示"超级会员"标题和 VIP 标识
- **AND** 不显示"立即开通"按钮或显示为禁用态

### Requirement: VIP 权益介绍页
br-app SHALL 提供 VIP 权益介绍页（`/pages/membership/index`），展示 VIP 权益列表（8折优惠、专属座位、优先预约等）和"立即开通 - 充值100元起"按钮。

#### Scenario: 展示 VIP 权益
- **WHEN** 用户访问 VIP 权益介绍页
- **THEN** 页面展示 VIP 权益列表
- **AND** 底部显示"立即开通 - 充值100元起"按钮
- **AND** 点击按钮跳转到充值页并携带 `amount=100&source=vip` 参数

#### Scenario: VIP 用户访问权益页
- **GIVEN** 用户已是 VIP
- **WHEN** 用户访问 VIP 权益介绍页
- **THEN** 页面展示权益信息
- **AND** 按钮显示"已是超级会员"或隐藏开通按钮

### Requirement: 充值页 VIP 开通联动
br-app 充值页 SHALL 检测 `source=vip` URL 参数，预填充金额为 100 元。充值成功后 SHALL 检查响应中的 `membership_upgraded` 字段，为 true 时弹出升级成功提示。

#### Scenario: VIP 来源预填充金额
- **WHEN** 用户从 VIP 权益页跳转到充值页（携带 `source=vip&amount=100`）
- **THEN** 充值金额预填充为 100 元

#### Scenario: 充值成功后弹出升级提示
- **GIVEN** 用户从 VIP 开通流程进入充值
- **WHEN** 充值 100 元成功且响应 `membership_upgraded=true`
- **THEN** 页面弹出"恭喜成为超级会员"成功提示
- **AND** 提示中展示赠送的 VIP 8 折券信息
- **AND** 用户确认后返回我的页面

