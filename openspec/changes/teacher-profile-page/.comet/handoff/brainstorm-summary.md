# Brainstorm Summary

- Change: teacher-profile-page
- Date: 2026-08-17

## 确认的技术方案

- Teacher 模型新增 bio (String(1000), nullable) 和 student_count (Integer, default=0) 列
- 教师详情 API: GET /api/v1/teachers/{teacher_id}，使用 outerjoin + group_by 一次查询课程和课时计数
- room_follows follow_type 扩展支持 teacher，teacher 类型校验 teachers 表存在性
- 前端页面 pages/teacher/profile.vue，Options API，参照原型实现
- 前端服务 followedTeachers.js，独立 localStorage key
- 课程卡片复用 booking/detail.vue 的课程列表样式，替换主讲老师行为"共X课时·含资料"

## 关键取舍与风险

- room_follows.room_id 在 teacher 类型中存储 teacher_id，通过代码注释文档化
- lesson_count 使用 outerjoin + group_by 而非冗余字段，避免数据一致性问题
- 静态评价数据后续替换为真实 API 时只需替换数据源

## 测试策略

- 后端: test_teacher_detail_api.py (集成测试), test_teacher_follow.py (单元测试)
- 前端: 构建验证 + 避免已知 bug (BUG-14/20/22)

## Spec Patch

无
