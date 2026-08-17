# 设计说明

## 后端变更

### Course 模型新增字段

在 `br-server/app/models/course.py` 的 `Course` 模型中新增：

```python
full_custom_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
```

### 数据库迁移

创建 Alembic 迁移文件，为 `courses` 表添加 `full_custom_price` 列。

### API 响应

CourseDetailResponse 已包含课程所有字段，新增字段会自动包含在响应中。

## 前端变更

### 全套优惠价格逻辑

在 `course-booking.vue` 的 `priceSummary` 计算属性中：
- `bookingType === 'fixed'` 时使用 `courseInfo.full_package_price`
- `bookingType === 'custom'` 时使用 `courseInfo.full_custom_price`

### 1V1 私人定制时间选择器

替换原有的"选择课时后可与老师协商上课时间"提示，改为：
1. 横向滚动的周几选择器（周一~周日，显示日期）
2. 时间段网格（08:00-10:00, 10:00-12:00, ..., 20:00-22:00）
3. 单选周几的某一个时间段

样式参考 `br-app/src/pages/booking/seat-select.vue` 的日期和时间选择器。
