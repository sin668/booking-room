# br-server Clean Architecture 重构设计

## 目标

在不改变外部 API 行为的前提下，将 `br-server` 服务层逐步重构到更清晰的 Clean Architecture 结构。第一阶段聚焦风险最高、业务规则最集中的模块：预约、钱包、支付、预约核销。

## 当前状态

`br-server` 已经具备基础分层：

- `app/api/routes`：FastAPI HTTP 适配层。
- `app/schemas`：请求与响应 DTO。
- `app/models`：SQLAlchemy 持久化模型。
- `app/services`：业务逻辑与外部集成。
- `app/core`：配置、数据库、安全与基础设施。
- `tests`：覆盖预约、钱包、认证、优惠券、支付、核销等核心流程。

主要问题是部分服务模块承担了过多职责：

- `wallet_service.py` 同时包含钱包规则、充值订单生命周期、微信回调处理、流水持久化、兑换码兑换等逻辑。
- `booking_service.py` 同时包含预约校验、座位可用性、优惠券变更、钱包支付、冲突检查、响应组装等逻辑。
- `booking_payment_service.py` 和 `booking_verification_service.py` 已经接近领域服务，但仍把领域规则、SQLAlchemy 查询和面向接口的数据形状耦合在一起。
- 路由文件大体是适配层，但部分路由仍了解过多业务编排细节。

## 架构方向

保留现有 FastAPI 和 SQLAlchemy 技术栈，不引入重型框架或大规模抽象。

目标是在 `br-server/app` 内形成四类明确边界：

1. **API 适配层**
   - FastAPI 路由只负责解析请求、执行认证依赖、调用用例、把异常映射为 HTTP 响应。
   - 路由不承载业务决策。

2. **应用用例层**
   - 编排完整业务流程，例如创建预约、取消预约、处理钱包充值回调、确认核销。
   - 在现有代码已经要求原子性的地方保留事务边界。
   - 依赖领域服务和仓储接口。

3. **领域服务层**
   - 承载纯规则或接近纯规则：预约时间校验、取消政策、钱包余额检查、优惠券适用性、支付状态流转、核销 token 规则。
   - 优先使用普通函数或小类，输入输出显式。

4. **基础设施适配层**
   - SQLAlchemy 仓储、外部客户端、存储服务、微信和短信集成。
   - 用聚焦的方法隐藏查询细节和 SDK 细节。

## 第一阶段范围

第一阶段只覆盖 `br-server`。

### 包含

- 从钱包和预约支付路径中提取共享金额与流水辅助逻辑。
- 从 `booking_service.py` 中提取预约时间窗口和冲突校验规则。
- 从 `wallet_service.py` 中提取钱包流水写入与余额变更操作。
- 在有明确收益时，从 `booking_verification_service.py` 中提取核销 token 编解码与校验策略。
- 仅在能消除重复或让测试更清晰时引入仓储接口。
- 保持现有路由行为和响应载荷稳定。
- 对任何影响行为的重构先补测试或保留现有测试保护。

### 不包含

- 不改数据库结构。
- 不改 API 路径、响应格式或认证协议。
- 不改前端。
- 不清理 `br-admin` 模板框架遗留代码。
- 不做全局格式化。
- 不为了“看起来分层”把所有函数强行改成类。

## 目标模块形态

第一阶段的目标结构：

```text
br-server/app/
  application/
    booking_use_cases.py
    wallet_use_cases.py
    verification_use_cases.py
  domain/
    booking_rules.py
    wallet_rules.py
    payment_rules.py
    verification_rules.py
  repositories/
    booking_repository.py
    wallet_repository.py
    coupon_repository.py
    seat_repository.py
  services/
    booking_service.py
    wallet_service.py
    booking_payment_service.py
    booking_verification_service.py
```

迁移期间，现有 `services` 模块可以保留为兼容门面。这样可以减少路由改动，保证每个提交都足够小且容易回滚。

## 重构顺序

1. **基线验证**
   - 先运行钱包、预约、支付、核销相关测试。
   - 在改代码前记录当前失败或警告。

2. **提取纯规则**
   - 把确定性的校验和格式化逻辑移动到 `app/domain`。
   - 先为这些规则写单元测试。
   - 再更新现有服务调用新规则。

3. **提取仓储适配**
   - 从重复或深层嵌套的读写逻辑开始。
   - 除非测试证明需要调整，否则保持 SQLAlchemy session 所有权不变。

4. **引入应用用例**
   - 把流程编排从过大的服务函数或服务类中移出。
   - 如果路由或测试依赖现有公开函数名，则先保留包装函数。

5. **清理兼容层**
   - 只有在测试证明新路径已经被使用后，再删除重复私有辅助函数。
   - 在调用方迁移完成前，保持公开导出稳定。

## 测试策略

每个提取动作都遵循 TDD：

- 为即将提取的规则或用例写聚焦测试。
- 先确认测试失败。
- 迁移最小实现。
- 运行聚焦测试。
- 运行受影响的既有服务和 API 测试。

建议基线命令：

```powershell
python -m pytest tests/test_booking_payment_service.py -q
python -m pytest tests/test_wallet_service.py -q
python -m pytest tests/test_booking_verification_service.py -q
python -m pytest tests/test_api_booking.py -q
python -m pytest tests/test_api_wallet.py -q
```

后端全量验证：

```powershell
python -m pytest
```

## 风险

- 预约和钱包流程会修改多张表。重构必须保持事务顺序和回滚行为。
- 优惠券使用和恢复与预约创建、取消强耦合，需要定向回归测试。
- 微信支付回调依赖幂等和签名处理，第一阶段不改变回调语义。
- 现有测试覆盖较强但文件较大，需要给抽出的规则补充小而快的单元测试。

## 成功标准

- 预约、钱包、支付、核销相关既有后端测试通过。
- 新增领域模块有聚焦测试。
- 路由行为不变。
- 最大的业务服务通过提取纯规则和持久化操作减少职责。
- 不包含无关前端或管理端改动。

