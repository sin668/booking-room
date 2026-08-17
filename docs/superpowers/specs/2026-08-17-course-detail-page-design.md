---
comet_change: course-detail-page
role: technical-design
canonical_spec: openspec
---

# 课程详情页 — 深度技术设计

## 1. 架构概览

```
┌─────────────────────────────────────────────────────────────┐
│  br-app (uni-app / Vue3 Options API)                        │
│                                                             │
│  training/index.vue ──tap──→ course-detail.vue              │
│       │                        │                            │
│       │                   ┌────┴────┐                       │
│       │                   │ API 层  │                       │
│       │                   └────┬────┘                       │
│       │            ┌───────────┼───────────┐               │
│       │            ▼           ▼           ▼               │
│       │    training.js   roomFollows.js  followedCourses.js│
│       │            │           │           │               │
└───────┼────────────┼───────────┼───────────┼───────────────┘
        │            ▼           ▼           ▼
        │     ┌──────────────────────────────────┐
        │     │  br-server (FastAPI)              │
        │     │                                    │
        │     │  /api/v1/training/courses/{id}    │
        │     │  /api/v1/room-follows (扩展)      │
        │     │                                    │
        │     │  training_service.get_course_detail│
        │     │  room_follow_service (follow_type) │
        │     └──────────────┬─────────────────────┘
        │                    ▼
        │     ┌──────────────────────────────────┐
        │     │  PostgreSQL 18                    │
        │     │  courses / course_lessons         │
        │     │  room_follows (follow_type)       │
        │     │  teachers / study_rooms           │
        │     └──────────────────────────────────┘
```

## 2. 数据库设计

### 2.1 course_lessons 表

```sql
CREATE TABLE course_lessons (
    id          SERIAL PRIMARY KEY,
    course_id   INTEGER NOT NULL REFERENCES courses(id) ON DELETE CASCADE,
    title       VARCHAR(200) NOT NULL,
    description VARCHAR(500),
    duration_minutes INTEGER,
    sort_order  INTEGER NOT NULL DEFAULT 0,
    is_free_preview BOOLEAN NOT NULL DEFAULT FALSE,
    created_at  TIMESTAMP NOT NULL DEFAULT NOW(),
    updated_at  TIMESTAMP NOT NULL DEFAULT NOW()
);

CREATE INDEX ix_course_lessons_course_id ON course_lessons(course_id);
```

**CourseLesson 模型**（`br-server/app/models/course_lesson.py`）：

```python
class CourseLesson(Base):
    __tablename__ = "course_lessons"
    __table_args__ = (
        Index("ix_course_lessons_course_id", "course_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    title: Mapped[str] = mapped_column(String(200), nullable=False)
    description: Mapped[str | None] = mapped_column(String(500), nullable=True)
    duration_minutes: Mapped[int | None] = mapped_column(Integer, nullable=True)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    is_free_preview: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
```

### 2.2 courses 表新增 description

```python
# Course 模型新增字段
description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
```

### 2.3 room_follows 表改造

**迁移步骤**（顺序关键）：

1. 添加 `follow_type` 列：`String(20)`, `server_default='room'`, `nullable=False`
2. 删除旧唯一约束 `uq_room_follows_user_room`
3. 创建新唯一约束 `uq_room_follows_user_room_type(user_id, room_id, follow_type)`
4. 删除外键约束 `room_follows_room_id_fkey`（`ALTER TABLE ... DROP CONSTRAINT`）

**模型变更**：

```python
class RoomFollow(Base):
    __tablename__ = "room_follows"
    __table_args__ = (
        UniqueConstraint("user_id", "room_id", "follow_type",
                         name="uq_room_follows_user_room_type"),
        Index("ix_room_follows_user_id_created_at", "user_id", "created_at"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    room_id: Mapped[int] = mapped_column(Integer, nullable=False, index=True)  # 删除 ForeignKey
    follow_type: Mapped[str] = mapped_column(
        String(20), default="room", nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), nullable=False
    )
```

