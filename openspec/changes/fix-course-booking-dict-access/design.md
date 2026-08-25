## 实现说明

`get_course_with_lessons` 返回 `course` 为 dict（第 81-107 行构建），但 `create_course_booking` 中 5 处使用了 ORM 风格的点号访问。

修复方式：将所有 `course.xxx` 改为 `course["xxx"]`。

涉及行：
- L256: `course.status` → `course["status"]`
- L313: `course.room_id` → `course["room_id"]`
- L329: `course.id` → `course["id"]`
- L338: `course.id` → `course["id"]`
- L391: `course.name` → `course["name"]`

无需修改 `calculate_price`，因其未实际使用 `course` 参数体。
