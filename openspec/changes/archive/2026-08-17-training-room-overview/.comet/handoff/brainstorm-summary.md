# Brainstorm Summary

- Change: training-room-overview
- Date: 2026-08-14

## 确认的技术方案

方案 A：分步查询 + 前端条件渲染。

后端 `get_training_room_detail(room_id)` 分步查询：
1. 查询 StudyRoom 表验证 room_type ∈ (training, comprehensive)
2. 查询 Course 表（room_id 匹配，status=active），LEFT JOIN Teacher 表，按 sort_order 排序
3. Python 层面从课程列表提取去重教师（按 teacher_id 去重）
4. Python 层面聚合统计（classroom_count=课程数、teacher_count=去重教师数、total_students=enrollment_count 求和、class_capacity="8-12"）

前端 detail.vue 修改：
- data() 新增 trainingData、roomType
- loadData() 先获取房间信息，根据 room_type 条件调用后续 API（study→getSeatStats、training→getTrainingRoomDetail、comprehensive→Promise.all）
- computed 封装 isTrainingRoom/isComprehensiveRoom/trainingStats/teachers/courses
- 模板 v-if 条件渲染：培训室简介、教室概况（2x2 网格）、名师团队（横向 scroll-view）、课程列表（纵向）
- 底部操作栏条件渲染：study→关注+立即预约、training→关注+返回课程、comprehensive→关注+预约自习室

页面区块（按原型图，去掉教学设施网格）：培训室简介、环境照片、教室概况、名师团队、课程列表。

## 关键取舍与风险

- 综合室需两个 API 并行调用（Promise.all），性能可接受
- 依赖 training-course-list change 的数据库迁移（room_type 列、teachers 表、courses 表）
- API 路由不使用尾部斜杠（BUG-22）
- Vue3 生命周期钩子从 vue 包导入（BUG-14）
- 不使用 &lt;/&gt; HTML 实体（BUG-20）
- 不使用 page_size=100 列表接口反查（BUG-13）

## 测试策略

- 后端单元测试：8 个测试场景（正常请求、综合室、404×2、教师去重、空课程、tags 解析、无教师、字段完整性）
- 前端构建验证：npm run build 无编译错误
- 回归验证：现有自习室详情页行为不受影响

## Spec Patch

无。open 阶段 specs 已覆盖所有验收场景。
