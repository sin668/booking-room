## Context

当前 booking-room 项目的活动模块已有面向小程序端的公开列表查询接口（GET /api/v1/activities/），Activity 模型已包含 `is_active`、`sort_order` 等管理字段。br-admin 管理后台基于 Vue3 + NaiveUI + Alova，已有 BasicTable、BasicForm、Modal 等可复用组件。

现有技术约束：
- br-admin 使用 NaiveUI 组件库（非 Element UI），Alova 作为 HTTP 客户端
- 后端 RBAC 权限需在后端强制执行
- 管理端 API 前缀约定为 `/api/v1/admin/`

## Goals / Non-Goals

**Goals:**
- 实现活动管理后台完整 CRUD（创建、查看、编辑、删除）
- 支持分页查询、关键词搜索、状态筛选
- 支持活动上下架切换
- 复用 br-admin 现有 BasicTable、BasicForm、Modal 组件模式

**Non-Goals:**
- 不涉及活动参与人数的真实统计（`participant_count` 仍为手动设置）
- 不涉及活动报名、签到等业务流程
- 不涉及小程序端页面变更
- 不涉及数据库迁移（Activity 模型已满足需求）

## Decisions

### 1. 管理端 API 路由前缀使用 `/api/v1/admin/activities`

**选择**: 管理端接口统一挂载在 `/api/v1/admin/` 前缀下，与公开接口隔离。

**替代方案**:
- A) 在现有 `/api/v1/activities/` 下扩展管理接口 → 职责混合，公开接口与管理接口耦合
- B) 使用独立路由文件 `admin_activity.py` → 增加文件数量，但职责更清晰

**结论**: 采用方案 B，创建独立的 `admin_activity.py` 路由文件，挂载在 `/api/v1/admin/activities`。

### 2. 管理端使用固定 Token 鉴权

**选择**: 管理端接口通过环境变量 `ADMIN_TOKEN` 配置固定 Token，请求 Header 携带 `X-Admin-Token` 进行校验。

**替代方案**:
- A) 暂不鉴权 → 不安全，不适合任何部署环境
- B) 完整管理员登录 + JWT → 工作量大，当前无管理员账号体系

**结论**: 采用固定 Token 方案，在 FastAPI 中实现 `get_current_admin` 依赖，校验 `X-Admin-Token` Header。后续可替换为 JWT/RBAC。

### 3. 前端复用 BasicTable + Modal 模式

**选择**: 活动列表页使用 br-admin 已有的 BasicTable 组件（支持分页、搜索），编辑使用 Modal 弹窗内嵌 BasicForm。

**理由**: 与现有 list/basicList 页面保持一致的开发模式和用户体验。

### 4. 分页查询使用后端分页

**选择**: 管理端列表接口支持 `page`、`page_size` 参数，后端返回 `total`、`items` 结构。

**理由**: 活动数据量增长后前端全量返回不可接受，后端分页为标准做法。

### 5. 封面图通过后端代理上传

**选择**: 后端提供 `POST /api/v1/admin/upload/` 文件上传接口，接收 multipart/form-data，存储到本地 `uploads/` 目录，返回可访问的 URL。

**替代方案**:
- A) 仅输入 URL → 运营需自行处理上传，体验差
- B) 前端直传 OSS → 需配置 OSS SDK 和临时凭证，当前无 OSS 基础设施

**结论**: 采用后端代理上传，存储到本地目录并通过 FastAPI StaticFiles 或专用路由提供访问。后续可平滑迁移到 OSS。

**序列图 — 活动封面图上传流程：**

```
管理员          br-admin          br-server           本地存储
  |                |                 |                   |
  |-- 选择图片 -->|                 |                   |
  |                |-- POST /admin/upload/ (file) -->|  |
  |                |                 |-- 保存文件 ----->|  |
  |                |                 |<-- 返回 URL -----|  |
  |                |<-- { url: "/uploads/xxx.jpg" } --|  |
  |<-- 预览图片 --|                 |                   |
  |                |                 |                   |
  |-- 提交表单 -->|                 |                   |
  |                |-- POST /admin/activities/ ------->|  |
  |                |<-- 创建成功 (cover_image 含 URL)-|  |
  |<-- 列表刷新 --|                 |                   |
```

## Risks / Trade-offs

- **[固定 Token 安全性]** → Token 通过环境变量配置，不在代码中硬编码；后续迭代替换为 JWT/RBAC
- **[本地文件存储可扩展性]** → 当前使用本地 `uploads/` 目录，后续可迁移至 OSS/S3，接口层无需变更
- **[NaiveUI 版本兼容]** → br-admin 当前使用 NaiveUI，需确保表单校验、表格交互在该版本下正常工作
