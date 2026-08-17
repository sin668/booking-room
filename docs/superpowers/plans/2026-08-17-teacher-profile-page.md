---
change: teacher-profile-page
design-doc: docs/superpowers/specs/2026-08-17-teacher-profile-page-design.md
base-ref: 7ff33ae11cbc0c499c0cd1d11a7a9961b97d8688
---

# 教师简介页面实施计划

## 概述

基于 Design Doc 和 tasks.md，实现教师简介页面功能。包含后端 API、数据库迁移、前端页面和关注功能。

**已知问题规避**（来自 bug-fixed.md）：
- BUG-14: `onMounted` 从 `vue` 导入，不从 `@dcloudio/uni-app` 导入
- BUG-20: 模板中不使用 `<` `>` HTML 实体，使用 Unicode 字符替代
- BUG-22: 后端路由定义不使用尾部斜杠

---

## 阶段 1: 后端 — Teacher 模型扩展与迁移

### 任务 1.1: Teacher 模型新增字段

**目标**: 为 Teacher 模型添加 `bio` 和 `student_count` 字段

**涉及文件**:
- `br-server/app/models/teacher.py` (修改)

**关键实现要点**:
```python
from sqlalchemy import String, Integer

# 在 Teacher 类中新增：
bio: Mapped[str | None] = mapped_column(String(1000), nullable=True)
student_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
```

**依赖**: 无

---

### 任务 1.2: 生成 alembic 迁移文件

**目标**: 为 teachers 表添加 bio 和 student_count 列

**涉及文件**:
- `br-server/alembic/versions/xxx_add_teacher_bio_student_count.py` (新建)

**关键实现要点**:
- 执行 `alembic revision --autogenerate -m "add teacher bio and student_count"`
- 确保 `bio` 使用 `nullable=True`
- 确保 `student_count` 使用 `server_default="0"` 保证存量数据兼容

**依赖**: 任务 1.1

---

### 任务 1.3: 更新 TeacherResponse schema

**目标**: 扩展 TeacherResponse，新增 bio 和 student_count 字段

**涉及文件**:
- `br-server/app/schemas/teacher.py` (修改)

**关键实现要点**:
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

**依赖**: 任务 1.1

---

### 任务 1.4: 更新 TeacherBrief schema

**目标**: 同步更新培训室详情 API 的 TeacherBrief schema

**涉及文件**:
- `br-server/app/schemas/course.py` (修改)

**关键实现要点**:
```python
class TeacherBrief(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0
```

**依赖**: 任务 1.1

---

## 阶段 2: 后端 — 教师详情 API

### 任务 2.1: 新建 TeacherDetailResponse 和 TeacherCourseItem

**目标**: 定义教师详情响应结构

**涉及文件**:
- `br-server/app/schemas/teacher.py` (修改)

**关键实现要点**:
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

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [tag.strip() for tag in v.split(",") if tag.strip()]

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

**依赖**: 任务 1.3

---

### 任务 2.2: 新建 teacher_service.py

**目标**: 实现 get_teacher_detail 方法

**涉及文件**:
- `br-server/app/services/teacher_service.py` (新建)

**关键实现要点**:
- 查询教师基本信息
- 查询关联课程 + 课时计数（一次查询，避免 N+1）
- 使用 `outerjoin(StudyRoom)` 获取 room_name
- 使用 `outerjoin(CourseLesson)` 并 `func.count(CourseLesson.id)` 获取 lesson_count
- 按 `Course.sort_order, Course.id` 排序
- 只返回 `status == "active"` 的课程

**依赖**: 任务 2.1

---

### 任务 2.3: 新建教师详情路由

**目标**: 注册 `GET /api/v1/teachers/{teacher_id}` 端点

**涉及文件**:
- `br-server/app/api/routes/teacher.py` (新建)

**关键实现要点**:
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

**注意**: 不使用尾部斜杠（规避 BUG-22）

**依赖**: 任务 2.2

---

### 任务 2.4: 在 main.py 注册 teacher 路由

**目标**: 将 teacher 路由注册到 FastAPI 应用

**涉及文件**:
- `br-server/app/main.py` (修改)

**关键实现要点**:
```python
from app.api.routes.teacher import router as teacher_router

# 在路由注册区域添加：
app.include_router(teacher_router)
```

**依赖**: 任务 2.3

---

### 任务 2.5: 编写教师详情 API 单元测试

**目标**: 覆盖有课程、无课程、不存在教师场景

**涉及文件**:
- `br-server/tests/test_teacher_detail_api.py` (新建)

