## MODIFIED Requirements

### Requirement: My bookings list page
系统 SHALL 将 br-app"订单"tab 页改造为我的预约列表页，参照 `prototype/orders.html`。每条记录展示门店名称、座位号、预约日期、时间段、状态标签（不同状态不同颜色）。支持按状态筛选，筛选项由 `constants/booking.js` 的 `BOOKING_TABS` 单一常量提供：全部（`all`）/待开始（`pending_start`）/进行中（`in_progress`）/已完成（`completed`）/已取消（`cancelled`）。进行中状态的订单 SHALL 显示"查看座位"按钮，点击后跳转到座位选择页的只读查看模式。对于 `can_cancel=true` 的进行中订单，页面 SHALL 在“查看座位”按钮右侧展示“取消”按钮。

**展示状态直接消费后端 `status`**：重命名后展示状态与落库状态为恒等映射，页面内 `displayStatus(order)` 的四个派生分支（`pending_confirm` 自映射、`pending + paid → pending_start`、课程 `confirmed → in_progress`、座位 `confirmed + now >= bookingStart → in_progress`）返回值全部等于 `order.status`，该函数 SHALL 被删除，模板与按钮判定 SHALL 直接引用 `order.status`。`statusLabel(order)` 中「自习室预约订单的已确认状态统一显示进行中」的特例分支（`ds === 'confirmed'`）SHALL 一并删除。

**「待支付」标签改由支付域派生**：`BOOKING_STATUS_LABELS.pending = '待支付'` 承载的是支付域语义。重命名后 `status` 不再出现 `pending` 值，若直接删除该键，未支付订单（`status='pending_start'` + `payment_status='pending'`）的标签会从「待支付」退化为「待开始」，与其卡片上的「去支付」按钮语义矛盾。为保持用户可见文案零变更，`statusLabel(order)` SHALL 增加 `payment_status === 'pending'` → 返回「待支付」的前置分支，`BOOKING_STATUS_LABELS` 中的 `pending` 与 `confirmed` 两个旧词表键 SHALL 被删除。

**死代码清理**：页面内的局部常量 `TABS`、`STATUS_MAP`、`ZONE_MAP` 各自只有定义处一次命中、零消费方（页面实际使用导入的 `BOOKING_TABS` 与 `SEAT_ZONE_LABELS`），SHALL 被删除。其中 `STATUS_MAP.pending='待确认'` 与 `BOOKING_STATUS_LABELS.pending='待支付'` 属互相矛盾的文案，随死代码一并消灭。

**重复派生收敛**：`isOrderStarted(order)` 与 `isOrderPendingStart(order)` 与 `displayStatus` 语义重叠，构成 br-app 内的第 2、3 份状态派生实现。`isOrderStarted` 中 `order.status === 'in_progress'` 分支在重命名前永不成立（后端不返回该值），`order.started === true` 仅对课程订单有值（座位订单为 `null`）。重构 SHALL 将这两个方法收敛为对 `order.status` 的直接判定，SHALL NOT 保留对旧词表字面量的比较。

#### Scenario: Display bookings on orders tab
- **WHEN** 用户点击底部"订单" tab
- **THEN** 页面展示预约记录列表，每条记录包含门店名称、座位号、日期、时间段、状态标签

#### Scenario: Filter tabs use the renamed vocabulary
- **WHEN** 订单页渲染顶部筛选标签
- **THEN** 标签项 SHALL 依次为「全部」「待开始」「进行中」「已完成」「已取消」
- **AND** 对应请求参数值 SHALL 为 `all`、`pending_start`、`in_progress`、`completed`、`cancelled`
- **AND** SHALL NOT 出现取值为 `confirmed` 或 `pending` 的筛选项

#### Scenario: Filter by status
> 标题沿用主 spec 原名（MODIFIED 整块替换语义要求）。主 spec 原写“选择‘已确认’→ 仅显示 `confirmed`”；旧状态值 `confirmed` 已重命名为 `in_progress`，标签文案改为“进行中”。另：主 spec 原描述为纯列匹配，实测为**后端派生口径**（附加 `payment_status='paid'`），该口径本次 SHALL 保持不变。
- **WHEN** 用户点击顶部筛选标签选择"进行中"
- **THEN** 列表仅显示按后端派生口径返回的 `in_progress` 预约记录
- **AND** 请求参数为 `?status=in_progress`

#### Scenario: Filter by pending-start status
- **WHEN** 用户点击顶部筛选标签选择"待开始"
- **THEN** 列表显示后端派生口径返回的预约记录（含 `pending_start` 与 `pending_confirm` 且已支付）
- **AND** 请求参数为 `?status=pending_start`

#### Scenario: Empty bookings state
- **WHEN** 用户没有任何预约记录
- **THEN** 显示空状态提示"暂无预约记录"，并提供"去预约"按钮跳转到预约页

