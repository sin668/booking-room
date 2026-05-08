## 1. 数据库 & 数据模型

- [x] 1.1 创建 `Banner` SQLAlchemy 模型（banners 表：id, image_url, title, subtitle, cta_text, link_type, link_value, sort_order, is_active, created_at, updated_at）
- [x] 1.2 创建 `Activity` SQLAlchemy 模型（activities 表：id, title, description, cover_image, participant_count, sort_order, is_active, created_at, updated_at）
- [x] 1.3 创建 `StudyRoom` SQLAlchemy 模型（study_rooms 表：id, name, description, cover_image, address, business_hours, status, min_price, created_at, updated_at）
- [x] 1.4 创建 Alembic 迁移脚本，生成 banners、activities、study_rooms 表
- [x] 1.5 编写种子数据脚本，插入 2 条轮播图、4 个活动、3 个自习室示例数据

## 2. 后端 API

- [x] 2.1 创建 Banner Pydantic schema（BannerResponse，含 title/subtitle/cta_text 字段）
- [x] 2.2 创建 Activity Pydantic schema（ActivityResponse）
- [x] 2.3 创建 StudyRoom Pydantic schemas（StudyRoomResponse, StudyRoomListResponse）
- [x] 2.4 创建 Banner service：查询 is_active=true 的轮播图，按 sort_order 升序
- [x] 2.5 创建 Activity service：查询 is_active=true 的活动，按 sort_order 升序
- [x] 2.6 创建 StudyRoom service：分页查询 status=open 的自习室列表
- [x] 2.7 创建 `GET /api/v1/banners/` 路由
- [x] 2.8 创建 `GET /api/v1/activities/` 路由
- [x] 2.9 创建 `GET /api/v1/rooms/` 路由（支持 page, page_size 参数，page_size 最大 50）
- [x] 2.10 编写 Banner API 单元测试
- [x] 2.11 编写 Activity API 单元测试
- [x] 2.12 编写 StudyRoom API 单元测试
- [x] 2.13 编写 API 集成测试

## 3. 前端 API 层

- [x] 3.1 创建 `br-app/api/banners.js`，封装轮播图接口调用
- [x] 3.2 创建 `br-app/api/activities.js`，封装热门活动接口调用
- [x] 3.3 创建 `br-app/api/rooms.js`，封装自习室列表接口调用（含分页参数）

## 4. 前端首页 UI

- [x] 4.1 配置 `pages.json` TabBar（4 个 Tab：首页、预约、订单、我的）
- [x] 4.2 创建预约页和订单页占位页面（`pages/booking/index.vue`、`pages/orders/index.vue`）
- [x] 4.3 重写 `pages/index/index.vue`：页面布局（导航栏 + 轮播图 + 快捷入口 + 学习码卡片 + 热门活动 + 自习室列表）
- [x] 4.4 实现顶部导航栏组件：城市定位 + 搜索框 + 通知铃铛
- [x] 4.5 实现轮播图组件：调用 banners API，展示标题/副标题/CTA 按钮，3.5 秒自动轮播，手势滑动，圆点指示器，处理点击跳转
- [x] 4.6 实现快捷入口网格：4 个圆形图标入口（钱包充值、卡券套餐、美团兑换、个人码）
- [x] 4.7 实现学习码卡片：渐变背景（primary → purple），标题+副标题+二维码占位图标
- [x] 4.8 实现热门活动列表：2×2 网格卡片，调用 activities API
- [x] 4.9 实现自习室列表卡片组件：展示封面图、名称、地址、营业状态、最低价格
- [x] 4.10 实现分页功能：下拉刷新 + 上拉加载更多
- [x] 4.11 实现加载状态：骨架屏 / loading 占位
- [x] 4.12 实现空状态：列表为空时展示占位图和提示文案
- [x] 4.13 实现错误处理：单个接口失败不影响其他模块展示

## 5. 集成与收尾

- [x] 5.1 API 文档更新（docs/api.md 补充新增的相关接口）
- [x] 5.2 代码审查与重构（确保 Clean Architecture 分层、消除重复代码）
- [x] 5.3 全量测试通过（单元测试 + 集成测试，覆盖率 > 90%）
