## ADDED Requirements

### Requirement: Homepage top navigation bar
首页 SHALL 展示固定顶部导航栏，包含三个区域：左侧城市定位（显示当前城市名+下拉箭头图标，可点击切换城市）、中间搜索框（灰色背景圆形搜索框，显示"搜索自习室"占位文案，点击跳转搜索页面）、右侧通知铃铛（带红色未读提示点）。导航栏背景为白色，固定在页面顶部。

#### Scenario: Display navigation bar
- **WHEN** 用户进入首页
- **THEN** 顶部展示白色导航栏，左侧显示城市定位"茂名市"+下拉箭头，中间显示"搜索自习室"搜索框，右侧显示通知铃铛图标

#### Scenario: Tap search bar
- **WHEN** 用户点击中间搜索框
- **THEN** 系统跳转到搜索页面（V1 暂为占位页面）

#### Scenario: Tap notification bell
- **WHEN** 用户点击通知铃铛
- **THEN** V1 不执行任何操作，铃铛仅做展示（后续版本实现通知功能）

### Requirement: Homepage carousel display
首页 SHALL 展示轮播图区域，从后端 `/api/v1/banners/` 接口获取数据，自动轮播，间隔 3.5 秒。仅展示 `is_active=true` 且按 `sort_order` 升序排列的轮播图。每张轮播图 SHALL 展示：底部渐变遮罩层、标题文字、副标题文字、CTA 按钮（圆角胶囊按钮）。支持手势左右滑动切换，底部展示圆点指示器（当前项为长条蓝色，其余为短条灰色）。点击 CTA 按钮根据 `link_type` 执行跳转：`page` 跳转小程序页面，`room` 跳转自习室详情，`none` 不跳转。

#### Scenario: Display active banners with overlay
- **WHEN** 用户进入首页且后端返回 3 条 `is_active=true` 的轮播图（含 title/subtitle/cta_text）
- **THEN** 首页按 `sort_order` 升序展示 3 张轮播图，每张有底部渐变遮罩、标题、副标题和 CTA 按钮，自动轮播间隔 3.5 秒

#### Scenario: Swipe to change banner
- **WHEN** 用户在轮播图区域左滑
- **THEN** 系统切换到下一张轮播图，圆点指示器同步更新

#### Scenario: Click CTA button with page link
- **WHEN** 用户点击 `link_type=page` 的轮播图 CTA 按钮
- **THEN** 系统跳转到 `link_value` 指定的页面

#### Scenario: Click CTA button with no link
- **WHEN** 用户点击 `link_type=none` 的轮播图 CTA 按钮
- **THEN** 系统不执行任何跳转操作

#### Scenario: No active banners
- **WHEN** 后端返回空的轮播图列表
- **THEN** 首页不展示轮播图区域，不影响其他模块显示

### Requirement: Homepage quick entry grid
首页 SHALL 展示快捷入口网格，4 列布局，每项包含圆形图标背景和文字标签。V1 固定 4 个入口：钱包充值（蓝色钱包图标）、卡券套餐（橙色票券图标）、美团兑换（绿色礼物图标）、个人码（紫色二维码图标）。点击各入口跳转到对应页面（V1 暂为占位页面）。

#### Scenario: Display quick entries
- **WHEN** 用户进入首页
- **THEN** 首页展示 4 个快捷入口图标，横向等分排列，每个图标下方有对应文字标签

#### Scenario: Tap quick entry
- **WHEN** 用户点击"钱包充值"快捷入口
- **THEN** 系统跳转到钱包充值页面（V1 暂为占位页面）

### Requirement: Homepage study code card
首页 SHALL 展示学习码入口卡片，使用主色到紫色的渐变背景（`#4F6EF7` → `#6C5CE7`），圆角卡片样式。左侧展示标题"我的学习码"、副标题"到店出示即可核销"、操作文字"立即查看 >"，右侧展示虚线边框的二维码图标占位。点击卡片跳转到个人二维码页面。

#### Scenario: Display study code card
- **WHEN** 用户进入首页
- **THEN** 首页展示渐变背景的学习码卡片，包含标题、副标题和二维码图标

#### Scenario: Tap study code card
- **WHEN** 用户点击学习码卡片
- **THEN** 系统跳转到个人二维码页面

### Requirement: Homepage hot activities section
首页 SHALL 展示"热门活动"区域，标题"热门活动"+ 右侧"查看更多"链接。活动列表为 2×2 网格布局，每个活动卡片包含：封面图（等比裁切）、活动标题、活动描述（单行截断）、参与人数（如"已有326人参与"）。数据从后端 `/api/v1/activities/` 接口获取。

#### Scenario: Display hot activities
- **WHEN** 用户进入首页且后端返回 4 个活动
- **THEN** 首页展示 2×2 网格的活动卡片，每个卡片含封面图、标题、描述和参与人数

#### Scenario: No activities
- **WHEN** 后端返回空的活动列表
- **THEN** 首页不展示热门活动区域

### Requirement: Homepage study room list
首页 SHALL 展示自习室列表区域（位于热门活动下方），从后端 `/api/v1/rooms/` 接口分页获取数据。每个自习室卡片展示：封面图、名称、地址、营业状态（营业中/已打烊）、最低价格。列表支持下拉刷新和上拉加载更多。

#### Scenario: Display study room cards
- **WHEN** 用户进入首页且后端返回自习室列表
- **THEN** 首页展示自习室卡片列表，每张卡片包含封面图、名称、地址、营业状态标签和最低价格

#### Scenario: Pull down to refresh
- **WHEN** 用户在首页下拉刷新
- **THEN** 系统重新请求第一页自习室列表数据并更新显示

#### Scenario: Pull up to load more
- **WHEN** 用户在列表底部上拉触底
- **THEN** 系统请求下一页数据并追加到列表中

#### Scenario: Empty room list
- **WHEN** 后端返回空的自习室列表
- **THEN** 首页展示空状态占位图和"暂无自习室"提示文案

### Requirement: Homepage TabBar navigation
应用 SHALL 配置底部 TabBar，包含四个 Tab：首页（首页图标）、预约（日历图标）、订单（收据图标）、我的（用户图标）。首页 Tab 默认选中。TabBar 使用原生配置，底部包含 iOS 安全区适配。

#### Scenario: Switch tab to homepage
- **WHEN** 用户点击底部"首页"Tab
- **THEN** 系统切换到首页 `/pages/index/index` 并高亮"首页"Tab

#### Scenario: Switch tab to booking
- **WHEN** 用户点击底部"预约"Tab
- **THEN** 系统切换到预约页面（V1 占位页）并高亮"预约"Tab

#### Scenario: Switch tab to orders
- **WHEN** 用户点击底部"订单"Tab
- **THEN** 系统切换到订单页面（V1 占位页）并高亮"订单"Tab

#### Scenario: Switch tab to profile
- **WHEN** 用户点击底部"我的"Tab
- **THEN** 系统切换到个人中心页面并高亮"我的"Tab

### Requirement: Homepage loading state
首页 SHALL 在数据加载中展示骨架屏或 loading 占位，加载完成后显示实际内容。单个模块请求失败不影响其他模块展示。

#### Scenario: Loading state display
- **WHEN** 用户进入首页且数据尚未返回
- **THEN** 轮播图区域、活动区域和列表区域分别展示对应的骨架屏/loading 状态

#### Scenario: Partial API failure
- **WHEN** 轮播图接口返回错误但自习室列表接口正常返回
- **THEN** 轮播图区域隐藏或展示错误占位，自习室列表正常展示