**边界条件**：
- 现有数据 `follow_type` 自动填充为 `'room'`（server_default）
- 不传 `follow_type` 时默认 `'room'`，现有 API 完全向后兼容
- `follow_type=course` 时 `room_id` 实际存储 `course_id`，应用层校验 target 存在性

### 2.4 Alembic 迁移文件

单个迁移文件，`upgrade()` 按顺序执行上述所有变更。`downgrade()` 逆序恢复：
1. 恢复 `room_follows.room_id` 外键约束（指向 `study_rooms.id`）
2. 恢复唯一约束 `uq_room_follows_user_room`
3. 删除 `follow_type` 列
4. 删除 `course_lessons` 表
5. 删除 `courses.description` 列

## 3. 后端 API 设计

### 3.1 课程详情端点

**路由**：`GET /api/v1/training/courses/{course_id}`

**`get_course_detail()` 服务方法**（3 步查询，避免 N+1）：

```
Step 1: SELECT courses + LEFT JOIN teachers + JOIN study_rooms
        WHERE courses.id = X AND courses.status = 'active'
        → 获取课程基本信息 + 教师 + 教室

Step 2: SELECT course_lessons
        WHERE course_id = X ORDER BY sort_order ASC
        → 获取课时列表

Step 3: SELECT courses (id, name, cover_image, price)
        WHERE category = <step1.category> AND id != X AND status = 'active'
        ORDER BY sort_order LIMIT 6
        → 获取相关课程
```

**错误处理**：
- Step 1 返回 None → 404（课程不存在或非 active）

**Schema 层次**：

```python
class LessonResponse(BaseModel):
    id: int
    title: str
    description: str | None = None
    duration_minutes: int | None = None
    sort_order: int
    is_free_preview: bool = False
    model_config = ConfigDict(from_attributes=True)

class RoomBrief(BaseModel):
    """轻量教室信息，嵌套在课程详情中"""
    id: int
    name: str
    address: str
    cover_image: str | None = None
    model_config = ConfigDict(from_attributes=True)

class RelatedCourseItem(BaseModel):
    """相关课程推荐项"""
    id: int
    name: str
    cover_image: str | None = None
    price: Decimal
    model_config = ConfigDict(from_attributes=True)

class CourseDetailResponse(BaseModel):
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
    is_hot: bool = False
    description: str | None = None
    teacher: TeacherBrief | None = None
    room: RoomBrief | None = None
    lessons: list[LessonResponse] = []
    related_courses: list[RelatedCourseItem] = []

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None or v == "":
            return []
        return [tag.strip() for tag in v.split(",") if tag.strip()]
```

### 3.2 关注 API 扩展

**路由变更**（添加 `follow_type` 查询参数）：

```python
@router.get("", response_model=FollowedRoomListResponse)
async def list_followed_rooms(
    follow_type: str = Query("room"),  # 新增
    ...
)

@router.post("/{room_id}", response_model=FollowedRoomResponse)
async def follow_room(
    room_id: int,
    follow_type: str = Query("room"),  # 新增
    ...
)

@router.delete("/{room_id}")
async def unfollow_room(
    room_id: int,
    follow_type: str = Query("room"),  # 新增
    ...
)
```

**服务层变更**：

```python
async def list_followed_rooms(db, user_id, follow_type="room"):
    # 添加 .where(RoomFollow.follow_type == follow_type)
    # follow_type="room" 时 JOIN study_rooms
    # follow_type="course" 时 JOIN courses（后续实现，当前只需参数透传）

async def follow_room(db, user_id, room_id, follow_type="room"):
    # 查询时添加 .where(RoomFollow.follow_type == follow_type)
    # follow_type="room" 时校验 study_rooms 存在
    # follow_type="course" 时校验 courses 存在

async def unfollow_room(db, user_id, room_id, follow_type="room"):
    # 删除时添加 .where(RoomFollow.follow_type == follow_type)
```

