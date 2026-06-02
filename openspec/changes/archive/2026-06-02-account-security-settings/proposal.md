## Why

“我的设置”里账号与安全分组目前只有占位提示，用户无法在小程序内完成关键账号安全操作。需要补齐修改密码、微信绑定、实名认证和注销账号能力，降低客服介入成本，并为余额、预约、支付等资产相关操作提供更完整的账号安全基础。

## What Changes

- 在小程序“我的设置 > 账号与安全”中实现四个可用入口：修改密码、微信绑定、实名认证、注销账号。
- 增加当前用户安全信息读取能力，用于展示手机号、微信绑定状态、实名状态、注销状态等安全摘要。
- 增加当前用户修改密码接口，要求校验旧密码，并在成功后维持或刷新登录态。
- 扩展微信绑定体验：支持展示绑定状态、从设置页发起绑定、处理已绑定/冲突/未配置等状态。
- 增加实名认证资料提交与状态查询能力，保存真实姓名、身份证号脱敏信息和认证状态。
- 增加账号注销能力，要求风险校验，阻止有未完成订单、余额、未用卡券等资产风险的账号注销；校验通过后不物理删除用户，而是设置 `status='deleted'`。
- 不包含外部实名核验供应商接入；本期按“提交资料后直接进入已认证状态”的产品闭环设计，保留后续接入外部核验的接口边界。
- 回滚方案：前端可隐藏账号与安全新入口或恢复占位提示；后端新增接口可下线路由，实名认证新增结构可保留不影响旧流程，必要时通过 Alembic downgrade 移除新增实名结构和 `deleted` 状态约束变更。

## Capabilities

### New Capabilities

<!-- No new standalone capability. This change extends existing profile, auth, settings UI, and WeChat binding capabilities. -->

### Modified Capabilities

- `profile-settings-ui`: 设置页账号与安全分组从占位提示升级为可操作的修改密码、微信绑定、实名认证和注销账号流程。
- `user-profile-api`: 当前用户资料 API 增加账号安全摘要、实名资料状态、账号注销风险检查和注销操作接口。
- `user-auth`: 增加已登录用户修改密码和 `deleted` 状态账号禁止继续登录的认证安全要求。
- `wechat-phone-binding`: 扩展设置页微信绑定状态展示、发起绑定和冲突反馈要求。

## Impact

- 影响移动端 `br-app/src/pages/settings/index.vue` 及必要的账号安全子页面/弹层、`br-app/src/api/*`、用户 store 和错误提示映射。
- 影响后端 `br-server/app/api/routes/user.py` 或新增当前用户安全路由、`br-server/app/services/user_profile_service.py`、认证服务、用户模型、Pydantic schemas 和 Alembic 迁移。
- 影响 PostgreSQL 用户相关数据结构：新增实名认证记录表，并扩展用户状态支持 `deleted`；不新增注销申请表，不物理删除用户。
- 影响测试：需要补充 API 集成测试、服务单元测试和前端逻辑脚本测试，覆盖成功、未登录、旧密码错误、微信绑定冲突、实名格式错误、注销风险阻断等路径。
- 不引入新的第三方依赖；实名认证外部核验和注销冷静期自动任务留作后续扩展。
