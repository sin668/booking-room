## 1. 数据库迁移

- [x] 1.1 创建 Alembic 迁移：User 模型新增 `membership_level` 字符串字段（默认 `none`，nullable=False）
- [x] 1.2 执行迁移并验证 `membership_level` 列已添加到 users 表

## 2. 后端 - VIP 会员开通逻辑

- [x] 2.1 修改 `WalletService.confirm_payment()`，充值成功后检测金额 ≥ 100 且 `membership_level=none`，自动升级 VIP
- [x] 2.2 实现 VIP 欢迎券自动创建：创建 Coupon 记录（`scope=vip_only`, `type=percentage_off`, `discount_percent=80`, 有效期 30 天）和 UserCoupon 记录（`source_type=vip_welcome`）
- [x] 2.3 增强 RechargeResponse，新增 `membership_upgraded: bool` 和 `vip_coupon_id: int | None` 字段
- [x] 2.4 编写 VIP 升级逻辑单元测试（升级条件满足/不满足、已是 VIP、赠券创建）

## 3. 后端 - 卡券管理服务层

- [x] 3.1 创建 `br-server/app/services/coupon_service.py`，实现 `CouponService` 类
- [x] 3.2 实现卡券分页列表查询方法（支持 keyword、type、scope、is_active 筛选）
- [x] 3.3 实现卡券详情查询方法
- [x] 3.4 实现卡券创建方法（含 type 与优惠规则匹配校验、scope 校验）
- [x] 3.5 实现卡券更新方法（已关联活动卡券时禁止修改 type 和优惠规则）
- [x] 3.6 实现卡券启停方法（已过期卡券禁止启用）
- [x] 3.7 实现卡券删除方法（已关联 ActivityCoupon 时禁止删除）
- [x] 3.8 编写 CouponService 单元测试（覆盖率 > 90%）

## 4. 后端 - 卡券管理 API 路由

- [x] 4.1 创建 `br-server/app/schemas/coupon_admin.py`，定义 AdminCoupon 相关 Pydantic schema（创建、更新、响应）
- [x] 4.2 创建 `br-server/app/api/routes/admin_coupon.py`，实现卡券管理 CRUD 端点
- [x] 4.3 配置 RBAC 权限码：`coupon:view`、`coupon:create`、`coupon:update`、`coupon:delete`
- [x] 4.4 在 admin router `__init__.py` 中注册 `admin_coupon` 路由
- [x] 4.5 编写卡券管理 API 集成测试

## 5. 后端 - VIP 适用范围逻辑

- [x] 5.1 抽取 `_check_scope(user, coupon)` 统一方法，处理 all/first_booking/vip_only/seat_zone 四类校验
- [x] 5.2 修改用户卡券查询逻辑（`coupon.py` 路由），增加 `scope=vip_only` 校验：仅返回 `membership_level` 为 vip/svip 用户的 VIP 专享卡券
- [x] 5.3 修改预约可用卡券查询逻辑，增加 VIP 用户校验
- [x] 5.4 编写 VIP 适用范围相关单元测试（VIP 用户可见/不可见、非 VIP 用户不可见）

## 6. 管理后台 br-admin - API 层

- [x] 6.1 创建 `br-admin/src/api/coupon/index.ts`，定义卡券管理 API 函数和 TypeScript 类型
- [x] 6.2 实现卡券列表查询、详情、创建、更新、启停、删除 API 调用

## 7. 管理后台 br-admin - 卡券管理页面

- [x] 7.1 创建 `br-admin/src/views/coupon/list/index.vue` 卡券列表页（表格、搜索、筛选、分页）
- [x] 7.2 创建 `br-admin/src/views/coupon/list/CouponEditModal.vue` 卡券新建/编辑弹窗表单（含类型联动优惠规则字段、适用范围选择含"VIP专享"、有效期日期选择器）
- [x] 7.3 创建 `br-admin/src/views/coupon/list/columns.ts` 表格列定义和格式化工具（适用范围含"VIP专享"标签）
- [x] 7.4 实现卡券状态切换（启停）操作和确认对话框
- [x] 7.5 实现卡券删除操作和关联冲突提示

## 8. 管理后台 br-admin - 路由和菜单

- [x] 8.1 创建 `br-admin/src/router/modules/coupon.ts` 路由模块（路径 `/coupon/list`）
- [x] 8.2 准备卡券管理菜单 SQL 数据（`admin_menus` 表 INSERT），包含目录和菜单项

## 9. 管理后台 br-admin - 活动卡券选择器改造

- [x] 9.1 修改 `ActivityCouponConfig.vue`，将卡券 ID 输入框替换为 `NSelect` 远程搜索选择器
- [x] 9.2 实现卡券选择器远程搜索（调用 admin coupons API，300ms 防抖）
- [x] 9.3 选中卡券后自动回显类型、优惠规则、有效期等只读信息
- [x] 9.4 添加重复关联同卡券的提示校验

## 10. 前端 br-app - VIP 会员开通

- [x] 10.1 修改我的页面（`profile/index.vue`）会员卡片：非 VIP 显示"立即开通"跳转权益页，VIP 显示已激活状态
- [x] 10.2 新增 VIP 权益介绍页（`pages/membership/index.vue`），展示权益列表和"立即开通"按钮
- [x] 10.3 修改充值页（`pages/recharge/index.vue`），检测 `source=vip` 参数预填充金额 100 元
- [x] 10.4 充值成功后检查 `membership_upgraded`，为 true 时弹出升级成功提示和赠券信息

## 11. 前端 br-app - 活动详情卡券区域

- [x] 11.1 修改 `br-app/src/pages/activity/detail.vue`，当 `activityCoupons.length === 0` 时使用 `v-if` 不渲染整个 coupon-section

## 12. 文档与收尾

- [x] 12.1 更新 `docs/api.md`，补充管理后台卡券管理接口和 VIP 会员相关接口文档
- [x] 12.2 代码审查：确保 Clean Architecture 分层、消除重复代码、权限校验完整
