## 1. 后端 Schema 与查询模型

- [x] 1.1 在 `br-server/app/schemas/wallet.py` 新增钱包流水列表项响应结构，字段包含 `id`、`type`、`title`、`amount`、`bonus_amount`、`direction`、`status`、`payment_method`、`balance_after`、`created_at`、`completed_at`、`order_id`
- [x] 1.2 在 `br-server/app/schemas/wallet.py` 新增钱包流水分页响应结构，字段包含 `items`、`total`、`page`、`page_size`、`has_more`
- [x] 1.3 明确流水类型筛选枚举：`all`、`recharge`、`consume`、`refund`
- [x] 1.4 明确分页参数约束：`page` 默认 1 且最小 1，`page_size` 默认 20 且范围为 1 到 50
- [x] 1.5 确认金额字段对外以 Decimal/字符串兼容的稳定格式返回，前端不得依赖浮点计算资金结果

## 2. 后端 Service 查询能力

- [x] 2.1 在 `br-server/app/services/wallet_service.py` 新增 `list_transactions(user_id, page, page_size, type)` 只读查询方法
- [x] 2.2 查询条件必须包含当前认证用户 `user_id`，不得允许前端传入或覆盖查询用户
- [x] 2.3 当 `type=all` 时查询当前用户全部钱包流水；当 `type=recharge`、`consume`、`refund` 时按类型过滤
- [x] 2.4 对 `consume`、`refund` 等预留类型，在无数据时返回空分页结果，不伪造流水
- [x] 2.5 查询结果按 `created_at` 倒序排列，并增加稳定的次级排序字段，避免同时间记录顺序漂移
- [x] 2.6 将充值流水标题映射为：`completed=充值到账`、`pending=充值待支付`、`failed=充值失败`
- [x] 2.7 将充值流水 `direction` 映射为 `income`，但只有 `completed` 状态允许前端展示到账成功视觉
- [x] 2.8 映射 `completed_at`：优先使用支付完成时间；没有完成时间时，待处理/失败流水允许返回空值
- [x] 2.9 计算 `has_more`，确保当前页不是最后一页时为 `true`，没有更多数据时为 `false`

## 3. 后端路由与接口契约

- [x] 3.1 在 `br-server/app/api/routes/wallet.py` 新增 `GET /api/v1/wallet/transactions` 路由
- [x] 3.2 路由复用现有认证依赖，未登录或 token 无效时返回 401
- [x] 3.3 路由复用现有数据库依赖和 `WalletService` 实例化方式，保持 route 层只做参数校验和 service 调用
- [x] 3.4 对不支持的 `type` 返回 422，并提供可理解的错误信息
- [x] 3.5 对 `page < 1`、`page_size < 1`、`page_size > 50` 返回 422
- [x] 3.6 确认接口不接收、不信任、也不透传 `user_id` 查询参数
- [x] 3.7 确认响应字段与 `wallet-recharge-api` 规格一致，包含分页元数据和流水列表

## 4. 后端测试

- [x] 4.1 在钱包 service 测试中覆盖当前用户第一页流水查询，断言只返回该用户数据
- [x] 4.2 在钱包 service 测试中覆盖 `type=recharge` 过滤，断言不返回其他类型流水
- [x] 4.3 在钱包 service 测试中覆盖倒序排序，断言新流水排在旧流水之前
- [x] 4.4 在钱包 service 测试中覆盖充值状态标题映射：完成、待支付、失败
- [x] 4.5 在钱包 API 测试中覆盖 `GET /api/v1/wallet/transactions` 成功响应结构
- [x] 4.6 在钱包 API 测试中覆盖 `type=consume` 且无数据时返回空列表和 `total=0`
- [x] 4.7 在钱包 API 测试中覆盖非法 `type` 返回 422
- [x] 4.8 在钱包 API 测试中覆盖分页参数越界返回 422
- [x] 4.9 在钱包 API 测试中覆盖越权隔离：A 用户不得看到 B 用户流水
- [x] 4.10 在钱包 API 测试中覆盖未认证请求返回 401
- [x] 4.11 运行钱包相关后端测试，并修复由本变更引入的回归

## 5. 前端 API 层

- [x] 5.1 在 `br-app/src/api/wallet.js` 新增 `getWalletTransactions(params)` 方法
- [x] 5.2 请求参数统一传递 `page`、`page_size`、`type`
- [x] 5.3 方法复用现有 `get` 请求工具，不新增请求库或全局状态依赖
- [x] 5.4 保持现有 `getBalance`、`createRechargeOrder`、`getRechargeOrder`、`confirmPayment`、`redeemPromoCode` 行为不变

