# Design: wallet-transaction-room-scope

## 归属口径

学习室归属 = `StudyRoom.created_by`（无独立 owner 字段）。

可见性统一为「学习室归属 OR 课程创建人」：

- 预约：所有 Booking 都有 `room_id`（NOT NULL），课程订单的 `room_id` 即课程所在室（`course_booking_service` 已确认）。故预约可见 = `_visible_creator_condition(StudyRoom.created_by)` **或** `(Booking.course_id 非空 且 _visible_creator_condition(Course.created_by))`。
- 评价：所有 Review 都有 `booking_id`（NOT NULL），经 Booking 取 `room_id`。故评价可见 = `_visible_creator_condition(StudyRoom.created_by)` **或** `(Review.course_id 非空 且 _visible_creator_condition(Course.created_by))`。
- 钱包：交易经 `booking_id → Booking` 回溯，复用预约可见性，且要求 `booking_id` 非空（充值等无归属流水排除）。

`_visible_creator_condition(column, viewer)` = `column IS NULL`（存量/legacy）**或** `column == viewer.admin_id`（自己拥有）**或** `column IN (超管 id 子查询)`（超管创建公开）。`_unrestricted(viewer)`（None/超管/legacy UUID(int=0)）→ 不过滤。

含义：学习室拥有者能看到该室发生的全部订单/评价（含他人创建课程产生的）；课程创建者仍能看到自己课程的订单/评价（即使在他人的室）。两者并集，超管/存量公开规则不变。

## 后端

### data_scope.py

重写两个条件函数（调用方已 outerjoin 所需表，无需改服务 join）：

```python
def booking_scope_condition(viewer):
    if _unrestricted(viewer):
        return None
    from app.models.booking import Booking
    from app.models.course import Course
    from app.models.study_room import StudyRoom
    return or_(
        _visible_creator_condition(StudyRoom.created_by, viewer),
        and_(Booking.course_id.is_not(None), _visible_creator_condition(Course.created_by, viewer)),
    )

def review_scope_condition(viewer):
    if _unrestricted(viewer):
        return None
    from app.models.booking import Booking
    from app.models.course import Course
    from app.models.review import Review
    from app.models.study_room import StudyRoom
    return or_(
        _visible_creator_condition(StudyRoom.created_by, viewer),
        and_(Review.course_id.is_not(None), _visible_creator_condition(Course.created_by, viewer)),
    )
```

调用方 join 约定（现状已满足）：
- booking：outerjoin Course（Booking.course_id）、StudyRoom（Booking.room_id）。
- review：outerjoin Course（Review.course_id）、Booking（Review.booking_id）、StudyRoom（Booking.room_id）。

新增钱包条件：

```python
def wallet_scope_condition(viewer):
    if _unrestricted(viewer):
        return None
    from app.models.wallet import WalletTransaction
    return and_(
        WalletTransaction.booking_id.is_not(None),
        booking_scope_condition(viewer),
    )
```

调用方需 outerjoin：`Booking`（WalletTransaction.booking_id == Booking.id）、`Course`（Booking.course_id == Course.id）、`StudyRoom`（Booking.room_id == StudyRoom.id）。

### wallet_service.py

- `admin_list_transactions(..., viewer=None)`：scope 非空时给 count 与 list 查询加上述三个 outerjoin，并把 scope 加入 conditions。list 查询已 join User，再追加 outerjoin。
- `admin_get_statistics(..., viewer=None)`：分组统计 stmt 与活跃用户 stmt 在 scope 非空时加 `select_from(WalletTransaction)` + 三个 outerjoin，conditions 加 scope。统计与列表同口径（普通用户充值统计为 0）。

### admin_wallet.py

- `list_transactions` / `get_statistics` / `export_transactions` 三端点加 `context: AdminContext | None = Depends(get_current_admin)`，把 `viewer=context` 传给服务函数。
- `export_transactions` 在路由内联构建 conditions：计算 `wallet_scope_condition(context)`，非空时给 count 与数据 stmt 加 outerjoin 并追加 scope，确保导出与列表一致。
- 导入 `AdminContext, get_current_admin`（已有 require_admin_permission）。

### 预约/评价服务

`admin_list_bookings`、`list_reviews` 已按上述约定 outerjoin，条件函数变化即生效，**不改服务代码**。readonly 判定（课程订单随课程创建人、座位订单随室创建人）保持不变——本次只放宽可见性，不改只读归属。

## 前端

无需改动。服务端按登录管理员强制过滤，API 签名不变，预约/评价/钱包页自动只返回可见数据。普通用户选「充值」类型筛选时返回空（符合预期）。

## 不改项

不改数据库 schema、不改权限码、不改超管公开/只读规则、不改 readonly 归属判定。

## 测试影响（既有断言需更新）

`test_data_scope.py` 的 `seed_content` 中 `booking_course`/`review_course` 位于 `room_b`（ADMIN_B 拥有）但课程为 `course_a`（ADMIN_A 创建）。旧断言：B 看不到 booking_course/review_course。放宽后 B 拥有 room_b → **应看到** booking_course/review_course。这是用户要求的预期行为，须更新断言而非回退逻辑：

- B 预约可见 = {booking_course, booking_seat, booking_legacy}。
- B 评价可见 = {review_course, review_seat}。
- A 预约可见 = {booking_course（自己课程）, booking_legacy}（room_b 非 A，booking_seat 不可见）。
- A 评价可见 = {review_course}。

## 验证

- pytest：更新既有预约/评价断言；新增「学习室拥有者跨创建人可见」与钱包归属测试（普通用户仅见拥有学习室的消费/退款、充值隐藏、他人学习室流水不可见、存量/超管创建公开、超管全部、统计/导出同口径）。全量对照 19 基线零回归。
- 真实环境冒烟：临时普通管理员（拥有某学习室）钱包流水仅显示该室消费/退款、充值不显示；预约/评价可见该室他人创建课程的记录；超管显示全部。