**关键实现要点**:
- 测试有课程的教师详情请求 → 200 + courses 非空 + lesson_count 正确
- 测试无课程的教师详情请求 → 200 + courses 为空
- 测试不存在的教师 → 404
- 测试 bio 为 null 的教师 → bio 返回 null
- 测试 tags 字符串正确解析为数组

**依赖**: 任务 2.4

---

## 阶段 3: 后端 — room_follows follow_type 扩展

### 任务 3.1: 扩展 room_follow 路由的 follow_type 参数正则

**目标**: 支持 teacher 类型的关注

**涉及文件**:
- `br-server/app/api/routes/room_follow.py` (修改)

**关键实现要点**:
- 将 3 个端点的 `follow_type` Query 参数正则从 `^(room|course)$` 改为 `^(room|course|teacher)$`

**依赖**: 无

---

### 任务 3.2: 扩展 room_follow_service 支持 teacher 类型

**目标**: follow/unfollow/list 方法支持 teacher 类型

**涉及文件**:
- `br-server/app/services/room_follow_service.py` (修改)

**关键实现要点**:
- `follow_room()` 中新增 teacher 分支：
  - 查询 Teacher 表验证教师存在
  - 不校验 study_rooms 表，直接创建 follow 记录
- `list_followed_rooms()` 中新增 teacher 分支：
  - join teachers 表获取教师信息
  - 返回 FollowedRoomResponse 格式
- `unfollow_room()` 无需修改，已按 follow_type 过滤删除

**依赖**: 任务 3.1

---

### 任务 3.3: 编写 teacher follow 类型单元测试

**目标**: 覆盖关注、取消关注、幂等、类型隔离场景

**涉及文件**:
- `br-server/tests/test_teacher_follow.py` (新建)

**关键实现要点**:
- 测试关注教师 → 201
- 测试重复关注 → 200（幂等）
- 测试取消关注 → 204
- 测试 teacher 类型与 room/course 类型互不干扰
- 测试不存在的教师关注 → 404

**依赖**: 任务 3.2

---

## 阶段 4: 前端 — API 层与服务层

### 任务 4.1: 新建 teacher.js API 封装

**目标**: 封装 getTeacherDetail API

**涉及文件**:
- `br-app/src/api/teacher.js` (新建)

**关键实现要点**:
```javascript
import { get } from '@/utils/request'

export function getTeacherDetail(teacherId) {
  return get(`/api/v1/teachers/${teacherId}`)
}
```

**依赖**: 任务 2.4

---

### 任务 4.2: 新建 followedTeachers.js 服务

**目标**: 实现教师关注/取消关注/状态查询

**涉及文件**:
- `br-app/src/services/followedTeachers.js` (新建)

**关键实现要点**:
- 参照 `followedRooms.js` 模式
- localStorage key: `followed_teachers`
- 导出: `followTeacher(teacher)`, `unfollowTeacher(teacherId)`, `isTeacherFollowed(teacherId)`, `getFollowedTeachers()`
- 乐观更新：先更新本地缓存，API 失败时回滚

**依赖**: 任务 3.2

---

### 任务 4.3: 扩展 roomFollows.js 支持 teacher 类型

**目标**: followRoom/unfollowRoom 支持传入 follow_type='teacher'

**涉及文件**:
- `br-app/src/api/roomFollows.js` (修改)

**关键实现要点**:
- 已有代码已支持 followType 参数，无需修改
- 确认 `followRoom(roomId, followType = 'room')` 可直接传入 `'teacher'`

**依赖**: 任务 3.1

---

## 阶段 5: 前端 — 教师简介页面

### 任务 5.1: 创建 teacher/profile.vue 页面

**目标**: 严格参考原型实现教师简介页面

**涉及文件**:
- `br-app/src/pages/teacher/profile.vue` (新建)

**关键实现要点**:

**组件结构** (Options API):
```javascript
data: teacher, courses, isFav, loading, statusBarHeight
onLoad: 解析 teacher_id 参数，加载数据
computed: heroImage, courseCount, statsData
methods: loadTeacherDetail, onToggleFav, onBackToCourses, onCourseDetail
```

**页面区域**（严格参考原型）:
1. **Hero 区**: 渐变背景 + 教师头像 + 姓名 + 认证标签
2. **统计行**: 学员数量 / 授课课程 / 综合评分（3 列网格）
3. **个人简介**: bio 文本展示
4. **主讲课程列表**: 标题 "主讲课程" + "共X门"，课程卡片列表
   - 卡片结构：封面 + 课程名 + "共X课时 · 含资料" + 评分/学员数 + 价格
