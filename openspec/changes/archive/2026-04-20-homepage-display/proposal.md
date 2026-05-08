## Why

系统当前首页仅有简单的登录/登出功能，用户登录后无法浏览自习室、查看快捷入口或进行任何有意义的操作。首页是用户进入小程序的第一触点，需要展示核心信息并引导用户进入预约流程，这是 V1 版本的基础功能。

## What Changes

- 新建首页 UI：顶部导航栏（定位+搜索+通知）、轮播图运营位、快捷入口（钱包充值/卡券套餐/美团兑换/个人码）、学习码卡片、热门活动列表、推荐自习室列表
- 新增自习室列表接口：后端提供自习室数据查询 API
- 新增轮播图接口：后端提供运营位数据 API（含标题/副标题/CTA 按钮文案）
- 新增热门活动接口：后端提供活动数据查询 API
- 完善底部 TabBar：首页、预约、订单、我的四个 Tab

## Capabilities

### New Capabilities
- `homepage-ui`: 首页界面展示，包括顶部导航栏、轮播图、快捷入口、学习码卡片、热门活动、自习室列表、TabBar 导航
- `study-room-list`: 自习室列表数据查询接口
- `banner-management`: 轮播图/运营位数据接口
- `activity-list`: 热门活动数据查询接口

### Modified Capabilities

（无已有 capability 需要修改）

## Impact

- **br-app**: 新增/重写 `pages/index/index.vue`，新增首页相关组件（导航栏、轮播、快捷入口、学习码卡片、活动卡片、自习室卡片），配置 `pages.json` TabBar（4 Tab），新增占位页面（预约、订单）
- **br-server**: 新增自习室/Banner/Activity Model，新增 API 路由 `/api/v1/rooms/`、`/api/v1/banners/`、`/api/v1/activities/`，新增数据库迁移
- **数据库**: 新增 `study_rooms`、`banners`、`activities` 表
- **回滚方案**: 删除新增的 API 路由和 Model，撤销数据库迁移，首页恢复为当前简单版本