#### Scenario: Booking status display
- **WHEN** 预约列表中存在不同状态的已支付记录
- **THEN** `in_progress` 显示"进行中"标签，`pending_start` 显示"待开始"标签，`pending_confirm` 显示"待确认"标签，`completed` 显示"已完成"标签，`cancelled` 显示"已取消"标签

#### Scenario: Unpaid booking shows pending-payment label
- **GIVEN** 订单列表中存在一笔 `status='pending_start'` 且 `payment_status='pending'` 的预约
- **WHEN** 订单卡片渲染状态标签
- **THEN** 标签文字 SHALL 为"待支付"
- **AND** 该文案 SHALL 由 `payment_status` 派生，而非由 `status` 查表得到
- **AND** 该行为 SHALL 与重命名前完全一致

#### Scenario: Display status is consumed directly from backend
- **WHEN** 订单卡片渲染状态标签或决定按钮可见性
- **THEN** SHALL 直接引用 `order.status`
- **AND** 页面内 SHALL NOT 存在 `displayStatus()` 派生函数

#### Scenario: Dead local constants are removed
- **WHEN** 重构完成后检查 `pages/orders/index.vue`
- **THEN** SHALL NOT 存在局部常量 `TABS`、`STATUS_MAP`、`ZONE_MAP` 的定义
- **AND** 筛选标签与座位区域文案 SHALL 分别来自导入的 `BOOKING_TABS` 与 `SEAT_ZONE_LABELS`

#### Scenario: View seat from confirmed order
> 标题沿用主 spec 原名；旧状态值 `confirmed` 已重命名为 `in_progress`。
- **GIVEN** 订单列表中存在 `status` 为 "in_progress" 的订单
- **WHEN** 用户点击"查看座位"按钮
- **THEN** 跳转到座位选择页，传递 `room_id`、`seat_id`、`date`、`start_time`、`end_time`、`mode=view` 参数

#### Scenario: View seat button hidden for non-confirmed orders
> 标题沿用主 spec 原名；旧状态值 `confirmed` 已重命名为 `in_progress`。
- **GIVEN** 订单列表中存在 `status` 为 "cancelled" 或 "completed" 的订单
- **WHEN** 订单卡片渲染
- **THEN** 不显示"查看座位"按钮

#### Scenario: Display cancel button next to view seat
- **GIVEN** 用户进入订单列表
- **AND** 列表中存在状态为 "in_progress" 且 `can_cancel=true` 的预约
- **WHEN** 订单卡片渲染
- **THEN** “查看座位”按钮右侧显示“取消”按钮

#### Scenario: Hide cancel button for non-cancellable booking
- **GIVEN** 用户进入订单列表
- **AND** 列表中存在状态为 "cancelled"、"completed" 或 `can_cancel=false` 的预约
- **WHEN** 订单卡片渲染
- **THEN** 不显示“取消”按钮

#### Scenario: Hide action buttons for unpaid booking
- **GIVEN** 列表中存在 `payment_status='pending'`（待支付）的预约
- **WHEN** 订单卡片渲染
- **THEN** SHALL NOT 显示“查看座位”与“取消”按钮
- **AND** SHALL 显示“去支付”入口

#### Scenario: Confirm before cancellation
- **GIVEN** 订单卡片显示“取消”按钮
- **WHEN** 用户点击“取消”
- **THEN** 页面展示确认弹窗
- **AND** 弹窗说明取消后剩余金额退回钱包
- **AND** 如果本次取消需要扣款，弹窗展示扣款金额提醒
- **AND** 用户可选择确认或放弃

#### Scenario: Submit cancellation after confirmation
- **GIVEN** 用户已打开取消确认弹窗
- **WHEN** 用户确认取消
- **THEN** 前端调用 `POST /api/v1/bookings/{booking_id}/cancel/`
- **AND** 取消请求进行中时禁用重复点击

#### Scenario: Cancellation success updates order list
- **GIVEN** 用户确认取消且后端返回 HTTP 200
- **WHEN** 前端收到取消结果
- **THEN** 页面提示取消成功及退款金额
- **AND** 刷新订单列表
- **AND** 对应订单状态显示为“已取消”
- **AND** 不再展示“取消”按钮

#### Scenario: Cancellation rejected because booking started
- **GIVEN** 用户确认取消
- **WHEN** 后端返回预约已开始不可取消错误
- **THEN** 页面展示不可取消提示
- **AND** 刷新订单列表
- **AND** 对应订单状态按后端返回值展示：处于「已开始但未结束」窗口时显示“进行中”，已过结束时间时显示“已完成”

#### Scenario: Cancellation network failure
- **GIVEN** 用户确认取消
- **WHEN** 取消请求失败或网络异常
- **THEN** 页面展示“取消失败，请重试”提示
- **AND** 订单列表保持当前状态