**边界条件**：
- `follow_type` 只接受 `room` 和 `course`，其他值返回 422
- 同一 `user_id + room_id` 但不同 `follow_type` 可并存（唯一约束允许）
- 关注课程时，target 存在性校验查 `courses` 表而非 `study_rooms`

### 3.3 前端 API 层

**`br-app/src/api/training.js`** 新增：

```javascript
export async function getCourseDetail(courseId) {
  const res = await request(`/api/v1/training/courses/${courseId}`)
  return res.data
}
```

**`br-app/src/api/roomFollows.js`** 扩展：

```javascript
// 所有方法添加 followType 参数
export async function persistFollowRoom(roomId, followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  const res = await request.post(`/api/v1/room-follows/${roomId}${params}`)
  return res.data
}

export async function persistUnfollowRoom(roomId, followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  await request.delete(`/api/v1/room-follows/${roomId}${params}`)
}

export async function fetchPersistedFollowedRooms(followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  const res = await request.get(`/api/v1/room-follows${params}`)
  return res.data
}
```

## 4. 前端设计

### 4.1 course-detail.vue 组件结构

**代码风格**：Options API（与 `booking/detail.vue` 一致）

**数据流**：

```
onLoad(options)
  ├── course_id = options.course_id
  ├── isFav = isCourseFollowed(course_id)
  └── loadCourseDetail()
        └── getCourseDetail(course_id)
              ├── course = data (基本信息)
              ├── teacher = data.teacher
              ├── room = data.room
              ├── lessons = data.lessons
              ├── relatedCourses = data.related_courses
              └── lessonCount = lessons.length
```

**data 结构**：

```javascript
data() {
  return {
    statusBarHeight: 0,
    courseId: null,
    course: {},
    teacher: null,
    room: null,
    lessons: [],
    relatedCourses: [],
    loading: true,
    isFav: false,
    lessonsExpanded: false,
    // 静态评价占位数据
    reviews: [
      { name: '张同学', rating: 5, content: '课程内容很充实，老师讲解很到位...', date: '2025-12-01' },
      { name: '李同学', rating: 4, content: '整体不错，希望能增加更多实操环节...', date: '2025-11-20' },
    ],
  }
}
```

**computed**：

```javascript
computed: {
  displayLessons() {
    if (this.lessonsExpanded || this.lessons.length <= 4) return this.lessons
    return this.lessons.slice(0, 4)
  },
  heroImage() {
    return this.course.cover_image || ''
  },
  tagsList() {
    const tags = this.course.tags || []
    if (this.course.is_hot) tags.unshift('热销')
    return tags
  },
}
```

**关注交互**（与 `booking/detail.vue` 的 `onToggleFav` 模式一致）：

```javascript
async onToggleFav() {
  if (!this.courseId) return
  if (this.isFav) {
    try {
      await unfollowCourse(this.courseId)
      this.isFav = false
      uni.showToast({ title: '已取消关注', icon: 'none' })
    } catch {
      uni.showToast({ title: '取消关注失败，请重试', icon: 'none' })
    }
    return
  }
  try {
    await followCourse({
      id: this.courseId,
      name: this.course.name,
      cover_image: this.course.cover_image,
      price: this.course.price,
    })
    this.isFav = true
    uni.showToast({ title: '已加入关注课程', icon: 'none' })
  } catch {
    uni.showToast({ title: '关注失败，请重试', icon: 'none' })
  }
}
```

### 4.2 followedCourses.js 服务

与 `followedRooms.js` 平行，但数据结构更简单（课程无 address/city 等字段）：

```javascript
export const FOLLOWED_COURSES_STORAGE_KEY = 'followed_courses'

import {
  fetchPersistedFollowedRooms,
  persistFollowRoom,
  persistUnfollowRoom,
} from '@/api/roomFollows'

export function normalizeCourse(course = {}) {
  const id = course.id ?? course.course_id
  if (id === undefined || id === null || id === '') return null
  return {
    id: Number(id),
    name: course.name || '未命名课程',
    cover_image: course.cover_image || course.coverImage || '',
    price: course.price ?? '',
    followed_at: course.followed_at || Date.now(),
  }
}

export function isCourseFollowed(courseId) { /* ... */ }
export function getFollowedCourses() { /* ... */ }
export async function followCourse(course) { /* 乐观更新 + API 调用 + 回滚 */ }
export async function unfollowCourse(courseId) { /* 乐观更新 + API 调用 + 回滚 */ }
export async function syncFollowedCourses() { /* 从后端同步 */ }
```

