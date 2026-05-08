## Why

系统当前仅提供用户端预约 API（创建、查询、取消），缺少管理后台对预约订单的管理能力。管理员无法查看所有用户的预约记录、处理异常订单（如手动取消/退款）。需要补齐后台订单管理闭环，与已有的自习室管理、座位管理形成完整的管理链路。

## What Changes

- 新增预约订单管理后台 API（列表、详情、取消、状态管理）
- 新增预约订单管理后台页面（订单列表页，含筛选、分页、操作）
- 管理员可查看全部用户的预约记录（不受 user_id 限制）
- 管理员可对异常订单执行取消操作
- 支持按日期范围、状态、自习室、用户等维度筛选订单

## Capabilities

### New Capabilities

- `booking-admin-api`: 预约订单管理后台 API，提供管理员查看全部订单、订单详情、取消订单等接口
- `booking-admin-ui`: 预约订单管理后台页面，提供订单列表展示、筛选、详情查看和状态管理功能

### Modified Capabilities

<!-- 无现有 spec 需要修改 -->

## Impact

- **后端模块**: `br-server/app/api/routes/`（新增 admin booking 路由）、`br-server/app/services/booking_service.py`（新增管理员方法）、`br-server/app/schemas/booking.py`（新增管理员响应 schema）
- **前端模块**: `br-admin/src/views/`（新增订单管理页面）、`br-admin/src/api/`（新增订单 API）、`br-admin/src/router/`（新增路由模块）
- **API**: 新增 `/api/v1/admin/bookings/` 系列 RESTful 端点
- **依赖**: 复用现有 `get_current_admin` 认证中间件
- **回滚方案**: 删除新增的路由文件和前端页面，移除新增的 service 方法，不影响现有用户端预约功能
