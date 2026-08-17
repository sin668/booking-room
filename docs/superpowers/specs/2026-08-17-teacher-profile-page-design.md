---
comet_change: teacher-profile-page
role: technical-design
canonical_spec: openspec
---

# 教师简介页面技术设计

## 1. 概述

在 br-app 新增教师简介页面，展示教师信息、主讲课程列表和学员评价。后端新增教师详情 API，扩展 room_follows 支持 teacher 关注类型。严格参考 `prototype/teacher-profile.html` 原型设计。

## 2. 后端实现设计

### 2.1 Teacher 模型扩展

**文件**: `br-server/app/models/teacher.py`

新增两个字段：

```python
bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
```

**迁移**: alembic 自动生成，`bio` 使用 `nullable=True`，`student_count` 使用 `server_default="0"` 保证存量数据兼容。

### 2.2 Schema 扩展

**文件**: `br-server/app/schemas/teacher.py`

扩展 `TeacherResponse`：

```python
class TeacherResponse(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0
```

新增教师详情响应和课程项：

```python
class TeacherCourseItem(BaseModel):
    id: int
    name: str
    cover_image: str | None = None
    category: str
    price: Decimal
    rating: Decimal
    enrollment_count: int
    schedule: str | None = None
    tags: list[str] = []
    status: str
    room_id: int
    room_name: str
    lesson_count: int = 0

class TeacherDetailResponse(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0
    courses: list[TeacherCourseItem] = []
```

**文件**: `br-server/app/schemas/course.py`

`TeacherBrief`（嵌套在培训室详情响应中）同步新增 `bio` 和 `student_count`。

### 2.3 教师详情服务

**文件**: `br-server/app/services/teacher_service.py`

```python
async def get_teacher_detail(db: AsyncSession, teacher_id: int) -> TeacherDetailResponse | None:
    # 1. 查询教师基本信息
    teacher = await db.get(Teacher, teacher_id)
    if not teacher:
        return None

    # 2. 查询关联课程 + 课时计数（一次查询，避免 N+1）
    query = (
        select(
            Course,
            StudyRoom.name.label("room_name"),
            func.count(CourseLesson.id).label("lesson_count")
        )
        .outerjoin(StudyRoom, Course.room_id == StudyRoom.id)
        .outerjoin(CourseLesson, Course.id == CourseLesson.course_id)
        .where(
            Course.teacher_id == teacher_id,
            Course.status == "active"
        )
        .group_by(Course.id, StudyRoom.name)
        .order_by(Course.sort_order, Course.id)
    )
    result = await db.execute(query)
    courses = [
        TeacherCourseItem(
            id=course.id,
            name=course.name,
            cover_image=course.cover_image,
            category=course.category,
            price=course.price,
            rating=course.rating,
            enrollment_count=course.enrollment_count,
            schedule=course.schedule,
            tags=parse_tags(course.tags),
            status=course.status,
            room_id=course.room_id,
            room_name=row.room_name or "",
            lesson_count=row.lesson_count,
        )
        for course, row in result  # 注意：实际实现需正确解包
    ]

    return TeacherDetailResponse(
        id=teacher.id,
        name=teacher.name,
        avatar=teacher.avatar,
        title=teacher.title,
        rating=teacher.rating,
        bio=teacher.bio,
        student_count=teacher.student_count,
        courses=courses,
    )
```

### 2.4 教师详情路由

**文件**: `br-server/app/api/routes/teacher.py`

```python
router = APIRouter(prefix="/api/v1/teachers", tags=["teachers"])

@router.get("/{teacher_id}", response_model=TeacherDetailResponse)
async def get_teacher_detail(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
):
    result = await teacher_service.get_teacher_detail(db, teacher_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return result
```

在 `main.py` 注册路由。

### 2.5 room_follows follow_type 扩展

**路由层** (`room_follow.py`)：3 个端点的 `follow_type` Query 参数正则：

```python
follow_type: str = Query("room", pattern="^(room|course|teacher)$")
```

**服务层** (`room_follow_service.py`)：

`follow_room()` 中新增 teacher 分支：

```python
if follow_type == "teacher":
    teacher = await db.get(Teacher, room_id)
    if teacher is None:
        raise ValueError(f"Teacher {room_id} not found")
    # 继续创建 follow 记录...
```

`list_followed_rooms()` 中新增 teacher 分支，join teachers 表获取教师信息。

`unfollow_room()` 无需修改，已按 follow_type 过滤删除。

## 3. 前端实现设计

### 3.1 API 层

**文件**: `br-app/src/api/teacher.js`

```javascript
import { get } from '@/utils/request'

export function getTeacherDetail(teacherId) {
  return get(`/api/v1/teachers/${teacherId}`)
}
```

