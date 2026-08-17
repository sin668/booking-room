---
comet_change: course-booking
role: technical-design
canonical_spec: openspec
---

# 课程预约功能 — 技术设计文档

## 1. 概述

本设计文档细化课程预约功能的实现方案。高层架构决策见 `openspec/changes/course-booking/design.md`，需求规格见 `openspec/changes/course-booking/specs/`。

## 2. 数据模型设计

### 2.1 Course 模型扩展

```python
# app/models/course.py 新增字段
custom_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
full_package_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
```

- `custom_price`：1V1 私人定制单价，默认 0（表示未设置）
- `full_package_price`：全套课时优惠价，null 表示不支持全套优惠

### 2.2 Booking 模型扩展

```python
# app/models/booking.py 新增/修改字段
booking_type: Mapped[str] = mapped_column(String(20), default="seat", nullable=False, index=True)
course_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("courses.id"), nullable=True)
lesson_ids: Mapped[list[int] | None] = mapped_column(ARRAY(Integer), nullable=True)
schedule_type: Mapped[str | None] = mapped_column(String(20), nullable=True)
# seat_id 改为 nullable
seat_id: Mapped[int | None] = mapped_column(Integer, nullable=True, index=True)
```

- `booking_type`：`"seat"` = 自习室座位预约（默认），`"course"` = 课程预约
- `course_id`：课程预约时关联的课程
- `lesson_ids`：PostgreSQL ARRAY 存储选中的课时 ID 列表
- `schedule_type`：`"fixed"` = 固定班课，`"custom"` = 1V1 自定义时间
- `seat_id`：改为 nullable，课程预约时为 null

### 2.3 Alembic 迁移

迁移文件需完成：
1. `courses` 表添加 `custom_price` (NUMERIC(10,2) NOT NULL DEFAULT 0) 和 `full_package_price` (NUMERIC(10,2) NULLABLE)
2. `bookings` 表添加 `booking_type` (VARCHAR(20) NOT NULL DEFAULT 'seat')、`course_id` (INTEGER NULLABLE, FK→courses.id)、`lesson_ids` (INTEGER[] NULLABLE)、`schedule_type` (VARCHAR(20) NULLABLE)
3. `bookings.seat_id` 改为 nullable（`alter_column ... nullable=True`）
4. `bookings` 表添加 `booking_type` 索引

## 3. 后端服务层设计

### 3.1 CourseBookingService

```python
# app/services/course_booking_service.py

class CourseBookingService:
    async def get_course_with_lessons(course_id, db) -> CourseWithLessons:
        """查询课程详情 + 课时列表 + 定价信息"""
        
    async def calculate_price(course, booking_type, lesson_ids) -> PriceBreakdown:
        """
        价格计算核心：
        - fixed: len(lesson_ids) × course.price
        - custom: len(lesson_ids) × course.custom_price
        - full_package: 当 len(lesson_ids) == total_lessons 且 full_package_price 存在时
          original_price = full_package_price
          discount_amount = total_lessons × price - full_package_price
        """
        
    async def create_course_booking(user_id, data, db) -> Booking:
        """
        创建课程预约（余额支付）：
        1. 验证课程存在且 status='active'
        2. 验证 lesson_ids 均属于该课程
        3. 计算价格
        4. 验证优惠券（如有）
        5. 创建 booking 记录
        6. 扣减余额
        7. 标记优惠券已使用
        """
        
    async def create_course_booking_wechat(user_id, data, db) -> tuple[Booking, dict]:
        """
        创建课程预约（微信支付）：
        1-5 同上
        6. 调用 booking_payment_service 创建微信支付
        7. 返回 payment_params
        """
        
    async def cancel_course_booking(booking_id, user_id, db) -> Booking:
        """
        取消课程预约：
        1. 复用 booking_service 的取消逻辑（退款计算）
        2. 额外恢复优惠券（如使用了优惠券）
        """
```

### 3.2 价格计算规则

