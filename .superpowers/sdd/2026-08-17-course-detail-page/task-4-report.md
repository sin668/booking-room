# Task 4 修复报告

## 修复日期
2026-08-17

## Review 来源
`.superpowers/sdd/2026-08-17-course-detail-page/task-4-review.md`

---

## 🔴 Critical: Alembic 迁移 revision ID 冲突

### 问题描述
1. 新迁移 `b3c4d5e6f7a8` 与已有迁移 `2026_08_14_1000-add_room_type_teachers_courses.py` 使用了相同的 revision ID
2. 旧迁移 `a3f7c9d1e2b4`（来自 commit `ea02245`）未清理，与本次迁移存在大量重叠操作
3. `down_revision` 指向错误的父迁移 `a2b3c4d5e6f7`，而正确的 head 应为 `fccf087f0f34`

### 修复操作
1. **删除旧迁移文件**：
   - `br-server/alembic/versions/2026_08_17_1000-a3f7c9d1e2b4_add_course_lessons_and_follow_type.py`

2. **删除冲突的迁移文件**：
   - `br-server/alembic/versions/2026_08_17_1000-b3c4d5e6f7a8_add_course_description_and_room_follow_type.py`

3. **创建新迁移文件**（唯一 revision ID）：
   - `br-server/alembic/versions/2026_08_17_1000-c4d5e6f7a8b9_add_course_description_and_room_follow_type.py`
   - revision: `c4d5e6f7a8b9`
   - down_revision: `fccf087f0f34`（正确的父迁移）

4. **修复 downgrade 函数 bug**：
   - `op.create_unique_constraint()` 的 `table_name` 参数位置错误，改为位置参数

5. **数据库状态同步**：
   - 直接更新 `alembic_version` 表从 `a3f7c9d1e2b4` 到 `c4d5e6f7a8b9`

### 验证结果
```bash
$ alembic heads
c4d5e6f7a8b9 (head)

$ alembic current
c4d5e6f7a8b9 (head)

$ alembic downgrade -1 && alembic upgrade head
# 双向迁移成功
```

---

## 🟡 Warning: inactive 课程路由测试未使用真实数据

### 问题描述
`test_get_course_detail_inactive_404` 使用硬编码 ID `99998`，未真正验证 inactive → 404 路径。

### 修复操作
1. **更新 seed fixture**：
   - `seed_course_detail_data` 现在返回 `inactive_course_id`

2. **更新测试用例**：
   - `test_get_course_detail_inactive_404` 使用 fixture 返回的真实 inactive 课程 ID

### 代码变更
```python
# fixture 返回值
return {
    "course_id": course.id,
    "room_id": room.id,
    "teacher_id": teacher.id,
    "inactive_course_id": inactive.id,  # 新增
}

# 测试用例
async def test_get_course_detail_inactive_404(
    self, client: AsyncClient, seed_course_detail_data
):
    """已下线课程返回 404。"""
    ids = seed_course_detail_data
    resp = await client.get(f"/api/v1/training/courses/{ids['inactive_course_id']}")
    assert resp.status_code == 404
```

---

## 额外修复

### test_schemas_import.py 修复
`test_import_course_schemas` 测试缺少 `TrainingRoomResponse.rating` 字段，补充该必填字段。

---

## 测试结果

### 课程详情测试 (17 tests)
```
tests/test_course_detail.py: 17 passed ✅
```

### 所有 training 相关测试 (93 tests)
```
tests/ -k "training or course": 93 passed ✅
```

### 迁移验证
```
alembic heads: c4d5e6f7a8b9 (head) ✅
alembic downgrade -1 && alembic upgrade head: 成功 ✅
```

---

## 变更文件清单

| 文件 | 操作 |
|------|------|
| `br-server/alembic/versions/2026_08_17_1000-a3f7c9d1e2b4_add_course_lessons_and_follow_type.py` | 删除 |
| `br-server/alembic/versions/2026_08_17_1000-b3c4d5e6f7a8_add_course_description_and_room_follow_type.py` | 删除 |
| `br-server/alembic/versions/2026_08_17_1000-c4d5e6f7a8b9_add_course_description_and_room_follow_type.py` | 新建 |
| `br-server/tests/test_course_detail.py` | 修改 |
| `br-server/tests/test_schemas_import.py` | 修改 |

---

## 最终状态
✅ 所有 Review 问题已修复
✅ 所有测试通过
✅ 迁移链正确，双向迁移验证通过
