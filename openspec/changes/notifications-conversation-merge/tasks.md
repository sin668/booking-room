# Tasks: 会话并入全部收件箱 + 头像回退 + 铃铛计入会话未读

- [x] message-bubble.vue：`flow==='in'` 且头像为空或等于自己头像时回退默认头像
- [x] notifications/index.vue：「全部」TAB 顶部增加「会话」聚合行（话/会话 + 时间 + 无数字红点），点击进入会话 TAB；全部 TAB 也订阅会话列表
- [x] index/index.vue：铃铛 `hasNotification` 合并 IM `totalUnreadCount`，onShow 订阅、onHide/onUnload 取消
- [x] 扩展 `scripts/verify-im-peer-profile.js` 断言三处改动
- [x] 构建 mp-weixin 通过、断言脚本通过，提交推送 main