```
输入: course, booking_type, lesson_ids, total_lessons_count
输出: original_price, discount_amount, total_price

if booking_type == 'fixed':
    unit_price = course.price
elif booking_type == 'custom':
    unit_price = course.custom_price

subtotal = len(lesson_ids) × unit_price

# 全套优惠判定
if (len(lesson_ids) == total_lessons_count 
    and course.full_package_price is not null):
    original_price = course.full_package_price
    discount_amount = subtotal - course.full_package_price
else:
    original_price = subtotal
    discount_amount = 0

# 优惠券抵扣
coupon_discount = coupon.face_value if coupon else 0
total_price = max(0, original_price - coupon_discount)
```

### 3.3 与现有服务的集成点

| 现有服务 | 集成方式 | 说明 |
|---------|---------|------|
| `coupon_service` | `validate_coupon()` / `mark_coupon_used()` / `restore_coupon()` | 优惠券验证/使用/恢复 |
| `booking_payment_service` | `create_wechat_payment()` / `handle_payment_notification()` | 微信支付下单/回调 |
| `wallet_service` | `deduct_balance()` / `add_balance()` | 余额扣款/退款 |
| `booking_service` | 取消逻辑参考 | 退款计算、违约金 |

### 3.4 API 路由设计

```python
# app/api/routes/course_booking.py
router = APIRouter()

@router.get("/api/v1/courses/{course_id}/lessons")
async def get_course_lessons(course_id: int, db, current_user):
    """返回课程详情 + 课时列表 + 定价信息"""
    
@router.post("/api/v1/course-bookings")
async def create_course_booking(data: CourseBookingCreate, db, current_user):
    """创建课程预约订单"""
    # 根据 payment_method 分流：
    # - balance: 直接创建已支付预约
    # - wechat: 创建 pending 预约 + 返回 payment_params
```

**请求 Schema**：
```python
class CourseBookingCreate(BaseModel):
    course_id: int
    booking_type: str  # "fixed" | "custom"
    lesson_ids: list[int]
    schedule_type: str  # "fixed" | "custom"
    payment_method: str  # "balance" | "wechat"
    coupon_id: int | None = None
```

**响应 Schema**：
```python
class CourseBookingResponse(BaseModel):
    booking_id: int
    course_name: str
    lesson_count: int
    original_price: float
    discount_amount: float
    total_price: float
    payment_status: str
    payment_params: dict | None = None  # 微信支付时返回
```

### 3.5 列表接口扩展

`GET /api/v1/bookings` 返回数据增加字段：
```python
# 在 BookingResponse 中新增
booking_type: str  # "seat" | "course"
course_name: str | None  # 课程预约时的课程名
lesson_titles: list[str] | None  # 课程预约时的课时标题列表
```

通过 `booking_type` 判断：
- `booking_type == 'seat'`：返回 seat/room 信息（现有逻辑）
- `booking_type == 'course'`：返回 course/lesson 信息（新增逻辑）

### 3.6 取消逻辑扩展

现有 `booking_service.cancel_booking()` 需增加：
- 当 `booking_type == 'course'` 且 `coupon_id` 存在时，调用 `coupon_service.restore_coupon()` 恢复优惠券

## 4. 前端实现设计

### 4.1 页面结构 (course-booking.vue)

```
页面布局（参考 prototype/course-booking.html）：
┌─────────────────────────────┐
│ 导航栏（返回 + 标题）         │
├─────────────────────────────┤
│ 课程信息摘要                  │ ← 封面图 + 名称 + 教师 + 单价
├─────────────────────────────┤
│ 预约类型选择                  │ ← 固定班课 / 1V1 双列卡片
├─────────────────────────────┤
│ 课时选择列表                  │ ← checkbox 多选 + 已选计数
│ └── 全套课时推广条            │ ← 点击查看全套 + 全选 + 优惠
├─────────────────────────────┤
│ 上课时间                      │ ← 固定时间表 / 日期时段选择器
├─────────────────────────────┤
│ 优惠券                        │ ← 选择入口 + 抵扣金额
├─────────────────────────────┤
│ 支付方式                      │ ← 余额 / 微信 radio
├─────────────────────────────┤
│ 价格摘要                      │ ← 课程费 + 优惠券 + 实付
├─────────────────────────────┤
│ 底部操作栏（固定）             │ ← 合计 + 立即支付
└─────────────────────────────┘
```

