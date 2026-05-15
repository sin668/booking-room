## Why

当前 App 的城市名"茂名市"在前端硬编码，选城按钮 (`onTapCity`) 是空壳占位。随着业务向更多城市扩张，需要一套城市选择机制让用户切换城市，并按城市筛选自习室列表。这同时需要后端 City 数据模型和 API 支持。

## What Changes

- 新增 City 数据模型（city_name, province, sort_order, status），支持多城市管理
- StudyRoom 模型新增 `city_id` 外键，建立自习室与城市的关联
- 新增城市列表 API、城市切换接口（后端）
- 前端新增城市选择页面，支持搜索和定位
- 首页/预约页城市显示改为动态读取，点击跳转城市选择
- 自习室列表 API 增加 city_id 过滤参数
- 用户选城偏好持久化到本地存储

## Capabilities

### New Capabilities
- `city-selection-api`: 城市数据管理 API — City 模型、城市列表接口、城市与自习室关联查询
- `city-selection-ui`: 城市选择前端交互 — 城市选择页面、选城持久化、自习室列表城市过滤

### Modified Capabilities
- `study-room-booking-api`: 自习室列表 API 新增 city_id 过滤参数
- `study-room-booking-ui`: 预约页城市显示改为动态读取，点击触发城市选择
- `study-room-list`: 首页自习室列表增加城市维度过滤

## Impact

- **后端模型**: 新增 City 模型，StudyRoom 新增 city_id 外键 + Alembic 迁移
- **后端路由**: 新增 /api/cities 路由，修改 /api/rooms 路由增加 city_id 参数
- **前端页面**: 新增城市选择页面，修改 booking/index.vue 和首页
- **数据迁移**: 现有自习室需要分配默认 city_id
- **回滚方案**: 移除 city_id 外键和 City 模型即可回滚，前端恢复硬编码城市名。数据库迁移使用 Alembic downgrade
