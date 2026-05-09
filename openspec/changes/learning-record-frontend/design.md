## Context

当前系统已有完整的预约功能（booking），用户预约座位后会生成 booking 记录（status: confirmed/cancelled/completed）。个人中心页面已预留学习记录入口（`/pages/study-record/index`），但页面尚未实现。

学习记录本质上是对已完成预约（status=completed）的聚合展示，无需新建数据模型。

## Goals / Non-Goals

**Goals:**

- 基于现有 booking 数据提供学习记录查询能力
- 实现月度统计（学习时长、预约次数、连续天数、累计时长）
- 实现月度日历打卡视图
- 实现学习记录列表分页查询
- 前端页面与原型 `prototype/study-record.html` 保持一致

**Non-Goals:**

- 不新增独立的学习记录数据模型（复用 booking）
- 不做学习记录的导出功能
- 不做管理后台的学习记录管理页面

## Decisions

### 1. 数据来源：复用 Booking 模型

学习记录直接从 `bookings` 表查询 `status='completed'` 的记录。无需新建表或迁移。

**理由**: 学习记录和预约记录本质是同一份数据的不同视图，避免数据冗余和同步问题。

**备选方案**: 新建 `study_records` 表 — 增加数据冗余，需要额外的同步逻辑，收益不大。

### 2. API 设计：两个端点

- `GET /api/v1/study-records/summary?month=YYYY-MM` — 月度统计 + 日历打卡数据
- `GET /api/v1/study-records?page=1&page_size=10&month=YYYY-MM` — 学习记录列表

**理由**: 统计和列表查询频率不同，分离后统计接口可独立缓存。日历打卡数据合并到 summary 中减少请求次数。

### 3. 前端页面结构

单页面方案：一个 Vue 文件包含统计卡片、日历、记录列表三个区域。日历月份切换触发 summary 刷新，记录列表支持分页加载。

**理由**: 页面结构简单（约 3 个区域），无需拆分子组件，单文件即可保持清晰。

## Risks / Trade-offs

- **大量历史数据查询性能** → summary 接口添加 `month` 必填参数，限定查询范围；列表接口分页
- **Booking 状态依赖** → 学习记录仅统计 `status='completed'` 的记录，如果 completed 状态未及时更新，统计数据会不准确。需确保现有预约流程正确标记 completed 状态

## Migration Plan

纯新增功能，无数据库迁移。部署步骤：

1. 后端部署 study_record 路由
2. 前端新增页面并注册路由
3. 回滚：删除新增文件，移除路由注册
