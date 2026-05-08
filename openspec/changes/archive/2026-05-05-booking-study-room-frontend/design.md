## Context

当前系统已完成自习室列表后端 API（`GET /api/v1/rooms/`）和数据库模型（`study_rooms` 表）。br-app 移动端有 4 个 tab 页（首页、预约、订单、我的），其中"预约"和"订单"均为占位符。后端无座位和预约相关 API 及数据模型。

技术约束：
- br-app UI 实现参考 prototype 目录的高保真原型图，请保持总体风格一致
- br-app 使用 uni-app (Vue3) + uView 2.0，需兼容微信小程序和 H5
- br-server 使用 FastAPI + SQLAlchemy，PostgreSQL 18
- 遵循项目现有分层架构（routes → services → models → schemas）

## Goals / Non-Goals

**Goals:**
- 用户可在 br-app 预约 tab 页完成日期、时段、座位选择并下单预约
- 用户可在门店详情页查看座位概况后进入座位选择
- 用户可在"订单"页查看预约记录及状态
- 后端提供座位查询 API 和预约 CRUD API，含冲突检测和取消机制

**Non-Goals:**
- 支付功能（后续迭代，确认页先展示费用明细）
- 管理后台预约管理功能
- 评价系统
- 楼层切换功能（原型中有，MVP 先固定单楼层）

## Decisions

### 1. 预约模型：按时间范围预约房间内座位

选择按房间内座位 + 日期 + 时间段预约。

**备选方案**：
- A) 房间内座位 + 时间段（选定方案）
- B) 整间房间 + 时间段

**理由**：需要区分静音区、键盘区、VIP区三个区域，模拟生成一定量的座位数据供预约。参照 prototype 中 `booking.html` 和 `seat-select.html` 的座位图交互。

### 2. 座位模型设计

Seat 模型字段：`id`、`room_id`（外键）、`seat_number`（如 "A-01"）、`zone`（枚举：quiet/keyboard/vip）、`position`（如 "靠窗"、"中间"、"独立"）、`floor`（楼层，默认 3）、`price_per_hour`（每小时价格）、`status`（枚举：available/maintenance），以及 `row`、`col` 用于座位图布局。

MVP 阶段通过 alembic seed 脚本为每个自习室模拟生成座位数据。

### 3. 时间冲突检测：应用层校验 + 数据库约束

在 service 层查询同座位同日期的时间重叠，返回明确错误信息。

**备选方案**：
- A) 应用层校验（选定方案）
- B) 仅数据库唯一约束

**理由**：应用层可返回友好的错误消息（如"该时段已被预约"），数据库约束作为兜底防止并发冲突。

### 4. 预约状态流转

```
confirmed → completed
     ↘ cancelled
```

- `confirmed`：已确认（MVP 阶段创建即 confirmed）
- `completed`：已使用（手动标记）
- `cancelled`：用户取消

MVP 阶段简化为创建即 confirmed，用户可取消。

### 5. 前端页面结构

参照 prototype 目录中的原型图：

```
pages/booking/index.vue        → 预约主页面（日期+时段+区域筛选+座位图+立即预约）
                                 参照 prototype/booking.html
pages/booking/detail.vue       → 门店详情页（封面/评分/地址/座位概况/环境照片/立即预约）
                                 参照 prototype/store-detail.html
pages/booking/seat-select.vue  → 座位选择页（区域tab+楼层切换+座位平面图+确认选座）
                                 参照 prototype/seat-select.html
pages/booking/confirm.vue      → 订单确认页（门店+座位信息+日期时段+费用明细+立即支付）
                                 参照 prototype/order-confirm.html
pages/orders/index.vue         → 我的预约列表（改造占位符）
                                 参照 prototype/orders.html
```

预约 tab 页 (`booking/index.vue`) 是核心交互页面，包含日期选择器、时段网格、区域筛选标签、座位平面图和底部操作栏。门店详情页提供另一种入口路径。

### 6. 前端预约流程

```
预约tab → 选择日期/时段 → 选择座位 → 点击"立即预约" → 确认页 → 提交
门店详情 → 点击"立即预约" → 座位选择页 → 点击"确认选座" → 确认页 → 提交
```

## Risks / Trade-offs

- **[并发预约冲突]** → 数据库层面增加 `(seat_id, date)` 索引加速查询，service 层使用 SELECT FOR UPDATE 加行锁
- **[座位数据生成]** → MVP 使用 seed 脚本为现有自习室生成模拟座位，后续可改为管理后台配置
- **[预约状态简化]** → MVP 不做自动 completed 转换，依赖用户手动或管理操作，后续可加定时任务
- **[原型一致性]** → UI 需严格参照 prototype，使用 Tailwind CSS 和主色 #4F6EF7
