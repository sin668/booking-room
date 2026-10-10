# Design: TUIKit 产物瘦身

## 决策 1：只保留 `TUIChatKit` 导出

外部消费者（`entry-chat-only.ts`、`entry.ts`）只 import `TUIChatKit`。其余导出（`TUIKit`、`TUIComponents`、`TUIChat`、`TUIConversation`、`TUIContact`、`TUISearch`、`TUIGroup`、`hideTUIChatFeatures`、`genTestUserSig`）均无外部消费者。组件通过 uni-app 页面路由加载，不走 JS import。

**决定**：`index.ts` 只保留 `Server` 导入和 `TUIChatKit` 导出，删除所有其他导入和导出。

## 决策 2：删除 debug 目录而非条件导入

条件导入（`import.meta.env.DEV && ...`）仍会把库留在产物里（tree-shaking 不可靠）。该库完全无用，直接删除。

## 决策 3：不触碰组件内部代码

组件目录虽然大，但都是 uni-app 页面路由实际加载的，不能删。本次只清理入口文件的死导入。
