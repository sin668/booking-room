## ADDED Requirements

### Requirement: Account security entries are actionable
设置页 SHALL 在“账号与安全”分组提供可操作的“修改密码”、“微信绑定”、“实名认证”和“注销账号”入口，不得继续只展示暂未开放提示。

#### Scenario: Open change password flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“修改密码”
- **THEN** 小程序 SHALL 打开修改密码表单
- **AND** 表单 SHALL 包含旧密码、新密码、确认新密码和提交按钮

#### Scenario: Open WeChat binding flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“微信绑定”
- **THEN** 小程序 SHALL 根据当前微信绑定状态展示已绑定信息或打开绑定流程

#### Scenario: Open identity verification flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“实名认证”
- **THEN** 小程序 SHALL 打开实名认证页面或弹层
- **AND** 页面 SHALL 展示实名状态、姓名输入、身份证号输入和提交按钮

#### Scenario: Open account deactivation flow
- **GIVEN** 用户已登录并打开“我的设置”页面
- **WHEN** 用户点击“注销账号”
- **THEN** 小程序 SHALL 打开注销账号说明页或确认弹层
- **AND** 页面 SHALL 展示注销影响、风险检查结果和二次确认操作

### Requirement: Account security statuses
设置页 SHALL 在账号与安全入口右侧展示当前状态摘要，便于用户判断是否已完成安全设置。

#### Scenario: Display security status summary
- **GIVEN** 用户已登录
- **WHEN** 设置页加载账号安全摘要成功
- **THEN** “微信绑定”行 SHALL 展示“已绑定”或“未绑定”
- **AND** “实名认证”行 SHALL 展示“已认证”或“未认证”
- **AND** “注销账号”行 SHALL 在账号已注销前保持可进入状态

#### Scenario: Fallback when security summary fails
- **GIVEN** 用户已登录
- **WHEN** 设置页加载账号安全摘要失败
- **THEN** 页面 SHALL 保持账号与安全入口可见
- **AND** 状态摘要 SHALL 展示为空或“--”
- **AND** 用户点击入口时 SHALL 重新尝试加载必要数据

### Requirement: Change password feedback
修改密码流程 SHALL 对前端校验和后端错误提供明确反馈。

#### Scenario: Reject mismatched new password confirmation
- **GIVEN** 用户正在修改密码
- **WHEN** 新密码和确认新密码不一致
- **THEN** 小程序 SHALL 阻止提交
- **AND** 展示“确认密码与新密码不一致”

#### Scenario: Show old password error
- **GIVEN** 用户正在修改密码
- **WHEN** 后端返回旧密码错误
- **THEN** 小程序 SHALL 保持表单可编辑
- **AND** 展示“原密码错误”

#### Scenario: Password changed successfully
- **GIVEN** 用户正在修改密码
- **WHEN** 后端确认密码修改成功
- **THEN** 小程序 SHALL 展示“密码已更新”
- **AND** 返回“我的设置”页面或关闭修改密码弹层

### Requirement: Identity verification feedback
实名认证流程 SHALL 对身份证号、姓名、提交状态和脱敏展示提供明确反馈。

#### Scenario: Reject invalid identity format
- **GIVEN** 用户正在实名认证
- **WHEN** 用户提交空姓名或格式错误的身份证号
- **THEN** 小程序 SHALL 阻止提交或展示后端错误
- **AND** 不得保存无效实名资料

#### Scenario: Show masked identity after submission
- **GIVEN** 用户提交实名认证资料成功
- **WHEN** 设置页重新加载
- **THEN** “实名认证”入口 SHALL 展示认证状态
- **AND** 实名详情 SHALL 只展示脱敏身份证号

### Requirement: Account deletion confirmation
注销账号流程 SHALL 在提交前展示风险检查和二次确认，提交成功后清除本地登录态。

#### Scenario: Block deactivation with unresolved risks
- **GIVEN** 用户打开注销账号流程
- **WHEN** 后端返回余额、未完成订单、未用卡券等阻断原因
- **THEN** 小程序 SHALL 展示阻断原因列表
- **AND** 不允许用户提交注销申请

#### Scenario: Submit account deletion
- **GIVEN** 用户无注销阻断风险
- **WHEN** 用户完成二次确认并提交注销
- **THEN** 小程序 SHALL 调用注销账号接口
- **AND** 成功后清除本地登录态并跳转登录页
