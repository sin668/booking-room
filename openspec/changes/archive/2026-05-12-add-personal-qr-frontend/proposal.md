## Why

用户到店后需要快速出示个人学习码，由门店工作人员扫码查看预约信息并完成核销。当前原型只有“我的学习码”视觉页面，缺少动态二维码、扫码展示 booking 信息、员工确认核销和后端状态变更，无法形成真实到店核销闭环。

## What Changes

- 新增用户端个人学习码页面，参考 `prototype/qrcode.html` 高保真原型展示用户信息、动态二维码、当前可核销预约摘要和安全提示。
- 新增后端核销码能力：用户登录后为当前可核销 booking 签发 5 分钟有效、不可伪造的动态 token。
- 新增员工扫码 H5 核销页：微信扫一扫打开 `verify_url`，员工登录后查看 booking 信息并点击“确认核销”。
- 新增后端核销 API：解析 token、校验权限和 booking 状态，将 `confirmed` booking 核销为 `completed`。
- 在移动端 `pages.json` 注册个人学习码页面和员工 H5 核销页面路由。
- 在个人中心增加“我的学习码”入口。
- 将原型中的“保存到相册/分享给好友”调整为非核心能力；动态核销码优先提供倒计时、刷新和错误兜底，避免误导用户保存过期码。

## Capabilities

### New Capabilities

- `personal-qr-ui`: 用户端个人学习码页面与入口，包括动态二维码展示、当前 booking 摘要、倒计时刷新、未登录和无可核销预约兜底。
- `booking-verification-api`: 后端 booking 核销码 API，包括 token 签发、token 解析、员工确认核销和状态保护。
- `booking-verification-ui`: 员工扫码 H5 核销页，包括 booking 信息展示、权限/错误态处理和确认核销操作。

### Modified Capabilities

（无需修改现有 spec 的需求定义）

## Impact

- **br-app**: 新增 `src/pages/qrcode/index.vue` 用户端二维码页面；新增 `src/pages/verify-booking/index.vue` 员工 H5 核销页；修改 `src/pages.json` 注册路由；修改 `src/pages/profile/index.vue` 增加入口；新增二维码生成和核销 API 前端封装。
- **br-server**: 新增 booking verification schemas、service、routes；复用现有 `bookings`、`seats`、`study_rooms` 数据；新增确认核销状态流转 `confirmed -> completed`。
- **docs/api.md**: 补充 booking verification 相关接口文档。
- **prototype**: 以 `prototype/qrcode.html` 为用户端页面视觉参考，不改动原型文件。
- **安全/权限**: token 由后端签发，5 分钟有效；解析和确认核销要求员工/管理员权限；确认核销时后端二次校验 token、booking 状态和权限。
- **回滚方案**: 删除新增核销 API、schemas、service、routes 和测试；删除新增前端页面/API 封装；移除 `pages.json` 路由注册和个人中心入口；回退 `docs/api.md` 新增接口文档即可完全回滚。
