# TUIKit 产物瘦身与加载加速

## 动机

`br-app/src/TUIKit/index.ts` 无条件 `import { genTestUserSig } from './debug'`，将 147KB 的测试 UserSig 生成库（含加密 minified 库）打入 mp-weixin 产物。本系统 UserSig 由后端 API 下发，`genTestUserSig` 从未被调用。此外 `index.ts` 还导入了空壳 `index.vue` 和多个无外部消费者的组件引用，增加无意义的模块解析开销。

## 目标

- 删除 `debug/` 目录及其导入链（~160KB）
- 清理 `index.ts` 中所有无外部消费者的导入与导出
- 删除空壳 `index.vue` 和无用的 `vue.config.js`
- 不改变任何运行时行为

## 范围

- `br-app/src/TUIKit/index.ts` — 瘦身导入/导出
- `br-app/src/TUIKit/debug/` — 整目录删除
- `br-app/src/TUIKit/index.vue` — 删除
- `br-app/src/TUIKit/vue.config.js` — 删除
