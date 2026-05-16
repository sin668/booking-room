## Why

当前钱包充值页面和后端钱包 API 已支持创建充值订单与模拟确认支付，但尚未接入真实微信支付。小程序端选择“微信支付”后仍直接调用后端确认接口，缺少微信统一下单、客户端支付参数、微信支付结果通知、签名验签、幂等回调和异常补偿能力，无法上线处理真实资金。

需要将钱包充值链路升级为微信支付 JSAPI 支付，使用户可在微信小程序内完成真实支付；后端以微信支付回调作为唯一可信入账来源，保证余额和交易流水一致。

## What Changes

- 后端新增微信支付配置、签名、验签、统一下单、回调解密与订单查询能力。
- 修改钱包充值接口：创建充值订单时返回微信小程序支付参数，不再依赖前端调用模拟确认接口完成入账。
- 新增微信支付异步通知接口，校验通知来源与签名后幂等更新充值订单、用户余额和交易流水。
- 新增订单支付状态查询接口，供前端在支付完成、取消或未知状态时轮询确认结果。
- 小程序充值页接入 `uni.requestPayment`，微信支付成功后查询后端订单状态并刷新余额。
- 保留支付宝选择入口但标记为暂不可用，避免误导用户进入未实现支付链路。
- 更新 API 文档与测试覆盖，补齐单元测试、接口测试和支付回调异常场景。

## Capabilities

### New Capabilities

- `wechat-payment-api`: 微信支付后端能力，包含统一下单、支付参数生成、回调验签/解密、幂等入账、订单状态查询和异常处理。
- `wechat-payment-ui`: 小程序微信支付前端能力，包含支付参数消费、`uni.requestPayment` 唤起、结果轮询、失败提示和余额刷新。

### Modified Capabilities

- `wallet-recharge-api`: 充值订单创建响应需包含 `payment_params`、`payment_provider`、`payment_status` 等真实支付字段；模拟确认接口仅允许在测试环境使用或移除出生产入口。
- `wallet-recharge-ui`: 充值提交流程从“创建订单后立即确认”改为“创建订单 -> 唤起微信支付 -> 查询支付结果 -> 刷新余额”。

## Impact

- **前端模块**：`br-app`，主要影响 `src/pages/recharge/index.vue` 与 `src/api/wallet.js`。
- **后端模块**：`br-server`，主要影响 `app/services/wallet_service.py`、`app/api/routes/wallet.py`、新增微信支付 service/client/schema/config。
- **数据库**：扩展 `wallet_transactions` 支付字段，建议增加 `payment_provider`、`payment_status`、`prepay_id`、`transaction_id`、`paid_at`、`notify_payload`、`notify_processed_at`，并确保 `order_id` 与微信交易号具备唯一约束。
- **API 变更**：修改 `POST /api/v1/wallet/recharge` 响应；新增 `GET /api/v1/wallet/recharge/{order_id}`；新增 `POST /api/v1/wallet/wechat/notify`。
- **配置变更**：新增微信支付商户号、AppID、API v3 密钥、商户私钥/证书序列号、平台证书缓存或公钥配置、回调 URL。
- **安全影响**：回调接口必须验签、解密、校验金额、校验订单归属与状态，禁止使用客户端支付成功结果直接入账。
- **回滚方案**：保留旧的测试环境模拟确认接口；若生产微信支付异常，可关闭微信支付配置开关，前端隐藏充值提交或提示暂不可用。数据库新增列可通过 Alembic downgrade 回滚；已创建的 pending 订单保持未入账，不影响用户余额。
