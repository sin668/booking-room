## 1. 后端 Admin Schemas

参考 `br-server/app/schemas/activity.py` 的模式（BaseModel + from_attributes + Field 约束）。

- [x] 1.1 新建 `br-server/app/schemas/study_room.py`（如文件已存在则追加），新增：`RoomCreate`（name 必填、address 必填、其余可选）、`RoomUpdate`（所有字段 Optional）、`RoomStatusUpdate`（status 枚举 open/closed）、`RoomAdminResponse`（继承 Room 字段 + seat_count/available_seat_count 统计字段）、`RoomListResponse`（分页包装，复用现有 ActivityListResponse 的 items/total/page/page_size 模式）
- [x] 1.2 新建 `br-server/app/schemas/seat.py`（如文件已存在则追加），新增：`SeatCreate`（seat_number/zone/price_per_hour 必填）、`SeatBulkZoneConfig`（zone/rows/cols/prefix/start_number/price_per_hour/floor）、`SeatBulkCreate`（包含 seats: list[SeatBulkZoneConfig]）、`SeatUpdate`（所有字段 Optional）、`SeatStatusUpdate`（status 枚举 available/maintenance）、`SeatAdminResponse`（继承 Seat 字段 + room_name 关联字段）

## 2. 后端 Study Room Admin Service

在 `br-server/app/services/study_room_service.py` 中新增方法，复用现有的 `MAX_PAGE_SIZE=50`、`DEFAULT_PAGE_SIZE=10` 常量和 async session 模式。

- [x] 2.1 新增 `admin_list_rooms()` — 分页查询所有房间（不过滤 status），支持 status 筛选参数
- [x] 2.2 新增 `admin_get_room()` — 查询单个房间详情，含 seat_count 和 available_seat_count 统计（用 func.count 聚合）
- [x] 2.3 新增 `create_room()` — 创建房间，返回 RoomAdminResponse
- [x] 2.4 新增 `update_room()` — 部分更新房间字段
- [x] 2.5 新增 `delete_room()` — 删除前检查是否存在 confirmed 状态的 Booking（查 bookings 表 room_id），有则抛 HTTPException(409)
- [x] 2.6 新增 `toggle_room_status()` — 切换 open/closed 状态
- [x] 2.7 编写 study room admin service 单元测试 `br-server/tests/test_study_room_admin_service.py`，覆盖：创建成功、列表分页、状态筛选、详情含统计、更新、删除成功、删除有活跃预约的房间(409)、状态切换、房间不存在(404)

## 3. 后端 Seat Admin Service

在 `br-server/app/services/seat_service.py` 中新增方法，复用现有的 `_room_exists()` 私有方法。

- [x] 3.1 新增 `admin_list_seats()` — 查询指定房间所有座位（不过滤 status），支持 zone/status 筛选
- [x] 3.2 新增 `admin_get_seat()` — 查询单个座位详情，含 room_name
- [x] 3.3 新增 `create_seat()` — 创建座位前检查 seat_number 在同一 room_id 下唯一（查 seats 表），重复则抛 HTTPException(409)
- [x] 3.4 新增 `bulk_create_seats()` — 按 SeatBulkZoneConfig 生成座位列表，遍历每个 zone 配置按 rows×cols 生成 seat_number（prefix + 零填充编号），全部生成后批量插入（原子操作），生成前检查所有编号不冲突
- [x] 3.5 新增 `update_seat()` — 部分更新座位字段，若修改 seat_number 需检查唯一性
- [x] 3.6 新增 `delete_seat()` — 删除前检查是否存在 confirmed 状态的 Booking（查 bookings 表 seat_id），有则抛 HTTPException(409)
- [x] 3.7 新增 `toggle_seat_status()` — 切换 available/maintenance 状态
- [x] 3.8 编写 seat admin service 单元测试 `br-server/tests/test_seat_admin_service.py`，覆盖：创建成功、编号重复(409)、批量生成（单区/多区）、批量编号冲突(409)、空数组(422)、列表含筛选、详情含 room_name、更新、更新编号冲突(409)、删除成功、删除有活跃预约(409)、状态切换

## 4. 后端 Admin Routes

参考 `br-server/app/api/routes/admin_activity.py` 的模式：APIRouter(prefix + tags + dependencies)、Depends(get_current_admin) 路由级鉴权、标准 CRUD 端点。

- [x] 4.1 新建 `br-server/app/api/routes/admin_study_room.py`，注册 6 个端点：`POST /`（创建）、`GET /`（列表）、`GET /{room_id}/`（详情）、`PUT /{room_id}/`（更新）、`DELETE /{room_id}/`（删除）、`PATCH /{room_id}/status/`（状态切换）
- [x] 4.2 新建 `br-server/app/api/routes/admin_seat.py`，注册 8 个端点：`POST /rooms/{room_id}/seats/`（单个创建）、`POST /rooms/{room_id}/seats/bulk/`（批量创建）、`GET /rooms/{room_id}/seats/`（列表）、`GET /seats/{seat_id}/`（详情）、`PUT /seats/{seat_id}/`（更新）、`DELETE /seats/{seat_id}/`（删除）、`PATCH /seats/{seat_id}/status/`（状态切换）。注意：需要两个路由前缀或分开注册以处理 room_id 嵌套和扁平两种路径
- [x] 4.3 在 `br-server/app/main.py` 中 import 并注册 admin_study_room_router 和 admin_seat_router，插入到 admin_activity_router 之后
- [x] 4.4 编写 admin routes 集成测试 `br-server/tests/test_admin_room_routes.py` 和 `br-server/tests/test_admin_seat_routes.py`，覆盖所有端点的成功/失败场景（无 token → 401、参数缺失 → 422、资源不存在 → 404、冲突 → 409）

