# Tasks: 会话 TAB 显示对方在本系统的头像与昵称

## 1. IM 用户画像写入能力

- [x] 1.1 在 `br-app/src/utils/im.js` 引入 `TUIUserService`，新增 `setIMProfile(profile)`：缓存资料，IM 已就绪则立即推送，未就绪时由 `ensureIM()` 登录成功后补推
- [x] 1.2 推送时只携带非空的 `nick`/`avatar`，两者皆空直接跳过；调用失败仅告警，不影响 `ensureIM()` 返回就绪
- [x] 1.3 保持 `utils/im.js` 不 import pinia store，避免与 `store/modules/user.js` 形成循环依赖

## 2. 用本系统资料驱动同步

- [x] 2.1 `br-app/src/store/modules/user.js` 的 `fetchUserInfo()` 在写入 `userInfo` 后调用 `setIMProfile({ nick: nickname, avatar })`
- [x] 2.2 `updateProfile()` 在保存成功后同样调用 `setIMProfile`，保证用户改昵称/头像后对方可见

## 3. 自检与构建

- [x] 3.1 新增 `br-app/scripts/verify-im-peer-profile.js`，断言画像写入链路（setter、空值过滤、store 两处触发、无反向 import、会话行仍走 `getAvatar()` + 首字母兜底、未读依赖 `TUIStore.watch` 与 `onShow` 重拉），并在 `br-app/package.json` 注册脚本、并入 `test:scripts`
- [x] 3.2 执行 `node scripts/verify-im-peer-profile.js` 与 `npm run build:mp-weixin`，确认构建通过且产物包含 `updateMyProfile` 调用
