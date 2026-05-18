# 项目上下文

## 目的 
项目名叫“好好学习”，这是一个共享自习室预约系统，项目模仿了“茂名去K书”微信小程序的界面风格（主题色除外），实现了首页、预约、个人中心等核心模块。

## 技术栈

### 前端(br-app) 
- 前端框架：uni-app（Vue3）
- CSS 框架：ailwindCSS
- UI库：uView 2.0
- 状态管理：Vuex

### WEB PC管理后台(br-admin)
- Vue3 
- Naive UI
- Vite2
- TypeScript

### 后端(br-server)
- Pythoen 3.12+
- FastAPI
- Uvicorn
- SQLAlchemy ORM
- Pydantic

### 数据库
- PostgreSQL 18

## 项目约定 

### 编码规范
- 遵循 Clean Architecture 
- 使用 Domain-Driven Design 
- 所有核心逻辑需要单元测试 
- API 需要集成测试

### 架构模式 
- 前端：组件分层 (pages → components → api → utils) 
- 后端：分层架构 (api/routes → services → models → schemas) 
- RBAC 权限控制必须在后端强制执行，不仅仅是前端隐藏

### Git 工作流 
- 主分支：`main` (生产环境) 
- 功能分支：`feature/<描述>` 
- 修复分支：`fix/<描述>` 
- 提交信息格式：`type(scope): description` 
  - 类型：feat, fix, docs, refactor, test

## 管理后台初始化与认证迁移

admin RBAC 动态设置变更落地后，后端数据库迁移只负责建表；默认管理员、超级管理员角色、默认菜单、按钮权限和系统设置通过独立 seed 脚本初始化。

```bash
cd br-server
alembic upgrade head
python -m app.services.seed_admin
```

seed 脚本应保持幂等，可以重复执行且不得重复插入默认角色、菜单、权限或系统设置。默认开发账号为 `admin / 123456`，也可以通过环境变量覆盖：

```bash
ADMIN_DEFAULT_USERNAME=admin
ADMIN_DEFAULT_PASSWORD=change-me
ADMIN_DEFAULT_EMAIL=admin@example.com
```

生产环境必须显式设置 `ADMIN_DEFAULT_PASSWORD`，不得依赖弱默认密码创建管理员。

管理后台认证将从 legacy `X-Admin-Token` 迁移到 br-server 签发的 `Authorization: Bearer <admin access token>`。`X-Admin-Token` 仅作为兼容和应急超级管理员通道保留，不能作为新 admin API 的主认证路径。

## 重要约束 

### 技术约束 
- 高并发支撑：内置 Redis 队列，有效削峰解耦，提升系统并发能力。
- 精细权限控制：基于 Spring Security 实现按钮级权限管理，保障系统安全。
- 接口规范：RESTful API 设计，接口复用率高，逻辑清晰。
- 数据可视化：集成 ECharts，支持订单、用户、资金等多维度数据看板。
- 覆盖率目标：核心业务逻辑 > 80%

### 业务约束
- 同一座位在同一时段不可重复预约
- 不可重复扣款，注意操作的幂等性
- 支付、充值要保留详细的操作流水

### 其他约束
- 微信小程序移动端优先设计  
- 数据库定期备份 
- 错误日志记录

## 核心功能清单
 
### V1 必须实现 
1. 首页
- [ ] 导航栏：支持门店选择（模拟多门店场景）
- [ ] 轮播图：展示优惠信息、活动推广
- [ ] 快捷入口：余额充值、卡券套餐、美团兑换
- [ ] 个人二维码：用于门店核销
- [ ] 热门活动：半开发状态，可展示活动列表
2. 预约
- [ ] 门店信息展示：名称、地址、距离等
- [ ] 预约时间选择：基于日期和时段的选择器
- [ ]座位预览：可查看座位布局
3. 我的（个人信息）
- [ ] 个人信息：头像、昵称等
- [ ] 平台账户：余额、卡券包、储物柜信息
- [ ] 学习记录：查看历史预约
- [ ] 排行榜：学习时长排名
- [ ] 意见反馈：用户可提交问题