### 3.2 关注服务

**文件**: `br-app/src/services/followedTeachers.js`

参照 `followedRooms.js` 模式：
- localStorage key: `followed_teachers`
- 导出: `followTeacher(teacher)`, `unfollowTeacher(teacherId)`, `isTeacherFollowed(teacherId)`, `getFollowedTeachers()`
- 乐观更新：先更新本地缓存，API 失败时回滚

### 3.3 教师简介页面

**文件**: `br-app/src/pages/teacher/profile.vue`

**组件结构** (Options API)：

```
data: teacher, courses, isFav, loading, statusBarHeight
onLoad: 解析 teacher_id 参数，加载数据
computed: heroImage, courseCount, statsData
methods: loadTeacherDetail, onToggleFav, onBackToCourses, onCourseDetail
```

**页面区域**（严格参考原型）：

1. **Hero 区**: 渐变背景 + 教师头像 + 姓名 + 认证标签
2. **统计行**: 学员数量 / 授课课程 / 综合评分（3 列网格）
3. **个人简介**: bio 文本展示
4. **主讲课程列表**: 标题 "主讲课程" + "共X门"，课程卡片列表
   - 卡片结构：封面 + 课程名 + "共X课时 · 含资料" + 评分/学员数 + 价格
5. **学员评价**: 3 条静态评价数据（头像、昵称、五星、内容、时间）
6. **底部操作栏**: 心状关注按钮 + "返回课程"按钮（switchTab 到 /pages/training/index）

**关注按钮交互**：
- 右上角固定定位心状按钮
- 未关注: 空心心（使用 Unicode ♥ + opacity 区分）
- 已关注: 实心心
- 点击切换，调用 followedTeachers 服务

### 3.4 课程详情页集成

**文件**: `br-app/src/pages/training/course-detail.vue`

```javascript
onTeacherTap() {
  if (!this.teacher || !this.teacher.id) return
  uni.navigateTo({
    url: `/pages/teacher/profile?teacher_id=${this.teacher.id}`
  })
}
```

### 3.5 路由注册

**文件**: `br-app/src/pages.json`

```json
{
  "path": "pages/teacher/profile",
  "style": {
    "navigationBarTitleText": "老师简介",
    "navigationStyle": "custom"
  }
}
```

## 4. 已知问题规避

参照 `bug-fixed.md`，实现过程中注意：

| BUG | 规避措施 |
|-----|---------|
| BUG-14 | `onMounted` 从 `vue` 导入，不从 `@dcloudio/uni-app` 导入 |
| BUG-20 | 模板中不使用 `<` `>` HTML 实体，使用 Unicode 字符替代 |
| BUG-22 | 后端路由定义不使用尾部斜杠 |
| BUG-15 | datetime 统一使用 naive datetime（Asia/Shanghai） |

## 5. 测试计划

### 后端测试

**`tests/test_teacher_detail_api.py`**:
- 有课程的教师详情请求 → 200 + courses 非空 + lesson_count 正确
- 无课程的教师详情请求 → 200 + courses 为空
- 不存在的教师 → 404
- bio 为 null 的教师 → bio 返回 null
- tags 字符串正确解析为数组

**`tests/test_teacher_follow.py`**:
- 关注教师 → 201
- 重复关注 → 200（幂等）
- 取消关注 → 204
- teacher 类型与 room/course 类型互不干扰
- 不存在的教师关注 → 404

### 前端验证

- `npm run build` 构建通过
- 页面路由正确注册
- 课程详情页教师卡点击正确跳转

## 6. 文件清单

| 模块 | 操作 | 文件 |
|------|------|------|
| br-server | 修改 | `app/models/teacher.py` |
| br-server | 新建 | `alembic/versions/xxx_add_teacher_bio_student_count.py` |
| br-server | 修改 | `app/schemas/teacher.py` |
| br-server | 修改 | `app/schemas/course.py` (TeacherBrief) |
| br-server | 新建 | `app/services/teacher_service.py` |
| br-server | 新建 | `app/api/routes/teacher.py` |
| br-server | 修改 | `app/main.py` |
| br-server | 修改 | `app/api/routes/room_follow.py` |
| br-server | 修改 | `app/services/room_follow_service.py` |
| br-server | 新建 | `tests/test_teacher_detail_api.py` |
| br-server | 新建 | `tests/test_teacher_follow.py` |
| br-app | 新建 | `src/api/teacher.js` |
| br-app | 新建 | `src/services/followedTeachers.js` |
| br-app | 新建 | `src/pages/teacher/profile.vue` |
| br-app | 修改 | `src/pages.json` |
| br-app | 修改 | `src/pages/training/course-detail.vue` |
