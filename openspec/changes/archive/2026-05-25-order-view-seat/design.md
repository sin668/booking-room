## Context

当前 br-app 订单列表页（`pages/orders/index.vue`）已有"查看座位"按钮（仅 `status === 'confirmed'` 时显示），但点击后仅跳转到自习室详情页（`pages/booking/detail.vue`），无法定位到具体座位。座位选择页（`pages/booking/seat-select.vue`）是一个完整的交互式选座页面，包含日期选择、时段选择、区域切换和确认按钮，没有只读查看模式。

## Goals / Non-Goals

**Goals:**
- 点击"查看座位"后，跳转到座位布局图，预定的座位上显示小人图标
- 自动加载对应日期和时段的座位数据，无需用户手动选择
- 其他已占座位保持原有样式，可选座位正常显示但不响应点击

**Non-Goals:**
- 不修改后端 API
- 不创建新的独立页面（复用 seat-select 页面）
- 不支持查看非 confirmed 状态的订单座位

## Decisions

### 1. 复用 seat-select 页面而非新建页面

**选择**：在 seat-select.vue 中通过 URL 参数 `mode=view` 激活只读模式

**替代方案**：新建 `pages/booking/seat-view.vue` 独立页面

**理由**：座位布局渲染逻辑（区域分组、座位网格、样式计算）完全相同，新建页面会导致大量重复代码。通过 `mode` 参数切换模式，改动最小且维护成本低。

### 2. 通过 URL 参数传递查看模式

**选择**：`/pages/booking/seat-select?room_id=X&seat_id=Y&date=D&start_time=S&end_time=E&mode=view`

**理由**：uni-app 页面间传参的标准方式，无需引入额外状态管理。参数与预约确认页一致，保持 API 设计风格统一。

### 3. 预定座位显示小人图标

**选择**：在座位元素中显示一个 `🧑` 或小人 SVG 图标

**理由**：用户明确要求"像飞机选座一样有个小人站在对应座位上"，视觉直观明确。

### 4. viewMode 下隐藏交互元素

**选择**：隐藏日期选择器、时段选择器、区域筛选、底部确认栏

**理由**：查看模式下用户只需看到座位布局和自己的预定位置，这些交互元素不仅无意义还会造成困惑。保留区域 tab 切换，方便查看不同区域的座位分布。

## Risks / Trade-offs

- **[复用页面导致文件变大]** → seat-select.vue 逻辑增加但可控，viewMode 为纯条件分支，不会显著增加复杂度
- **[URL 参数长度]** → 参数数量较多但在微信小程序限制内（1024 字节），无风险
