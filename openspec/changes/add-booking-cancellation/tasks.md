## 1. 当前状态梳理

- [x] 1.1 梳理 `br-server/app/models/booking.py` 中现有预约状态、支付、卡券和金额字段。
- [x] 1.2 梳理 `br-server/app/services/booking_service.py` 中现有创建、列表、详情、取消逻辑和事务边界。
- [x] 1.3 梳理 `br-server/app/api/routes/booking.py` 和 `br-server/app/schemas/booking.py` 中现有取消接口和响应结构。
- [x] 1.4 梳理钱包模型、Schema、Service 和路由中的流水类型处理、余额更新模式。
- [x] 1.5 梳理 `br-app/src/pages/orders/index.vue` 中“查看座位”操作区、状态文案、列表刷新流程和弹窗/Toast 模式。
- [x] 1.6 梳理 `br-app/src/api/bookings.js` 与钱包 API 模块中现有请求封装约定。

## 2. 数据库迁移和模型

- [x] 2.1 新增 Alembic 迁移，为预约表增加取消审计字段：`cancelled_at`、`penalty_amount`、`refund_amount`、`cancel_policy`。
- [x] 2.2 扩展钱包流水持久化，支持 `type='booking_refund'` 并增加预约关联字段。
- [x] 2.3 更新 SQLAlchemy 预约模型，使字段默认值和可空规则与迁移一致。
- [x] 2.4 更新钱包流水模型和类型校验，使 `booking_refund` 可用且不影响已有充值记录。
- [x] 2.5 尝试在本地配置环境运行迁移，若环境不可用则记录阻塞原因。
  - 说明：使用临时 SQLite 数据库执行 `alembic upgrade head` 时，被历史迁移中 SQLite 不支持的 `ALTER COLUMN` 语法阻塞，尚未执行到本次迁移。模型/表兼容性已通过异步 SQLite 测试库的 `Base.metadata.create_all` 覆盖。
- [x] 2.6 增加迁移/模型相关验证，覆盖取消字段默认值和 `booking_refund` 类型兼容性。
- [x] 2.7 为 `booking_refund` 增加预约维度的数据库唯一保护，降低重复退款风险。

## 3. 取消规则逻辑

- [x] 3.1 在后端服务层新增聚焦的取消规则辅助模块。
- [x] 3.2 使用 `booking.date` 和 `booking.start_time` 组合预约开始时间，并按 `BOOKING_TIMEZONE` 获取服务端当前时间。
- [x] 3.3 实现取消档位和金额计算：`remaining > 48h`、`24h < remaining <= 48h`、`2h < remaining <= 24h`、`0 < remaining <= 2h`、`remaining <= 0`。
- [x] 3.4 所有金额计算使用 Decimal，并确保 `penalty_amount + refund_amount = total_price`。
- [x] 3.5 增加取消规则边界测试，覆盖精确 48 小时、24 小时、2 小时和预约开始时间点。
- [x] 3.6 增加非整金额测试，确认两位小数舍入稳定。
- [x] 3.7 为列表/详情响应增加当前取消预估字段 `cancel_penalty_amount` 和 `cancel_refund_amount`，避免前端误用取消后审计字段。

## 4. 预约状态同步

- [x] 4.1 增加后端逻辑：已支付 confirmed 预约到达开始时间后同步为 `completed`。
- [x] 4.2 在预约列表/详情响应中复用完成状态同步，避免过期 confirmed 订单继续显示可取消。
- [x] 4.3 在取消请求中复用完成状态同步，作为服务端最终校验。
- [x] 4.4 增加测试，证明已开始 confirmed 预约在列表/详情访问时会变成 `completed`。
- [x] 4.5 增加测试，证明预约开始时间点及之后取消会被拒绝且不会创建退款。

## 5. 取消接口和结算

- [x] 5.1 更新 `POST /api/v1/bookings/{booking_id}/cancel/`，确保只能取消当前用户自己的预约。
- [x] 5.2 强制取消资格：状态必须为 `confirmed`，支付状态必须为 `paid`，预约尚未开始。
- [x] 5.3 锁定预约行并查询既有退款流水，保护重复点击和重复退款场景。
- [x] 5.4 在一个数据库事务中更新预约状态/审计字段、恢复卡券、增加钱包余额、创建 `booking_refund` 钱包流水。
- [x] 5.5 返回取消结果字段：预约状态、`penalty_amount`、`refund_amount`、`cancel_policy`、`cancelled_at` 和退款流水标识。
- [x] 5.6 增加 API 测试，覆盖全额退款、10% 扣款、20% 扣款、50% 扣款。
- [x] 5.7 增加无效取消测试，覆盖已取消、已完成/已开始、未支付、其他用户预约。
- [x] 5.8 增加重复取消测试，证明不会重复增加余额，也不会创建第二条 `booking_refund` 流水。
- [x] 5.9 管理端取消接口复用同一套取消结算逻辑，避免后台绕过退款和审计规则。

## 6. 预约 Schema 和列表响应

