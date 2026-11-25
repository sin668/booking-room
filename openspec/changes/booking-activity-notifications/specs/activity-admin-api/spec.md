## ADDED Requirements

### Requirement: Activity save triggers broadcast notification

管理端新建或编辑活动保存成功后，若活动发布状态为已上架（`is_active=true`）且存在关联卡券，系统 SHALL 触发一次活动群发通知。

#### Scenario: Create published activity with coupons
- **WHEN** 管理员创建活动，`is_active=true` 且提交了 `activity_coupons`
- **THEN** 活动保存成功
- **AND** 系统 SHALL 调用公共发送消息方法向全部 App 用户群发该活动消息

#### Scenario: Update activity to published with coupons
- **GIVEN** 活动已存在
- **WHEN** 管理员编辑活动并保存，保存后 `is_active=true` 且活动关联卡券
- **THEN** 系统 SHALL 触发活动群发通知

#### Scenario: Save unpublished or coupon-less activity
- **WHEN** 管理员保存 `is_active=false` 的活动，或活动没有关联卡券
- **THEN** 系统 SHALL NOT 触发活动群发通知
- **AND** 活动保存结果 SHALL 保持正常

#### Scenario: Broadcast failure does not roll back activity save
- **GIVEN** 活动保存成功但群发过程出现异常
- **WHEN** 管理端收到保存结果
- **THEN** 活动数据 SHALL 保持已保存状态
- **AND** 系统 SHALL 记录群发失败日志