5. **学员评价**: 3 条静态评价数据（头像、昵称、五星、内容、时间）
6. **底部操作栏**: 心状关注按钮 + "返回课程"按钮

**注意**:
- 使用 `onLoad` 从 `@dcloudio/uni-app` 导入（页面级生命周期）
- 不使用 `onMounted`（规避 BUG-14）
- 模板中不使用 `<` `>` HTML 实体（规避 BUG-20）

**依赖**: 任务 4.1, 4.2

---

### 任务 5.2: 主讲课程列表卡片结构

**目标**: 复用培训室概况页的课程卡片结构

**涉及文件**:
- `br-app/src/pages/teacher/profile.vue` (修改)

**关键实现要点**:
- 参考 `br-app/src/pages/booking/detail.vue` 的课程卡片结构
- 将"主讲老师"行替换为"共X课时 · 含资料"行
- 课程卡片包含：封面 + 课程名 + 评分/学员数 + 价格

**依赖**: 任务 5.1

---

### 任务 5.3: 实现心状关注按钮交互

**目标**: 右上角 + 底部操作栏的关注按钮

**涉及文件**:
- `br-app/src/pages/teacher/profile.vue` (修改)

**关键实现要点**:
- 右上角固定定位心状按钮
- 底部操作栏心状按钮
- 未关注: 空心心（使用 Unicode ♥ + opacity 区分）
- 已关注: 实心心
- 点击切换，调用 followedTeachers 服务
- 参考 `br-app/src/pages/booking/detail.vue` 的 `onToggleFav` 方法

**依赖**: 任务 5.1

---

### 任务 5.4: 底部"返回课程"按钮跳转

**目标**: 点击跳转到培训课程列表页

**涉及文件**:
- `br-app/src/pages/teacher/profile.vue` (修改)

**关键实现要点**:
```javascript
onBackToCourses() {
  uni.switchTab({ url: '/pages/training/index' })
}
```

**依赖**: 任务 5.1

---

### 任务 5.5: 在 pages.json 注册路由

**目标**: 注册教师简介页面路由

**涉及文件**:
- `br-app/src/pages.json` (修改)

**关键实现要点**:
```json
{
  "path": "pages/teacher/profile",
  "style": {
    "navigationBarTitleText": "老师简介",
    "navigationStyle": "custom"
  }
}
```

**依赖**: 任务 5.1

---

## 阶段 6: 前端 — 课程详情页集成

### 任务 6.1: 修改 course-detail.vue 的 onTeacherTap 方法

**目标**: 点击教师卡片跳转到教师简介页

**涉及文件**:
- `br-app/src/pages/training/course-detail.vue` (修改)

**关键实现要点**:
```javascript
onTeacherTap() {
  if (!this.teacher || !this.teacher.id) return
  uni.navigateTo({
    url: `/pages/teacher/profile?teacher_id=${this.teacher.id}`
  })
}
```

**依赖**: 任务 5.5

---

## 阶段 7: 验证

### 任务 7.1: 后端 pytest 全部通过

**目标**: 确保新增测试 + 回归测试通过

**执行命令**:
```bash
cd br-server
pytest tests/test_teacher_detail_api.py tests/test_teacher_follow.py -v
pytest tests/ -q  # 回归测试
```

**依赖**: 任务 2.5, 3.3

---

### 任务 7.2: 前端构建无错误

**目标**: 确保前端构建通过

**执行命令**:
```bash
cd br-app
npm run build
```

**依赖**: 任务 5.5, 6.1

---

### 任务 7.3: 检查已知问题规避

**目标**: 确认避免 bug-fixed.md 中的 BUG-14/20/22

**检查项**:
- [x] `onMounted` 从 `vue` 导入，不从 `@dcloudio/uni-app` 导入
- [x] 模板中不使用 `<` `>` HTML 实体
- [x] 后端路由定义不使用尾部斜杠

**依赖**: 任务 7.1, 7.2

---

## 文件清单

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

---

## 执行顺序总结

```
阶段 1: 后端模型扩展
  1.1 → 1.2 → 1.3 → 1.4

阶段 2: 后端 API
  2.1 → 2.2 → 2.3 → 2.4 → 2.5

阶段 3: 后端关注扩展
  3.1 → 3.2 → 3.3

阶段 4: 前端 API/服务层
  4.1, 4.2, 4.3 (可并行)

阶段 5: 前端页面
  5.1 → 5.2, 5.3, 5.4 (可并行) → 5.5

阶段 6: 前端集成
  6.1

阶段 7: 验证
  7.1, 7.2, 7.3
```
