## Context

当前 br-app 预约页城市名"茂名市"硬编码在 `booking/index.vue` 中，`onTapCity()` 是空函数。br-server 的 StudyRoom 模型没有城市关联字段，所有自习室通过 address 文本字段存储地址信息。后端没有 City 数据模型。

现有自习室种子数据分布在茂名市不同区县（茂南区、电白区、高州市），但系统无法按城市过滤。

技术约束：
- 前端使用 uni-app (Vue3) + Vuex
- 后端使用 FastAPI + SQLAlchemy 2.0 + Pydantic V2
- 数据库迁移使用 Alembic
- 遵循分层架构：routes → services → models → schemas

## Goals / Non-Goals

**Goals:**
- 支持多城市运营，用户可切换当前城市
- 后端 City 数据模型和 CRUD API
- 自习室列表支持按城市过滤
- 前端城市选择页面（搜索 + 热门城市 + 全部城市列表）
- 用户选城偏好本地持久化，跨会话保持

**Non-Goals:**
- 城市/区级后台管理界面（MVP 通过 Alembic seed 管理）
- GPS 自动定位城市
- 省级/国家级多级行政区划
- 后台管理端城市管理

## Decisions

### 1. City 模型设计：独立表 + StudyRoom 外键关联

**选择**: 新建 `cities` 表，StudyRoom 添加 `city_id` 可空外键。

**备选方案**:
- A) 城市直接嵌入 StudyRoom（冗余 city_name 字段）— 简单但不支持城市级聚合查询
- B) 独立 City 表 + 外键 — 规范化，支持城市列表/排序/启停管理

**理由**: 独立 City 表是标准做法，城市数据可单独管理（排序、启停状态），后续扩展城市管理后台无需改模型。`city_id` 设为可空以保证迁移兼容性。

### 2. 城市选择 UI：独立全屏页面

**选择**: 新增 `pages/city-select/index.vue` 全屏页面，从预约页点击城市跳转。

**备选方案**:
- A) 底部弹出半屏弹窗 — 节省页面跳转，但城市列表多时体验差
- B) 全屏页面 — 支持搜索、分区展示，交互空间充足

**理由**: 全屏页面更适合搜索 + 热门城市分区展示，体验更完整。符合微信小程序常见选城模式（美团、大众点评风格）。

### 3. 选城持久化：Vuex + uni.setStorageSync

**选择**: Vuex store 管理当前城市状态，同步到本地存储持久化。

**备选方案**:
- A) 仅本地存储 — 简单但组件间共享不便
- B) 后端存储用户偏好 — 增加复杂度，用户未登录时无法使用

**理由**: Vuex + localStorage 兼顾响应式更新和持久化，无需登录即可使用。后续可扩展为登录后同步到后端。

### 4. API 设计：城市列表独立接口 + 自习室列表增加过滤

**选择**:
- `GET /api/v1/cities/` — 返回启用状态的城市列表（按 sort_order 排序）
- `GET /api/v1/rooms/?city_id=1` — 现有接口增加可选 city_id 过滤参数

**理由**: 复用现有 rooms 接口，仅增加可选参数，向后兼容。城市列表独立接口职责清晰。

## Risks / Trade-offs

- **[数据迁移]** 现有自习室无 city_id → 迁移时分配默认城市（茂名市），address 文本解析区县信息不可靠 → 使用 Alembic 迁移脚本批量设置默认 city_id
- **[向后兼容]** city_id 可空 → 前端请求不传 city_id 时返回全部城市自习室，需确认这是期望行为 → 确认：不传 city_id 返回全部，兼容现有调用方
- **[城市数据管理]** MVP 无管理后台 → 通过 Alembic seed 脚本管理城市数据，新增城市需要代码部署 → 可接受，后续迭代增加管理界面

## Migration Plan

1. 创建 City 模型和 cities 表
2. StudyRoom 添加 city_id 可空外键
3. Alembic 迁移：创建表 → seed 多个广东省城市（茂名市、广州市、深圳市等）→ 批量更新现有 StudyRoom 的 city_id
4. 部署后端 API
5. 部署前端城市选择页面
6. 验证现有功能不受影响（city_id 可空，不传参数返回全部）

**回滚**: Alembic downgrade 移除 city_id 列和 cities 表，前端恢复硬编码城市名。
