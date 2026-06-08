## Context

当前系统已完成卡券核心数据模型（Coupon、ActivityCoupon、UserCoupon）和用户端领券/用券流程。卡券 API 规范（`coupon-api`）定义了满减、立减、折扣三类卡券和全场通用、首次预约、指定座位区域三种适用范围。活动卡券活动（`activity-coupon-campaign`）实现了活动关联卡券的领取机制。

管理后台（br-admin）已实现活动管理页面（`activity-admin-ui`），其中 `ActivityCouponConfig.vue` 组件支持关联卡券配置，但卡券模板 ID 需手动输入，缺少卡券浏览和选择能力。后端缺少独立的卡券管理 CRUD API。

用户模型当前无 VIP 等级字段，需新增 VIP 用户标识以支持 VIP 专享卡券。

## Goals / Non-Goals

**Goals:**
- 提供管理后台卡券模板全生命周期管理能力（CRUD + 启停）
- 在 br-admin 新增卡券管理菜单和列表页面，遵循现有 admin 页面风格（Naive UI + 表格 + 弹窗表单）
- 新增 VIP 用户适用范围，使卡券可限定仅 VIP 用户使用
- 改善活动关联卡券的交互体验，使用卡券选择器替代手动 ID 输入
- br-app 活动详情页无关联卡券时隐藏整个卡券区域

**Non-Goals:**
- SVIP 开通规则和权益定义（仅预留枚举值）
- 不涉及用户 VIP 等级的降级机制（VIP 永久有效）
- 不涉及卡券领取后的核销流程改造
- 不涉及卡券数据统计和分析报表
- 不涉及卡券批量操作（批量创建、批量停用）

## Decisions

### 决策 1：VIP 用户标识方案

**选择**：在 User 模型新增 `membership_level` 字符串枚举字段（`none`/`vip`/`svip`）

**备选方案**：
- A) 在 User 模型新增 `is_vip` 布尔字段 —— 当前够用但无法扩展到多级会员体系
- B) 新建 `user_membership` 关联表 —— 支持复杂会员体系但当前需求不匹配

**理由**：使用枚举字段为未来 SVIP 等多级会员预留扩展空间，同时当前实现成本与布尔字段几乎相同。

**影响**：需 Alembic 迁移添加 `membership_level` 列；用户端卡券查询需增加 VIP 校验。

### 决策 1.1：VIP 升级触发机制

**选择**：在充值确认回调中内嵌 VIP 升级逻辑

**触发条件**：`WalletService.confirm_payment()` 中充值金额 ≥ 100 且用户 `membership_level == "none"`

**执行流程**：同一 DB 事务内更新 `membership_level` 为 `"vip"`，创建 VIP 欢迎券（`scope=vip_only`, `type=percentage_off`, `discount_percent=80`, 有效期 30 天），创建 UserCoupon（`source_type=vip_welcome`）

**响应增强**：RechargeResponse 新增 `membership_upgraded: bool` 和 `vip_coupon_id: int | None` 字段

### 决策 2：卡券适用范围扩展方式

**选择**：在现有 `scope` 字段新增 `vip_only` 值

**理由**：`scope` 字段为 String 类型，当前值为 `all`、`first_booking` 和座位区域值（如 `vip`、`economy`）。为避免歧义，VIP 用户限制使用 `vip_only`（而非复用 `vip` 座位区域值），保持语义清晰。

**校验逻辑**：
- `scope=all`：所有用户可用
- `scope=first_booking`：仅无成功预约历史的用户可用
- `scope=vip_only`：仅 `membership_level` 为 `vip` 或 `svip` 的用户可用
- `scope=<seat_zone>`：仅匹配对应座位区域

### 决策 3：Admin API 路由和服务组织

**选择**：新增 `admin_coupon.py` 路由文件 + `coupon_service.py` 服务层

**模式**：遵循现有 admin 路由模式（参考 `admin_activity.py`）：
- 路由前缀：`/api/v1/admin/coupons`
- 权限码：`coupon:view`、`coupon:create`、`coupon:update`、`coupon:delete`
- 路由注册到 admin router（在 `__init__.py` 中挂载）
- 服务层封装数据库操作和业务校验

### 决策 4：活动卡券选择器实现方式

**选择**：在 ActivityCouponConfig.vue 中将卡券 ID 输入框替换为 `NSelect` 组件，调用 `GET /api/v1/admin/coupons` 远程搜索

**理由**：复用卡券管理 API，支持模糊搜索，选中后自动回显卡券信息。无需新建独立的选择器接口。

### 决策 5：br-app 卡券区域条件渲染

**选择**：在 `activity/detail.vue` 中，当 `activityCoupons.length === 0` 时不渲染整个 `coupon-section` 容器

**当前行为**：始终显示 coupon-section，无卡券时展示空状态文案。

**修改后**：使用 `v-if="activityCoupons.length > 0"` 包裹 coupon-section，无卡券时整个区域不渲染。

## Risks / Trade-offs

**[VIP 运营管理]** → br-admin 用户管理页面需新增 `membership_level` 展示和编辑能力，可通过管理后台手动调整用户会员等级。

**[卡券选择器性能]** → 当卡券数量较大时，远程搜索可能存在延迟。使用分页 + 防抖（300ms）+ 缓存最近搜索结果缓解。

**[scope 值歧义]** → `scope` 字段同时承载用户限制（all/first_booking/vip_only）和座位限制（座位区域名）。当前通过值语义区分，未来如限制类型增多，可拆分为 `user_scope` + `seat_scope` 两个字段。

## 迁移计划

1. 后端新增 `membership_level` 字段的 Alembic 迁移（默认 `none`）
2. 后端在充值确认流程中嵌入 VIP 升级和赠券逻辑
3. 后端新增 `admin_coupon.py` 路由和 `coupon_service.py` 服务
4. 后端修改用户卡券查询逻辑，增加 `membership_level` 校验
5. br-app 新增 VIP 权益介绍页和会员卡片联动
6. br-app 充值页支持 VIP 开通参数和升级提示
7. br-admin 新增卡券管理页面和菜单
8. br-admin 修改 ActivityCouponConfig.vue 卡券选择器
9. br-app 修改活动详情卡券区域条件渲染
10. 数据库插入卡券管理菜单数据到 `admin_menus` 表

**回滚方案**：
- 删除新增的 `admin_coupon.py`、`coupon_service.py`、相关 schema 文件
- 回滚 Alembic 迁移移除 `membership_level` 列
- 恢复 ActivityCouponConfig.vue 的手动 ID 输入
- 恢复 br-app 的卡券空状态显示
- 删除 `admin_menus` 中的卡券管理菜单记录
