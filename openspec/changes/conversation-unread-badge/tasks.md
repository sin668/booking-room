# Tasks: conversation-unread-badge

- [x] 1. 在 `br-app/src/TUIKit/components/TUIChat/index.vue` 的 `onUnload` 中清除当前会话（调用 `reset()`），保留 `onUnmounted` 原有 `reset()`
- [x] 2. 扩展 `br-app/scripts/verify-im-peer-profile.js`：断言 `onUnload` 内清除当前会话、`onUnmounted` 仍清除
- [x] 3. 运行自检脚本与 `npm run build:mp-weixin`，确认产物编译通过，并在产物中核实 `onUnload` 调用了 `switchConversation("")`
- [x] 4. 登记 Comet 证据并通过 build/verify 守卫
