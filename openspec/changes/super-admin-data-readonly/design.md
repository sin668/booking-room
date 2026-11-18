# Design: super-admin-data-readonly

## 后端

### data_scope.py 新增助手（唯一判定来源）

- `async def readonly_creators(db, creator_ids, viewer) -> set[UUID]`：viewer 不受限（超管/legacy/None）时返回空集；否则一次 SELECT 查出给定创建人中当前 `user_type='super-admin'` 的 id 子集。列表/详情服务用 `row.created_by in 该集合` 得出 `readonly`。
- `async def ensure_writable(db, model, obj_id, viewer)`：viewer 不受限直接返回；查目标 `created_by`，若属于当前超管则抛 `HTTPException(403, "超级管理员创建的数据仅可查看")`；目标不存在或 `created_by` 为空/普通用户时不拦截（404 与归属可见性由既有逻辑负责）。
- 随属记录入口：
  - 课时/排课：路径已有 `course_id` → `ensure_writable(Course, course_id)`。
  - 座位：嵌套路由用 `room_id`；扁平路由经 seat → `room_id`。
  - 预约：booking → `course_id`（课程订单）或 `room_id`（座位订单）。
  - 评价：review → `course_id`，否则经 booking → `room_id`。

判定口径与可见性一致：按创建人**当前** user_type；超管降级后其数据恢复归属过滤，本人可正常写。

### 路由接入（不改服务写函数签名）

在写端点调用服务前执行 `ensure_writable`，viewer 取 `get_current_admin` 的 AdminContext。覆盖：

| 路由 | 写端点 |
| --- | --- |
| admin_study_room | PUT / DELETE / PATCH status |
| admin_course | PUT / DELETE / PATCH status；lessons POST/PUT/DELETE；schedules POST/PUT/DELETE/postpone-lesson |
| admin_activity | PUT / DELETE / PATCH status |
| admin_coupon | PUT / PATCH status / DELETE |
| admin_teacher | PUT / DELETE / PATCH status / PUT available-time-slots |
| admin_seat | 嵌套 POST；扁平 PUT/DELETE/PATCH status（含批量创建如存在） |
| admin_booking | POST cancel / POST confirm |
| admin_review | PATCH status / PATCH reply |

### readonly 字段

响应模型加 `readonly: bool = False`：RoomAdminResponse、ActivityAdminResponse、AdminCouponResponse、AdminTeacherListItem/Detail、AdminCourseItem（及详情）、SeatAdminResponse、BookingAdminResponse（及详情）、AdminReviewItem。列表/详情服务在既有 scope 查询处顺带取 `created_by`（booking/review 已 outerjoin Course/StudyRoom），用 `readonly_creators` 批量判定，避免逐行查询。

## 前端（br-admin）

- `BasicTable`：`props.ts` 与 `BasicTableProps` 增加 `rowClassName` 透传（getBindValues 已展开 props，声明后即达 n-data-table）。
- 全局样式新增 `.readonly-row`：文字置灰、透明度降低。
- 8 个 API item 类型补 `readonly?: boolean`。
- 8 个列表页：`:row-class-name="row => row.readonly ? 'readonly-row' : ''"`；修改类 `TableAction` 动作加 `disabled: record.readonly`（ActionItem 已支持 disabled）；下拉动作同样禁用。保留查看类入口：预约「查看」、教室「管理座位」（进入后座位页自身置灰禁改）。
- 座位页：行置灰 + 编辑/删除/状态禁用；所属教室只读时「新增座位/批量创建」按钮禁用。
- 编辑页直达 URL 的写提交由后端 403 兜底，不在本次前端改造范围。

## 验证

- pytest：test_data_scope.py 扩展写保护与 readonly 场景；全量对照 19 个存量基线失败零回归。
- br-admin `pnpm build` 通过。
- 真实环境冒烟/浏览器：临时普通管理员（仅相应菜单权限）看到超管数据置灰、按钮禁用、直接调 API 写返回 403；超管不受影响。