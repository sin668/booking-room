## ADDED Requirements

### Requirement: Order list cancellation action
br-app 订单列表 SHALL 在已确认且可取消的预约单中，于“查看座位”按钮右侧展示“取消”按钮。点击“取消”后 SHALL 展示确认弹窗，说明退款将退回钱包，并在用户确认后调用取消预约 API。取消成功后 SHALL 刷新订单列表，订单状态显示为“已取消”，并展示退款结果提示。

#### Scenario: Display cancel button next to view seat
- **GIVEN** 用户进入订单列表
- **AND** 列表中存在状态为 "confirmed" 且 `can_cancel=true` 的预约
- **WHEN** 订单卡片渲染
- **THEN** “查看座位”按钮右侧显示“取消”按钮

#### Scenario: Hide cancel button for non-cancellable booking
- **GIVEN** 用户进入订单列表
- **AND** 列表中存在状态为 "cancelled"、"completed" 或 `can_cancel=false` 的预约
- **WHEN** 订单卡片渲染
- **THEN** 不显示“取消”按钮

#### Scenario: Confirm before cancellation
- **GIVEN** 订单卡片显示“取消”按钮
- **WHEN** 用户点击“取消”
- **THEN** 页面展示确认弹窗
- **AND** 弹窗说明取消后剩余金额退回钱包
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
- **AND** 对应订单状态显示为“已完成”

#### Scenario: Cancellation network failure
- **GIVEN** 用户确认取消
- **WHEN** 取消请求失败或网络异常
- **THEN** 页面展示“取消失败，请重试”提示
- **AND** 订单列表保持当前状态
