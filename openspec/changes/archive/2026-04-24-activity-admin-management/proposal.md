## Why

当前活动模块仅有面向小程序端的公开列表查询接口（GET /api/v1/activities），缺少管理后台对活动的增删改查能力。运营人员无法通过 br-admin 管理活动数据，需要直接操作数据库，效率低且易出错。

## What Changes

- **新增活动管理后台 API**：为 br-admin 提供 CRUD 接口（创建、查看详情、更新、删除活动），支持分页查询、状态切换（上架/下架），使用固定 Token（`ADMIN_TOKEN` 环境变量 + `X-Admin-Token` Header）鉴权
- **新增文件上传接口**：后端代理上传，存储到本地 `uploads/` 目录，返回可访问 URL
- **新增活动管理后台页面**：在 br-admin 中实现活动列表页（含搜索、筛选、分页）和活动编辑弹窗（新建/编辑表单，含图片上传）
- **新增管理端 Schema**：补充 ActivityCreate、ActivityUpdate、ActivityAdminResponse 等 Pydantic 模型

## Capabilities

### New Capabilities
- `activity-admin-api`: 活动管理后台 RESTful API，包含分页列表、创建、详情、更新、删除、上下架等接口，使用固定 Token 鉴权
- `activity-admin-ui`: br-admin 活动管理前端页面，包含活动列表页（搜索、筛选、分页、上下架操作）和活动编辑弹窗（新建/编辑表单，含图片上传）
- `file-upload`: 通用文件上传服务，后端代理上传存储到本地 `uploads/` 目录，返回可访问 URL

### Modified Capabilities
- `activity-list`: 现有公开列表接口需增加管理端查询支持（返回全部活动含已下架），需补充管理员角色判断逻辑

## Impact

- **后端 (br-server)**:
  - 新增 API 路由：`admin_activity.py`（管理端活动接口）、`upload.py`（文件上传接口）
  - 新增 Service 方法：CRUD 业务逻辑、文件上传逻辑
  - 新增 Schema：管理端请求/响应模型
  - 新增鉴权依赖：`get_current_admin`（固定 Token 校验）
  - 数据库迁移：无（Activity 模型已包含所需字段）
- **管理后台 (br-admin)**:
  - 新增页面：活动管理列表页、编辑弹窗
  - 新增 API 调用：活动管理接口封装
  - 新增路由：菜单配置
- **受影响模块范围**: `br-server/app/api/routes/activity.py`, `br-server/app/services/activity_service.py`, `br-server/app/schemas/activity.py`, `br-admin/src/`
- **回滚方案**: 所有新增代码为独立模块，可通过删除新增路由、页面和 API 即可回滚，不影响现有小程序端活动列表功能
