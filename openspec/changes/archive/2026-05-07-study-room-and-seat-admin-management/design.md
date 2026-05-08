## Context

当前系统已实现用户端自习室列表（`GET /api/v1/rooms/`）、座位查询（`GET /api/v1/rooms/{room_id}/seats/`）和预约管理 API，管理后台已有活动管理（activity）作为 admin 模块的参考实现。数据库模型 `StudyRoom` 和 `Seat` 已完整定义，无需迁移。

管理后台认证采用 `X-Admin-Token` Header 方式，后端通过 `get_current_admin` 依赖注入实现鉴权，前端通过 `getAdminHeaders()` 统一注入。br-admin 使用 Naive UI 组件库，表格和表单基于 `BasicTable` / `BasicForm` 封装。

## Goals / Non-Goals

**Goals:**
- 实现自习室和座位的完整后台 CRUD 管理
- 管理员可通过后台创建/编辑/下架自习室
- 管理员可按房间管理座位，支持单个创建和批量生成
- 管理员可切换自习室营业状态和座位维护状态
- 复用现有 admin 认证和前端组件模式

**Non-Goals:**
- 不涉及用户端 API 行为变更
- 不涉及数据库 schema 变更（复用现有表）
- 不涉及预约管理后台（已有或另行规划）
- 不涉及权限细分（当前 admin token 即为超级管理员）

## Decisions

### 1. API 路由设计

**选择**: `/api/v1/admin/rooms/` 和 `/api/v1/admin/rooms/{room_id}/seats/`

**理由**: 沿用活动管理的 admin 路由前缀风格（`/api/v1/admin/activities`），座位作为自习室的子资源嵌套。现有用户端 API 保持不变（`/api/v1/rooms/`、`/api/v1/rooms/{room_id}/seats/`）。

**备选方案**: 扁平化座位路由 `/api/v1/admin/seats/` — 放弃，因为座位管理与房间强关联，嵌套更符合资源层级关系。

### 2. 批量座位生成策略

**选择**: 单个 POST 端点接收批量参数（zone 分区 + 行列数）

**理由**: 运营人员创建新房间时通常需要快速生成大量座位（当前 seed 脚本按 80 座/房间生成），逐个创建体验极差。批量生成按"安静区/键盘区/VIP区"分区，每区指定行列数，自动编号（如 A-01~A-20）。

### 3. 前端页面结构

**选择**: 自习室列表 → 座位管理（嵌套路由）

**理由**: 座位管理从属于自习室，采用嵌套路由 `/room/list` → `/room/list/:id/seats` 符合资源关系，用户路径清晰。

```
门店管理
├── 门店列表      /room/list
│   ├── 新建门店  /room/create
│   └── 编辑门店  /room/edit/:id
└── 座位管理      /room/list/:id/seats
```

### 4. 文件上传集成

**选择**: 封面图片复用现有 `file-upload` 能力

**理由**: 项目已有文件上传 spec（`openspec/specs/file-upload/`），自习室封面图片上传直接复用，不重新实现。

### 5. 后端 Service 层扩展

**选择**: 在现有 `study_room_service.py` 和 `seat_service.py` 中新增 admin 方法，不创建独立 admin service

**理由**: admin CRUD 与 user-facing 查询共享同一领域逻辑（模型操作），拆分 service 会导致重复代码。通过 route 层注入不同鉴权依赖来区分权限。

## Risks / Trade-offs

- **[批量座位编号冲突]** → 生成时检查已有 seat_number，避免唯一约束冲突，冲突时追加后缀（如 A-01-2）
- **[删除自习室关联座位]** → 后端级联删除或阻止删除有活跃预约的房间，返回 409 Conflict
- **[Admin token 安全性]** → 当前方案为简化版，后续可升级为 JWT RBAC，本次不做改造
