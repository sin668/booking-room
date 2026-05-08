## Why

当前系统已实现用户端自习室列表、座位查询和预约功能，但管理后台（br-admin）完全缺失门店和座位的 CRUD 管理能力。运营人员无法通过后台创建/编辑/下架自习室、管理座位信息或维护座位状态，只能依赖数据库直接操作，严重影响运营效率和系统可维护性。

## What Changes

- 新增自习室管理后台 API：创建、查询详情、更新、删除、切换营业状态（open/closed）
- 新增座位管理后台 API：创建单个座位、批量创建座位、查询详情、更新、删除、切换维护状态（available/maintenance）
- 新增 br-admin 自习室管理页面：列表页（分页/筛选）、新建/编辑表单、详情查看
- 新增 br-admin 座位管理页面：按房间查看座位列表、新建/编辑表单、批量生成座位、座位状态管理
- 新增 br-admin 后端 API 集成模块：room.ts 和 seat.ts API 服务文件
- 新增后台路由配置和菜单入口
- 新增后台相关的 Pydantic 请求/响应 schema
- 新增后台管理 API 单元测试和集成测试

## Capabilities

### New Capabilities
- `study-room-admin-api`: 自习室管理后台 RESTful API（CRUD + 状态切换），需要管理员权限
- `seat-admin-api`: 座位管理后台 RESTful API（CRUD + 批量操作 + 状态切换），需要管理员权限
- `study-room-admin-ui`: br-admin 自习室管理前端页面（列表、新建/编辑、详情）
- `seat-admin-ui`: br-admin 座位管理前端页面（列表、新建/编辑、批量生成）

### Modified Capabilities

（无现有 spec 需求变更，仅新增后台管理能力，不影响用户端 API 行为）

## Impact

- **br-server**: 新增 admin 路由（`api/routes/admin_study_room.py`、`api/routes/admin_seat.py`）、admin schema、admin service 方法、测试文件
- **br-admin**: 新增 views（自习室管理、座位管理）、api 集成文件、路由配置、菜单配置
- **数据库**: 无 schema 变更，复用现有 `study_rooms` 和 `seats` 表
- **回滚方案**: 后端 API 路由可通过注释注册代码回滚，前端页面可通过移除路由配置回滚，不影响现有用户端功能和数据
- **模块范围**: br-server（routes/services/schemas/models）、br-admin（views/api/router）
