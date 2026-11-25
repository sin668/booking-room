## 1. 主题基础设施（br-app）

- [x] 1.1 `src/uni.scss`：语义色改为 `var(--token)` 间接引用，新增 `--bg-hero`、`--surface-muted`，`$white` 保持字面量 <!-- comet-task:61f17959-304c-462e-a29b-6d5f6279505a -->
- [x] 1.2 `src/App.vue`：全局定义浅色/深色两套 token，并在 `onLaunch` 初始化主题与原生配色 <!-- comet-task:ea58b241-6592-4d8d-bb22-b8cbcae2844e -->
- [x] 1.3 新增 `src/store/modules/theme.js`（状态、持久化、原生 UI 同步）与 `src/utils/theme.js`（`themeClass` mixin），在 `src/main.js` 注册 <!-- comet-task:3c66b8bb-fa63-450d-a263-832345f52479 -->

## 2. 页面接入

- [x] 2.1 除 `src/TUIKit/**` 外的 35 个页面根节点追加 `:class="themeClass"` <!-- comet-task:af09cb96-ab5d-45e1-ab2b-0721321e01db -->
- [x] 2.2 设置页「通用 - 深色模式」开关改为读写 theme store，并清理本页硬编码色值 <!-- comet-task:1a8791f2-b1d6-479a-8122-36d0d601b53d -->

## 3. 页面色值适配

- [x] 3.1 处理硬编码最多的页面：`notifications`、`certification`（4 页）、`training/course-booking`、`booking/seat-select`、`pages/index`、`booking/detail` <!-- comet-task:5a8b1969-d912-4270-8403-4392603e8cc2 -->
- [x] 3.2 其余页面硬编码背景/文本/边框改为 token 或半透明色，页面顶部渐变写死的 `#fff`/`#eef1fb` 一并 token 化 <!-- comet-task:b3a1cbda-1833-4a12-8b6e-0dd2c414c820 -->
- [x] 3.3 拆分 `$white` 双语义：背景与切割边框改 `$surface`/`$bg-color`，前景白保持不变 <!-- comet-task:bf70a05a-9d2f-4cb0-aa8b-9d1acf548150 -->

## 4. 验证与交付

- [x] 4.1 `npm run build:mp-weixin` 通过 <!-- comet-task:0bb7f376-448d-4662-bd57-7769c552a1c8 -->
- [x] 4.2 `npm run build:h5` 通过 <!-- comet-task:4be04360-5648-4008-b2e4-5acc7fa81479 -->
- [x] 4.3 `npm run test:dark-mode` 通过；`npm run test:scripts` 的存量失败（HEAD 同样失败）已记录，不计入本变更 <!-- comet-task:d4173493-d465-49f9-aa4f-9c0650f707cf -->
- [ ] 4.4 提交并推送 origin main <!-- comet-task:3aaa28d0-3106-4467-bc53-6fe2f22e39a0 -->