- [x] 6.1 扩展预约响应 Schema，包含 `cancelled_at`、`penalty_amount`、`refund_amount`、`cancel_policy`、`can_cancel`。
- [x] 6.2 确保列表和详情响应中的 Decimal 金额字段与现有预约金额字段序列化风格一致。
- [x] 6.3 确保仅当前用户、已支付、confirmed、未来开始的预约返回 `can_cancel=true`。
- [x] 6.4 确保已取消、已完成、未支付、已开始预约返回 `can_cancel=false`。
- [x] 6.5 增加 Schema/列表/详情测试，覆盖新增取消字段和 `can_cancel`。
- [x] 6.6 管理端预约响应增加取消审计字段，方便后台查看取消退款结果。

## 7. 钱包流水查询更新

- [x] 7.1 将 `booking_refund` 流水映射为标题“取消退款”、方向 `income`、状态 `completed`，返回金额、交易后余额、完成时间和预约关联。
- [x] 7.2 确保 `GET /api/v1/wallet/transactions?type=all` 包含 `booking_refund` 流水。
- [x] 7.3 确保 `GET /api/v1/wallet/transactions?type=booking_refund` 仅返回当前用户的预约取消退款流水。
- [x] 7.4 保持现有充值、待支付充值、失败充值和非法类型行为不变。
- [x] 7.5 增加钱包流水 API 测试，覆盖 `booking_refund` 映射、筛选、all 查询、排序和当前用户隔离。

## 8. br-app 预约 API 客户端

- [x] 8.1 确认 `br-app/src/api/bookings.js` 中已有 `cancelBooking(bookingId)`，并保持现有请求封装风格。
- [x] 8.2 订单列表直接使用后端取消响应字段和列表预估字段：状态、退款金额、扣款金额、错误信息。
- [x] 8.3 保持现有预约列表、支付状态和查看座位 API 客户端行为不变。
- [x] 8.4 通过页面集成构建验证覆盖客户端行为；项目暂无单独 API 模块测试脚本。

## 9. br-app 订单列表 UI

- [x] 9.1 在 `can_cancel=true` 的订单中，将“取消”操作添加到“查看座位”右侧。
- [x] 9.2 对 `can_cancel=false`、`cancelled`、`completed` 订单隐藏“取消”操作。
- [x] 9.3 调用取消接口前增加确认弹窗，文案说明退款退回钱包。
- [x] 9.4 取消请求进行中禁用取消操作，防止重复点击。
- [x] 9.5 取消成功后展示包含退款金额的成功提示，并刷新订单列表。
- [x] 9.6 已开始预约取消被拒绝时展示“已开始不可取消”提示，刷新列表并显示“已完成”。
- [x] 9.7 通用失败或网络错误时展示“取消失败，请重试”，不乐观修改当前列表状态。
- [x] 9.8 保持按钮间距、字体和操作区视觉风格与现有订单卡片一致。
- [x] 9.9 如果当前取消会产生扣款，确认弹窗展示扣款金额提醒。

## 10. br-app 钱包流水 UI

- [x] 10.1 在钱包流水页面增加“退款”Tab，按 `type=booking_refund` 查询预约取消退款流水。
- [x] 10.2 将 `booking_refund` 流水图标文字显示为“退”。
- [x] 10.3 将钱包流水页顶部统计按顺序调整为“累计充值 / 消费支出 / 取消退款”。
- [x] 10.4 “消费支出”和“取消退款”按当前已加载流水分别汇总 `consume` 和 `booking_refund` 的完成金额。

## 11. API 文档

- [x] 11.1 更新 `docs/api.md`，记录 `POST /api/v1/bookings/{booking_id}/cancel/` 的资格条件、退款档位、响应字段和错误场景。
- [x] 11.2 记录余额支付和微信支付预约取消后均退回钱包，不走原支付渠道退款。
- [x] 11.3 记录钱包流水 `type=booking_refund`、标题“取消退款”、方向 `income` 和 `type=booking_refund` 筛选。
- [x] 11.4 记录预约列表/详情字段 `can_cancel`、`cancelled_at`、`penalty_amount`、`refund_amount`、`cancel_policy`，以及取消预估字段。

## 12. 评审和重构

- [x] 12.1 检查路由、服务、Schema 边界，确保取消规则和结算逻辑不放在路由处理器中。
- [x] 12.2 重构新增的金额格式化、预约开始时间和取消资格检查逻辑，避免重复。
- [x] 12.3 确认钱包结算和预约取消共享清晰的事务边界。
- [x] 12.4 确认业务正确性不依赖前端校验；前端只负责展示和交互提示。
- [x] 12.5 使用只读评审代理检查实现，处理时区、管理端取消、唯一约束、文档一致性等评审反馈。

## 13. 验证

- [x] 13.1 运行后端取消规则和舍入单元测试。
- [x] 13.2 运行后端取消接口、完成状态同步、钱包退款流水和钱包流水筛选测试。
- [x] 13.3 运行现有预约支付测试，确认余额支付和微信支付创建流程不受影响。
- [x] 13.4 运行管理端取消相关测试，确认后台取消也会结算退款。
- [x] 13.5 运行 br-app 小程序构建验证。
- [x] 13.6 运行 OpenSpec 状态检查，确认 `add-booking-cancellation` 变更所有工件完整。
- [x] 13.7 运行 `git diff --check` 并审阅最终 diff，确认仅包含预期后端、前端、文档和 OpenSpec 变更。
