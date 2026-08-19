# 任务清单

## Task 1: 后端 Course 模型新增 full_custom_price 字段

- [x] 在 `br-server/app/models/course.py` 的 `Course` 模型中添加 `full_custom_price` 字段
- [x] 创建 Alembic 迁移文件
- [x] 运行迁移验证

## Task 2: 前端全套优惠价格逻辑调整

- [x] 修改 `course-booking.vue` 的 `priceSummary` 计算属性
- [x] 根据 `bookingType` 使用不同的全套优惠价格字段
- [x] 更新 `fullPackageSaveAmount` 计算属性

## Task 3: 1V1 私人定制时间选择器 UI

- [x] 替换原有的自定义时间提示为时间选择器
- [x] 实现周几选择器（横向滚动，显示日期）
- [x] 实现时间段网格（3 列布局）
- [x] 添加选中状态样式
- [x] 参考 seat-select.vue 的样式实现

## Task 4: 验证与构建

- [x] 前端构建验证
- [x] 后端 API 验证
- [x] 提交 GitHub