### 4.2 数据流

```
onLoad(course_id)
  → getCourseLessons(course_id)  // 获取课程+课时+定价
  → getBalance()                 // 获取钱包余额
  → init state

用户交互:
  toggleLesson(id)      → 更新 selectedLessonIds → 重算价格
  selectFullPackage()   → 全选 + 标记 isFullPackage → 重算价格
  switchBookingType(t)  → 更新 bookingType + 单价 → 重算价格
  selectCoupon(c)       → 更新 coupon → 重算价格
  switchPayment(m)      → 更新 paymentMethod

computed priceSummary:
  subtotal = isFullPackage ? full_package_price : selectedCount × unitPrice
  couponDiscount = coupon?.face_value ?? 0
  total = max(0, subtotal - couponDiscount)

submitOrder():
  → createCourseBooking({course_id, booking_type, lesson_ids, ...})
  → [余额] 成功 → 显示成功弹窗 → 跳转订单页
  → [微信] 返回 payment_params → uni.requestPayment → 轮询结果 → 成功弹窗
```

### 4.3 订单列表适配 (orders/index.vue)

修改策略：
- 在订单卡片模板中添加 `v-if/v-else` 条件分支
- `booking_type === 'course'` 时渲染课程信息
- `booking_type === 'seat'` 时保持现有渲染逻辑不变

```html
<!-- 订单头部 -->
<view v-if="item.booking_type === 'course'" class="course-header">
  <text class="course-name">{{ item.course_name }}</text>
  <text class="lesson-info">第{{ item.lesson_titles[0] }} · 共{{ item.lesson_titles.length }}课时</text>
</view>
<view v-else class="seat-header">
  <!-- 现有自习室预约渲染 -->
</view>
```

### 4.4 API 模块 (api/courseBooking.js)

```javascript
import request from '@/utils/request'

export function getCourseLessons(courseId) {
  return request({ url: `/api/v1/courses/${courseId}/lessons`, method: 'GET' })
}

export function createCourseBooking(data) {
  return request({ url: '/api/v1/course-bookings', method: 'POST', data })
}
```

## 5. 已知问题规避清单

| BUG | 规避措施 |
|-----|---------|
| BUG-1: Sass @import | 不在 `<style>` 中 `@import '@/uni.scss'`，uni-app 自动注入 |
| BUG-14: onMounted 导入 | `onMounted` 从 `vue` 导入，不从 `@dcloudio/uni-app` |
| BUG-15: aware/naive datetime | 所有写入数据库的 datetime 使用 `datetime.now()` (naive, Asia/Shanghai) |
| BUG-20: WXML < > 字符 | 使用 Unicode `‹` `›` 替代 HTML 实体 |
| BUG-22: 路由尾部斜杠 | 所有 API 路由定义不带尾部 `/` |

## 6. 测试计划

### 6.1 后端单元测试 (test_course_booking_service.py)

- 价格计算：fixed/custom/full_package 三种模式
- 边界：空 lesson_ids、无效 course_id、部分选择不触发全套优惠
- 优惠券验证：有效券/过期券/已用券
- 余额充足/不足

### 6.2 后端集成测试 (test_api_course_booking.py)

- GET /courses/{id}/lessons：正常/不存在
- POST /course-bookings：余额支付成功/微信支付/优惠券/无效课程/空课时/余额不足
- 取消：已支付退款/待支付取消/优惠券恢复
- GET /bookings：混合列表包含课程预约

### 6.3 前端验证

- 构建通过（无编译错误）
- 原型 UI 一致性手动验证