### 4.3 课程列表导航

**`training/index.vue`** 修改：
- 热门课程项 `<view @tap="onCourseDetail(course)">` 添加点击事件
- 分类标签下的课程卡片同理

```javascript
function onCourseDetail(course) {
  if (!course || !course.id) return
  uni.navigateTo({ url: '/pages/training/course-detail?course_id=' + course.id })
}
```

### 4.4 路由注册

**`pages.json`** 新增：

```json
{
  "path": "pages/training/course-detail",
  "style": {
    "navigationStyle": "custom",
    "navigationBarTitleText": "课程详情"
  }
}
```

### 4.5 BUG 规避清单

参考 `bug-fixed.md`：

| BUG | 规避措施 |
|-----|---------|
| BUG-1 | 不使用 `@import '@/uni.scss'`，使用 `$primary` 等全局变量 |
| BUG-14 | Options API 使用 `onLoad` 生命周期，不涉及 `onMounted` 导入问题 |
| BUG-15 | 本页面无 datetime 展示需求 |
| BUG-20 | 不使用 HTML 实体，用 Unicode 字符（如 `♥`、`★`） |
| BUG-22 | 路由定义不带尾部斜杠 |

## 5. 种子数据策略

为现有活跃课程生成示例课时数据，脚本位于 `br-server/scripts/seed_course_lessons.py`：

- 每门活跃课程生成 4-12 个课时
- 课时标题使用有意义的示例数据（如「第一章：课程导论」「第二章：核心概念」）
- `sort_order` 从 0 递增
- `duration_minutes` 随机 30-90 分钟
- 第一个课时 `is_free_preview=True`

## 6. 测试计划

### 6.1 后端测试

**课程详情 API**（`tests/test_course_detail.py`）：

| 场景 | 预期 |
|------|------|
| 正常课程（含 teacher、room、lessons） | 200，所有字段正确填充 |
| 课程不存在 | 404 |
| 课程 status != 'active' | 404 |
| 课程无课时 | 200，lessons 为空数组 `[]` |
| 相关课程超过 6 门 | 只返回 6 门，排除当前课程 |
| 课程无 teacher | 200，teacher 为 null |

**课程关注 API**（`tests/test_course_follow.py`）：

| 场景 | 预期 |
|------|------|
| 关注课程（follow_type=course） | 201，follow_type='course' |
| 重复关注同一课程 | 200，幂等 |
| 取消关注课程 | 204 |
| 列表过滤 follow_type=course | 只返回课程关注 |
| 同一 target 不同 follow_type | 两条记录并存 |
| 不传 follow_type | 默认 room，行为不变 |

**回归测试**（`tests/test_room_follow.py`）：
- 现有全部测试通过，无需修改

### 6.2 前端验证

- `br-app` 构建无错误（`npm run build`）
- 页面路由正确注册
- API 调用路径正确

## 7. 实施顺序

按 tasks.md 的 9 组任务顺序执行：

1. **工作区隔离** → 创建分支和 worktree
2. **数据库迁移** → alembic 迁移文件
3. **CourseLesson 模型** → 后端模型 + Schema + 种子数据
4. **课程详情 API** → 服务方法 + 路由 + 前端 API 封装
5. **课程关注功能** → 服务扩展 + 路由扩展 + 前端 API 扩展
6. **后端测试** → pytest 全部通过
7. **前端课程详情页** → course-detail.vue 完整实现
8. **前端关注服务与导航** → followedCourses.js + 路由注册 + 卡片跳转
9. **构建验证** → 后端 pytest + 前端 build
