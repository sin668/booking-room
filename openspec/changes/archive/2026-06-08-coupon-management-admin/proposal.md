## Why

当前卡券模型（Coupon、ActivityCoupon、UserCoupon）已在后端定义完成，用户端领券和用券流程也已实现，但管理后台（br-admin）缺少独立的卡券管理能力。运营人员无法通过后台创建、编辑、停用卡券模板，活动关联卡券时只能手动输入卡券 ID，无法浏览选择。此外，卡券适用范围仅支持全场通用、首次预约和指定座位类型，缺少 VIP 用户限制，无法满足精细化运营需求。

## What Changes

- 新增管理后台卡券 CRUD API，支持卡券模板的创建、查询、更新、停用/启用和分页列表
- 新增管理后台卡券列表页面（br-admin），包含卡券列表、新建/编辑表单、状态切换等 UI
- 在管理后台新增卡券管理菜单入口
- User 模型新增 `membership_level` 枚举字段（`none`/`vip`/`svip`预留），支持 VIP 会员体系
- VIP 开通机制：用户单次充值 ≥ 100 元自动升级 VIP（永久有效），首次开通赠送 8 折券（有效期 1 个月）
- 卡券模型新增 VIP 用户适用范围（`scope=vip_only`），仅 VIP 用户可领取和使用该卡券
- br-app 新增 VIP 权益介绍页，我的页面会员卡片联动充值开通流程
- 活动管理中的卡券关联组件改用卡券选择器替代手动 ID 输入
- br-app 活动详情页：当活动无关联卡券时，整个卡券区域不渲染（而非显示空状态）

## Capabilities

### New Capabilities
- `coupon-admin-api`: 管理后台卡券模板 CRUD 接口（列表、详情、创建、更新、启停）
- `coupon-admin-ui`: 管理后台卡券管理页面（列表页、新建/编辑表单、菜单入口）

### New Capabilities
- `vip-membership`: VIP 会员开通机制（membership_level 字段、充值触发升级、首次开通赠券、权益页）

### Modified Capabilities
- `coupon-api`: 新增 VIP 用户适用范围（`scope=vip_only`），卡券使用和查询逻辑使用 `membership_level` 校验
- `activity-admin-ui`: 活动卡券关联组件使用卡券选择器替代手动 ID 输入，支持搜索和预览
- `wallet-recharge-api`: 充值确认回调中嵌入 VIP 升级逻辑，返回增强的 RechargeResponse

## Impact

- **后端 br-server**: 新增 `admin_coupon.py` 路由文件，新增 `CouponService` 服务层，修改 Coupon 模型校验逻辑
- **管理后台 br-admin**: 新增 `views/coupon/` 目录（列表页、表单页），新增 `api/coupon/` API 模块，新增路由模块，需新增菜单数据
- **前端 br-app**: 修改 `pages/activity/detail.vue` 卡券区域条件渲染逻辑
- **数据库**: 新增 `membership_level` 列的 Alembic 迁移（`scope` 字段无需迁移，新增 `vip_only` 值即可）
- **回滚方案**: 删除新增的 admin 路由和服务文件，恢复 ActivityCouponConfig.vue 的手动 ID 输入方式，恢复 br-app 的卡券空状态显示，回滚 Alembic 迁移移除 `membership_level` 列