## 6. 前端钱包流水页面

- [x] 6.1 新建 `br-app/src/pages/wallet/transactions.vue`
- [x] 6.2 在 `br-app/src/pages.json` 注册 `pages/wallet/transactions`，导航标题为“钱包流水”
- [x] 6.3 页面初始化时并行或顺序加载余额摘要和第一页流水，任一请求失败不得阻塞另一个区域展示
- [x] 6.4 顶部余额摘要复用现有品牌主色和充值页余额卡视觉，展示当前余额和累计充值金额
- [x] 6.5 构建紧凑筛选控件，默认选中“全部”，并提供“充值”筛选
- [x] 6.6 切换筛选时清空旧列表、重置页码、重新请求第一页
- [x] 6.7 实现首次加载状态，列表区域展示骨架或明确加载反馈，不出现空白等待
- [x] 6.8 实现上拉加载下一页，`has_more=false` 后停止继续请求
- [x] 6.9 实现“没有更多流水了”到底提示
- [x] 6.10 渲染流水列表项：左侧类型图标，中间标题/状态/时间/支付方式，右侧金额，底部展示交易后余额和赠送金额
- [x] 6.11 完成充值流水展示为正向收入视觉；待支付和失败充值不得使用到账成功视觉
- [x] 6.12 空列表时展示“暂无钱包流水”，并提供前往钱包充值的行动入口
- [x] 6.13 流水接口失败时展示“流水加载失败，请重试”，重试按当前筛选条件重新加载第一页
- [x] 6.14 余额摘要加载失败时提示“余额加载失败”，但仍允许流水列表正常加载和刷新
- [x] 6.15 页面样式使用现有 SCSS 变量和项目主色，不引入独立金融深色主题或新的全局视觉体系
- [x] 6.16 检查 375px 宽度下长标题、金额、状态文案不溢出、不遮挡

## 7. 前端入口与导航

- [x] 7.1 在 `br-app/src/pages/profile/index.vue` 的会员服务区域新增“钱包流水”菜单项
- [x] 7.2 “钱包流水”菜单项点击后跳转 `/pages/wallet/transactions`
- [x] 7.3 保留现有“钱包充值”入口和跳转行为不变
- [x] 7.4 在 `br-app/src/pages/recharge/index.vue` 余额卡片区域增加“交易明细”轻入口
- [x] 7.5 充值页“交易明细”入口点击后跳转 `/pages/wallet/transactions`
- [x] 7.6 确认新增入口在视觉上与现有菜单、卡片操作保持一致，不造成布局拥挤

## 8. 前端验证

- [x] 8.1 运行 `br-app` 可用的 lint 或 build 命令，确认前端语法和构建无新增错误
- [x] 8.2 验证钱包流水页面有数据时能展示余额摘要、筛选和流水列表
- [x] 8.3 验证“全部”和“充值”筛选切换会重置列表并重新加载
- [x] 8.4 验证分页加载会追加数据，且到底后不重复请求
- [x] 8.5 验证空状态展示“暂无钱包流水”并可跳转钱包充值
- [x] 8.6 验证流水接口错误状态可重试
- [x] 8.7 验证余额接口错误不会阻断流水列表
- [x] 8.8 验证个人中心“钱包流水”入口可达
- [x] 8.9 验证充值页“交易明细”入口可达
- [x] 8.10 验证页面使用现有品牌色、白色卡片、圆角和弱化分隔线，不出现独立金融主题
- [x] 8.11 验证常见移动端宽度下文本不溢出、按钮不遮挡、底部安全区正常

## 9. API 文档与代码审查

- [x] 9.1 更新 `docs/api.md`，新增 `GET /api/v1/wallet/transactions` 接口说明
- [x] 9.2 文档说明查询参数：`page`、`page_size`、`type`
- [x] 9.3 文档说明响应字段：`items`、`total`、`page`、`page_size`、`has_more` 以及流水项字段
- [x] 9.4 文档说明错误场景：401 未认证、422 参数非法或类型不支持
- [x] 9.5 审查后端分层：route 层保持薄封装，业务映射集中在 service/schema，model 不承载展示逻辑
- [x] 9.6 审查前端分层：页面负责状态与展示，API 文件只封装请求，避免把后端字段映射散落到多个页面
- [x] 9.7 审查是否存在重复金额格式化或状态映射逻辑；只有在实际复用点明确时再抽取工具函数
- [x] 9.8 运行 `npx @fission-ai/openspec validate wallet-transactions-frontend --strict`，确认 OpenSpec 变更仍然有效