## 5. 前端 API 集成

参考 `br-admin/src/api/activity/index.ts` 的模式：TypeScript 接口定义、Alova HTTP 客户端、getAdminHeaders() 注入 X-Admin-Token、camelCase ↔ snake_case 参数转换。

- [x] 5.1 新建 `br-admin/src/api/room/index.ts`，定义接口（RoomItem/RoomListParams/RoomFormParams）和 API 函数（getRoomList/createRoom/getRoomById/updateRoom/deleteRoom/toggleRoomStatus）
- [x] 5.2 新建 `br-admin/src/api/seat/index.ts`，定义接口（SeatItem/SeatListParams/SeatFormParams/SeatBulkZoneConfig/SeatBulkParams）和 API 函数（getSeatList/createSeat/getSeatById/updateSeat/deleteSeat/toggleSeatStatus/bulkCreateSeats）

## 6. 前端自习室管理页面

参考 `br-admin/src/views/activity/list/index.vue` 的模式：BasicForm 搜索 + BasicTable 数据表 + Modal 弹窗编辑。

- [x] 6.1 新建 `br-admin/src/views/room/list/index.vue`，实现：顶部搜索区（名称输入框 + 状态下拉选择）、BasicTable 列（封面缩略图/名称/地址/营业时间/最低价格/状态标签(n-tag)、座位数/操作列）、操作列下拉菜单（编辑/删除/上架或下架/管理座位→跳转嵌套路由）
- [x] 6.2 新建 `br-admin/src/views/room/list/components/RoomEditModal.vue`，实现：n-modal 弹窗表单、字段（名称 n-input / 描述 n-input textarea / 封面图片 upload / 地址 n-input / 营业时间 n-time-picker / 最低价格 n-input-number）、复用新建和编辑（通过 v-model:show + rowData prop 控制）、提交后 reloadTable
- [x] 6.3 实现列表页交互：handleDelete（n-popconfirm 确认 → deleteRoom → 有活跃预约显示错误提示）、handleToggleStatus（n-popconfirm 确认 → toggleRoomStatus）、handleManageSeats（router.push 到 /room/list/:id/seats）

## 7. 前端座位管理页面

- [x] 7.1 新建 `br-admin/src/views/room/seats/index.vue`，实现：顶部面包屑（门店列表 > 座位管理）+ 返回按钮 + 房间名称展示、搜索区（分区下拉 zone: quiet/keyboard/vip + 状态下拉 status: available/maintenance）、BasicTable 列（座位编号/分区标签(n-tag 不同颜色)/位置/楼层/每小时价格/状态标签/行列位置/操作列）
- [x] 7.2 新建 `br-admin/src/views/room/seats/components/SeatEditModal.vue`，实现：n-modal 弹窗表单、字段（座位编号 n-input / 分区 n-select / 位置 n-select(靠窗/中间/独立) / 楼层 n-input-number(默认3) / 每小时价格 n-input-number / 行号 n-input-number / 列号 n-input-number）、复用新建和编辑
- [x] 7.3 新建 `br-admin/src/views/room/seats/components/SeatBulkCreateModal.vue`，实现：n-modal 弹窗、可动态添加多个分区配置卡片（每张卡片含：分区类型 n-select / 行数 n-input-number / 列数 n-input-number / 编号前缀 n-input / 起始编号 n-input-number / 每小时价格 n-input-number / 楼层 n-input-number / 删除分区按钮）、底部预览区显示"共生成 N 个座位"、提交按钮调用 bulkCreateSeats
- [x] 7.4 实现座位列表页交互：handleDelete（n-popconfirm → deleteSeat → 有活跃预约显示错误）、handleToggleStatus（n-popconfirm → toggleSeatStatus）

## 8. 前端路由与菜单

参考 `br-admin/src/router/modules/activity.ts` 的模式：Layout 包裹、children 路由、meta(title/icon/sort)。

- [x] 8.1 新建 `br-admin/src/router/modules/room.ts`，路由结构：`/room`（Layout）→ children: `/room/list`（门店列表）、`/room/list/:id/seats`（座位管理，通过路径参数传递 room_id）
- [x] 8.2 在 br-admin 菜单配置中新增"门店管理"一级菜单（图标 HomeOutline）、"门店列表"子菜单，确认侧边栏正确渲染

## 9. 收尾

- [x] 9.1 代码审查：确认 Clean Architecture 分层（routes → services → models，schemas 独立）、无重复代码、admin/user 职责分离清晰
- [x] 9.2 更新 `docs/api.md`，补充所有新增 admin 接口文档（自习室 6 个 + 座位 7 个，含请求/响应示例）
