# Task 4 Report: 后端课程详情 API

## 状态: DONE

所有 6 个子任务已完成，TDD 循环验证通过，无回归。

---

## 创建/修改的文件

### 修改的文件
| 文件 | 子任务 | 变更说明 |
|------|--------|----------|
| `br-server/app/models/course.py` | 4.1 | 添加 `description: Mapped[str | None]` 字段 |
| `br-server/app/models/room_follow.py` | 4.2 | 添加 `follow_type` 字段，删除 `room_id` FK，更新唯一约束 |
| `br-server/app/schemas/course.py` | 4.3 | 新增 `RoomBrief`、`RelatedCourseItem`、`CourseDetailResponse` |
| `br-server/app/services/training_service.py` | 4.4 | 新增 `get_course_detail()` 方法 |
| `br-server/app/api/routes/training.py` | 4.5 | 新增 `GET /courses/{course_id}` 端点 |
| `br-server/alembic/env.py` | - | 补充导入缺失的模型（Course, CourseLesson, Teacher, RoomFollow, City） |
| `br-app/src/api/training.js` | 4.6 | 新增 `getCourseDetail()` 前端 API 封装 |

### 创建的文件
| 文件 | 说明 |
|------|------|
| `br-server/tests/test_course_detail.py` | 17 个 TDD 测试（Schema/Service/Route） |
| `br-server/alembic/versions/2026_08_17_1000-b3c4d5e6f7a8_add_course_description_and_room_follow_type.py` | 数据库迁移 |

---

## TDD 测试证据

### Red 阶段（测试失败）

**Schema 测试（4.3）**:
```
tests/test_course_detail.py::TestCourseDetailSchemas::test_roombrief_creation
E   ImportError: cannot import name 'RoomBrief' from 'app.schemas.course'
FAILED 1 failed in 0.17s
```

**Service 测试（4.4）**:
```
tests/test_course_detail.py::TestGetCourseDetailService::test_returns_full_detail
E   ImportError: cannot import name 'get_course_detail' from 'app.services.training_service'
FAILED 1 failed in 0.66s
```

**Route 测试（4.5）**:
```
tests/test_course_detail.py::TestCourseDetailRoute::test_get_course_detail_200
E   assert 404 == 200
FAILED 1 failed in 0.18s
```

### Green 阶段（测试通过）

**Schema 测试**:
```
tests/test_course_detail.py::TestCourseDetailSchemas::test_roombrief_creation PASSED
tests/test_course_detail.py::TestCourseDetailSchemas::test_roombrief_cover_image_optional PASSED
tests/test_course_detail.py::TestCourseDetailSchemas::test_relatedcourseitem_creation PASSED
tests/test_course_detail.py::TestCourseDetailSchemas::test_course_detail_response_creation PASSED
tests/test_course_detail.py::TestCourseDetailSchemas::test_course_detail_tags_validator PASSED
============================== 5 passed in 0.03s ===============================
```

**Service 测试**:
```
tests/test_course_detail.py::TestGetCourseDetailService::test_returns_full_detail PASSED
tests/test_course_detail.py::TestGetCourseDetailService::test_course_not_found PASSED
tests/test_course_detail.py::TestGetCourseDetailService::test_inactive_course_returns_none PASSED
tests/test_course_detail.py::TestGetCourseDetailService::test_no_teacher_returns_none_teacher PASSED
tests/test_course_detail.py::TestGetCourseDetailService::test_no_lessons_returns_empty_list PASSED
tests/test_course_detail.py::TestGetCourseDetailService::test_no_related_courses PASSED
============================== 6 passed in 0.90s ===============================
```

**Route 测试**:
```
tests/test_course_detail.py::TestCourseDetailRoute::test_get_course_detail_200 PASSED
tests/test_course_detail.py::TestCourseDetailRoute::test_get_course_detail_404 PASSED
tests/test_course_detail.py::TestCourseDetailRoute::test_get_course_detail_inactive_404 PASSED
tests/test_course_detail.py::TestCourseDetailRoute::test_course_detail_response_fields PASSED
tests/test_course_detail.py::TestCourseDetailRoute::test_lessons_sorted_by_sort_order PASSED
tests/test_course_detail.py::TestCourseDetailRoute::test_related_courses_max_6 PASSED
============================== 6 passed in 0.46s ===============================
```

**全部 17 个新测试**:
```
============================== 17 passed in 1.09s ==============================
```

**现有 training 测试无回归**:
```
56 passed in 3.81s
```

**全量测试**:
```
747 passed, 3 failed (预先存在的失败，与本次变更无关)
```

---

## 实现要点

### 路由顺序
`/courses/{course_id}` 正确放置在 `/courses` 之后、`/rooms/{room_id}` 之前，符合 brief 要求。

### 全局约束遵守
- ✅ 无 HTML 实体使用
- ✅ 路由不带尾部斜杠
- ✅ SQLAlchemy 2.0 Mapped 风格
- ✅ Pydantic v2 ConfigDict(from_attributes=True)

### 迁移说明
- `courses.description`: 新增 nullable 列
- `room_follows.follow_type`: 新增 NOT NULL 列，默认值 "room"
- `room_follows`: 删除 `room_id` 外键约束，删除旧唯一约束，新建三字段唯一约束

---

## 关注事项

1. **预先存在的测试失败**（非本次引入）：
   - `test_schemas_import.py::test_import_course_schemas` - `TrainingRoomResponse` 缺少 `rating` 字段
   - `test_activity_coupon_campaign.py` - 2 个活动卡券相关测试

2. **数据库迁移**：已生成但尚未在 PostgreSQL 上执行验证。部署时需运行 `alembic upgrade head`。

---

## Commit

`ca32c03` feat: implement course detail API with TDD
