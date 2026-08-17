---
change: course-detail-page
design-doc: docs/superpowers/specs/2026-08-17-course-detail-page-design.md
base-ref: 8e4fbeb7ce8080b5171f8063f9f835495f26f362
---

# 课程详情页 — 实施计划

## 概述

本计划实现课程详情页的完整功能，包含后端数据库迁移、模型/Schema/API 开发，前端页面/服务/导航集成。按 9 组任务顺序执行。

**环境约束**：
- Python 3.12.11 (conda: `conda activate booking-room`)
- Node v22.22.0 (nvm: `nvm use v22.22.0`)
- 后端：FastAPI + SQLAlchemy + PostgreSQL 18 + alembic
- 前端：uni-app (Vue3) Options API 风格

**BUG 规避清单**（参考 `bug-fixed.md`）：
| BUG | 规避措施 |
|-----|---------|
| BUG-1 | 不使用 `@import '@/uni.scss'`，直接使用 `$primary` 等全局变量（uni-app 自动注入） |
| BUG-14 | Options API 使用 `onLoad` 生命周期，不涉及 `onMounted` 导入问题 |
| BUG-15 | 本页面无 datetime 展示需求，无需处理 aware/naive datetime |
| BUG-20 | 不使用 HTML 实体，用 Unicode 字符（如 `♥`、`★`、`‹`、`›`） |
| BUG-22 | 路由定义不带尾部斜杠 |

---

## 任务 1：工作区隔离

### 1.1 创建 git 分支和 worktree

**操作**：
```bash
cd /Users/linhuanbin/BrianDocs/Workspace/work/yc-work/booking-room
git checkout -b course-detail-page 8e4fbeb7ce8080b5171f8063f9f835495f26f362
```

**验证**：
- `git branch --show-current` 输出 `course-detail-page`
- 后续所有变更均在此分支上进行

---

## 任务 2：数据库迁移

### 2.1-2.6 生成 alembic 迁移文件

**文件**：`br-server/alembic/versions/2026_08_17_1000-b3c4d5e6f7a8_add_course_lessons_and_follow_type.py`

**迁移内容**（单个迁移文件，`upgrade()` 按顺序执行）：

```python
"""add_course_lessons_and_follow_type

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-17 10:00:00.000000
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # 1. courses 表新增 description 列
    op.add_column("courses", sa.Column("description", sa.String(1000), nullable=True))

    # 2. 新建 course_lessons 表
    op.create_table(
        "course_lessons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_free_preview", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_course_lessons_course_id", "course_lessons", ["course_id"])

    # 3. room_follows 表新增 follow_type 列
    op.add_column(
        "room_follows",
        sa.Column("follow_type", sa.String(20), nullable=False, server_default="room"),
    )

    # 4. 删除旧唯一约束，创建新唯一约束
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "sqlite":
        # SQLite 不支持 DROP CONSTRAINT，使用 batch_alter_table
        with op.batch_alter_table("room_follows", recreate="always") as batch_op:
            batch_op.drop_constraint("uq_room_follows_user_room", type_="unique")
            batch_op.create_unique_constraint(
                "uq_room_follows_user_room_type",
                ["user_id", "room_id", "follow_type"],
            )
            # 5. 删除 room_id 外键约束
            batch_op.drop_constraint("room_follows_room_id_fkey", type_="foreignkey")
    else:
        op.drop_constraint("uq_room_follows_user_room", "room_follows", type_="unique")
        op.create_unique_constraint(
            "uq_room_follows_user_room_type",
            "room_follows",
            ["user_id", "room_id", "follow_type"],
        )
        # 5. 删除 room_follows.room_id 外键约束
        op.drop_constraint("room_follows_room_id_fkey", "room_follows", type_="foreignkey")

def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "sqlite":
        with op.batch_alter_table("room_follows", recreate="always") as batch_op:
            batch_op.create_foreign_key(
                "room_follows_room_id_fkey", "room_follows", "study_rooms", ["room_id"], ["id"], ondelete="CASCADE"
            )
            batch_op.drop_constraint("uq_room_follows_user_room_type", type_="unique")
            batch_op.create_unique_constraint("uq_room_follows_user_room", ["user_id", "room_id"])
            batch_op.drop_column("follow_type")
    else:
        op.create_foreign_key(
            "room_follows_room_id_fkey", "room_follows", "study_rooms",
            ["room_id"], ["id"], ondelete="CASCADE",
        )
        op.drop_constraint("uq_room_follows_user_room_type", "room_follows", type_="unique")
        op.create_unique_constraint("uq_room_follows_user_room", "room_follows", ["user_id", "room_id"])
        op.drop_column("room_follows", "follow_type")
    op.drop_index("ix_course_lessons_course_id", table_name="course_lessons")
    op.drop_table("course_lessons")
    op.drop_column("courses", "description")
```

**验证**：
```bash
cd br-server && conda activate booking-room
alembic upgrade head
alembic downgrade -1 && alembic upgrade head  # 验证双向迁移
```

---

## 任务 3：后端 — CourseLesson 模型与课时数据

### 3.1 新建 CourseLesson 模型

**文件**：`br-server/app/models/course_lesson.py`（新建）

**代码变更**：
```python
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, Index, func
from sqlalchemy.orm import Mapped, mapped_column
from app.core.database import Base

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

**同步修改**：`br-server/app/models/__init__.py`
- 添加 `from app.models.course_lesson import CourseLesson`
- 在 `__all__` 中添加 `"CourseLesson"`

### 3.2 新增 LessonResponse Schema

**文件**：`br-server/app/schemas/course.py`（修改）

**在文件末尾添加**：
```python
class LessonResponse(BaseModel):
    """课时响应 Schema"""
    id: int
    title: str
    description: str | None = None
    duration_minutes: int | None = None
    sort_order: int
    is_free_preview: bool = False
    model_config = ConfigDict(from_attributes=True)
```

### 3.3 课时种子数据脚本

**文件**：`br-server/scripts/seed_course_lessons.py`（新建）

**逻辑**：
- 连接数据库，查询所有 `status='active'` 的课程
- 为每门课程生成 4-12 个课时（随机数量）
- 课时标题使用有意义的示例（如「第1讲：课程导论」「第2讲：核心概念」等）
- `sort_order` 从 0 递增
- `duration_minutes` 随机 30-90
- 第一个课时 `is_free_preview=True`
- 使用 `asyncio.run()` 执行

**验证**：
```bash
cd br-server && python scripts/seed_course_lessons.py
# 检查数据库中 course_lessons 表有数据
```

---

## 任务 4：后端 — 课程详情 API

### 4.1 Course 模型添加 description 字段

**文件**：`br-server/app/models/course.py`（修改）

**在 `is_hot` 字段之前添加**：
```python
description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
```

### 4.2 RoomFollow 模型添加 follow_type 字段

**文件**：`br-server/app/models/room_follow.py`（修改）

**完整替换模型**：
- 删除 `room_id` 上的 `ForeignKey("study_rooms.id", ondelete="CASCADE")`，改为普通 `Integer, nullable=False, index=True`
- 删除旧 `UniqueConstraint("user_id", "room_id", name="uq_room_follows_user_room")`
- 添加新 `UniqueConstraint("user_id", "room_id", "follow_type", name="uq_room_follows_user_room_type")`
- 添加 `follow_type: Mapped[str] = mapped_column(String(20), default="room", nullable=False)`

### 4.3 新增 CourseDetailResponse Schema

**文件**：`br-server/app/schemas/course.py`（修改）

**在文件末尾添加以下 Schema**：
```python
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
    """课程详情响应"""
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

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None or v == "":
            return []
        return [tag.strip() for tag in v.split(",") if tag.strip()]
```

### 4.4 training_service.py 新增 get_course_detail()

**文件**：`br-server/app/services/training_service.py`（修改）

**添加导入**：
```python
from app.models.course_lesson import CourseLesson
from app.schemas.course import (
    CourseDetailResponse,
    LessonResponse,
    RelatedCourseItem,
    RoomBrief,
    # ... 保留现有导入
)
```

**新增方法**：
```python
async def get_course_detail(
    db: AsyncSession, course_id: int
) -> CourseDetailResponse | None:
    """返回课程详情，含教师、教室、课时和相关课程。

    3 步查询，避免 N+1：
    Step 1: courses + LEFT JOIN teachers + JOIN study_rooms
    Step 2: course_lessons WHERE course_id ORDER BY sort_order
    Step 3: 同分类其他活跃课程 LIMIT 6
    """
    # Step 1: 课程基本信息 + 教师 + 教室
    result = await db.execute(
        select(Course, Teacher, StudyRoom)
        .outerjoin(Teacher, Course.teacher_id == Teacher.id)
        .outerjoin(StudyRoom, Course.room_id == StudyRoom.id)
        .where(Course.id == course_id, Course.status == "active")
    )
    row = result.one_or_none()
    if row is None:
        return None
    course, teacher, study_room = row

    # Step 2: 课时列表
    lessons_result = await db.execute(
        select(CourseLesson)
        .where(CourseLesson.course_id == course_id)
        .order_by(CourseLesson.sort_order.asc())
    )
    lessons = [LessonResponse.model_validate(l) for l in lessons_result.scalars().all()]

    # Step 3: 相关课程（同分类，排除当前课程，最多 6 门）
    related_result = await db.execute(
        select(Course)
        .where(
            Course.category == course.category,
            Course.id != course_id,
            Course.status == "active",
        )
        .order_by(Course.sort_order.asc())
        .limit(6)
    )
    related_courses = [
        RelatedCourseItem(id=c.id, name=c.name, cover_image=c.cover_image, price=c.price)
        for c in related_result.scalars().all()
    ]

    # 组装响应
    teacher_brief = None
    if teacher:
        teacher_brief = TeacherBrief(
            id=teacher.id, name=teacher.name,
            avatar=teacher.avatar, title=teacher.title, rating=teacher.rating,
        )

    room_brief = None
    if study_room:
        room_brief = RoomBrief(
            id=study_room.id, name=study_room.name,
            address=study_room.address, cover_image=study_room.cover_image,
        )

    return CourseDetailResponse(
        id=course.id,
        name=course.name,
        cover_image=course.cover_image,
        category=course.category,
        price=course.price,
        rating=course.rating,
        enrollment_count=course.enrollment_count,
        schedule=course.schedule,
        tags=course.tags or [],
        status=course.status,
        is_hot=course.is_hot,
        description=course.description,
        teacher=teacher_brief,
        room=room_brief,
        lessons=lessons,
        related_courses=related_courses,
    )
```

### 4.5 training.py 路由新增课程详情端点

**文件**：`br-server/app/api/routes/training.py`（修改）

**添加导入**：
```python
from app.schemas.course import CourseDetailResponse  # 添加到现有导入
```

**新增路由**（放在 `get_training_room_detail` 之后）：
```python
@router.get("/courses/{course_id}", response_model=CourseDetailResponse)
async def get_course_detail(
    course_id: int,
    db: AsyncSession = Depends(get_db),
) -> CourseDetailResponse:
    result = await training_service.get_course_detail(db, course_id)
    if not result:
        raise HTTPException(status_code=404, detail="课程不存在或未上架")
    return result
```

**⚠️ 注意**：此路由必须放在 `/courses` 列表路由之后、`/rooms/{room_id}` 之前，避免路径冲突。由于 FastAPI 按注册顺序匹配，`/courses/{course_id}` 在 `/courses` 之后注册是正确的。

### 4.6 前端 API 封装

**文件**：`br-app/src/api/training.js`（修改）

**在文件末尾添加**：
```javascript
/**
 * 获取课程详情
 * @param {number} courseId - 课程ID
 */
export function getCourseDetail(courseId) {
  return get(`/api/v1/training/courses/${courseId}`)
}
```

**验证**：
```bash
cd br-server && pytest tests/ -x -q  # 确保现有测试不受影响
# 手动测试：curl http://localhost:8000/api/v1/training/courses/1
```

---

## 任务 5：后端 — 课程关注功能

### 5.1 room_follow_service.py 扩展

**文件**：`br-server/app/services/room_follow_service.py`（修改）

**添加导入**：
```python
from app.models.course import Course
```

**修改 `list_followed_rooms()`**：
- 添加 `follow_type: str = "room"` 参数
- 添加 `.where(RoomFollow.follow_type == follow_type)` 过滤条件
- `follow_type="room"` 时 JOIN `study_rooms`（现有逻辑）
- `follow_type="course"` 时 JOIN `courses`（当前阶段只需参数透传，返回空列表即可）

**修改 `follow_room()`**：
- 添加 `follow_type: str = "room"` 参数
- 查询已有关注时添加 `.where(RoomFollow.follow_type == follow_type)`
- 创建新关注时设置 `follow_type=follow_type`
- `follow_type="course"` 时校验 `courses` 表存在性（而非 `study_rooms`）

**修改 `unfollow_room()`**：
- 添加 `follow_type: str = "room"` 参数
- 删除时添加 `.where(RoomFollow.follow_type == follow_type)`

### 5.2 room_follow.py 路由扩展

**文件**：`br-server/app/api/routes/room_follow.py`（修改）

**添加导入**：
```python
from fastapi import Query
```

**修改三个路由方法**，添加 `follow_type` 查询参数：

```python
@router.get("", response_model=FollowedRoomListResponse)
async def list_followed_rooms(
    follow_type: str = Query("room", pattern="^(room|course)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FollowedRoomListResponse:
    return await room_follow_service.list_followed_rooms(db, user_id, follow_type=follow_type)

@router.post("/{room_id}", response_model=FollowedRoomResponse)
async def follow_room(
    room_id: int,
    response: Response,
    follow_type: str = Query("room", pattern="^(room|course)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> FollowedRoomResponse:
    try:
        room, created = await room_follow_service.follow_room(
            db, user_id, room_id, follow_type=follow_type
        )
    except ValueError:
        raise HTTPException(status_code=404, detail="Target not found")
    response.status_code = status.HTTP_201_CREATED if created else status.HTTP_200_OK
    return room

@router.delete("/{room_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unfollow_room(
    room_id: int,
    follow_type: str = Query("room", pattern="^(room|course)$"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> None:
    await room_follow_service.unfollow_room(db, user_id, room_id, follow_type=follow_type)
```

**⚠️ BUG-22 规避**：路由路径不带尾部斜杠（已确认现有路由无尾部斜杠）。

### 5.3 前端 API 层扩展

**文件**：`br-app/src/api/roomFollows.js`（修改）

**替换为**：
```javascript
import { del, get, post } from '@/utils/request'

export function getFollowedRooms(followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  return get(`/api/v1/room-follows${params}`)
}

export function followRoom(roomId, followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  return post(`/api/v1/room-follows/${roomId}${params}`)
}

export function unfollowRoom(roomId, followType = 'room') {
  const params = followType !== 'room' ? `?follow_type=${followType}` : ''
  return del(`/api/v1/room-follows/${roomId}${params}`)
}

export const persistFollowRoom = followRoom
export const fetchPersistedFollowedRooms = getFollowedRooms
export const persistUnfollowRoom = unfollowRoom
```

**向后兼容**：所有方法默认 `followType='room'`，现有调用无需修改。

**验证**：
```bash
# 关注课程
curl -X POST "http://localhost:8000/api/v1/room-follows/1?follow_type=course" -H "Authorization: Bearer <token>"
# 列表过滤
curl "http://localhost:8000/api/v1/room-follows?follow_type=course" -H "Authorization: Bearer <token>"
# 取消关注
curl -X DELETE "http://localhost:8000/api/v1/room-follows/1?follow_type=course" -H "Authorization: Bearer <token>"
# 验证默认行为不变（follow_type=room）
curl "http://localhost:8000/api/v1/room-follows" -H "Authorization: Bearer <token>"
```

---

## 任务 6：后端 — 测试

### 6.1 课程详情 API 测试

**文件**：`br-server/tests/test_course_detail.py`（新建）

**测试用例**：
| 场景 | 预期 |
|------|------|
| 正常课程（含 teacher、room、lessons） | 200，所有字段正确填充 |
| 课程不存在 | 404 |
| 课程 status != 'active' | 404 |
| 课程无课时 | 200，lessons 为空数组 `[]` |
| 相关课程超过 6 门 | 只返回 6 门，排除当前课程 |
| 课程无 teacher | 200，teacher 为 null |

**测试模式**：参考现有 `tests/test_api_booking.py` 的 fixture 模式，使用 `async_client` + `db_session` fixture。

### 6.2 课程关注 API 测试

**文件**：`br-server/tests/test_course_follow.py`（新建）

**测试用例**：
| 场景 | 预期 |
|------|------|
| 关注课程（follow_type=course） | 201，follow_type='course' |
| 重复关注同一课程 | 200，幂等 |
| 取消关注课程 | 204 |
| 列表过滤 follow_type=course | 只返回课程关注 |
| 同一 target 不同 follow_type | 两条记录并存 |
| 不传 follow_type | 默认 room，行为不变 |
| 非法 follow_type 值 | 422 |

### 6.3 现有 room_follow 测试回归

**文件**：`br-server/tests/test_room_follow.py`（已存在）

**操作**：运行现有测试确保全部通过，无需修改。

**验证**：
```bash
cd br-server && conda activate booking-room
pytest tests/test_course_detail.py tests/test_course_follow.py tests/test_room_follow.py -v
```

---

## 任务 7：前端 — 课程详情页

### 7.1 创建 course-detail.vue 页面

**文件**：`br-app/src/pages/training/course-detail.vue`（新建）

**代码风格**：Options API（与 `booking/detail.vue` 一致）

**⚠️ BUG 规避**：
- 不使用 `@import '@/uni.scss'`（BUG-1）
- 使用 `onLoad` 而非 `onMounted`（BUG-14）
- 不使用 HTML 实体，用 Unicode 字符（BUG-20）：`♥` 代替 `&hearts;`，`★` 代替 `&star;`
- 路由不带尾部斜杠（BUG-22）

**页面结构**（参考 `prototype/course-detail.html` 原型）：

```
template 结构：
├── 自定义导航栏（nav-overlay）
│   ├── statusBarHeight 占位
│   ├── 返回按钮（nav-btn + nav-chevron）
│   └── 分享按钮（nav-btn + nav-share）
├── scroll-view 内容区
│   ├── Hero 区域（封面图 + 渐变遮罩）
│   ├── 课程信息卡（info-card）
│   │   ├── 标签行（热销/分类标签）
│   │   ├── 课程名称
│   │   ├── 评分 + 已学人数 + 课时数
│   │   └── 价格区域
│   ├── 教师信息卡（teacher-card）
│   │   ├── 头像 + 认证标识
│   │   ├── 姓名 + 认证讲师标签
│   │   └── 评分 + 学员数
│   ├── 课程介绍区域（intro-section）
│   │   ├── 介绍文本
│   │   └── 特色亮点网格（2x2）
│   ├── 课程目录区域（lessons-section）
│   │   ├── 课时列表（displayLessons 计算属性控制显示数量）
│   │   └── 展开/收起按钮
│   ├── 学员评价区域（reviews-section）
│   │   ├── 评分汇总
│   │   └── 静态评价列表
│   ├── 相关课程横向滚动（related-scroll）
│   └── 底部留白 140rpx
└── 底部操作栏（bottom-bar）
    ├── 心形关注按钮（♥）
    ├── 价格展示
    └── 立即预约按钮
```

**script 结构**：
```javascript
import { getCourseDetail } from '@/api/training'
import { followCourse, isCourseFollowed, unfollowCourse } from '@/services/followedCourses'

export default {
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
      reviews: [
        { name: '张同学', rating: 5, content: '课程内容很充实，老师讲解很到位。', date: '2025-12-01' },
        { name: '李同学', rating: 4, content: '整体不错，希望能增加更多实操环节。', date: '2025-11-20' },
      ],
    }
  },
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
      if (this.course.is_hot) {
        return ['热销', ...tags]
      }
      return tags
    },
  },
  onLoad(options) {
    const sysInfo = uni.getSystemInfoSync()
    this.statusBarHeight = sysInfo.statusBarHeight || 0
    if (options.course_id) {
      this.courseId = Number(options.course_id)
      this.isFav = isCourseFollowed(this.courseId)
      this.loadCourseDetail()
    }
  },
  methods: {
    async loadCourseDetail() { /* 调用 getCourseDetail 并赋值 */ },
    onBack() { uni.navigateBack() },
    onShare() { /* placeholder */ },
    async onToggleFav() { /* 关注/取消逻辑 */ },
    onBook() { uni.showToast({ title: '预约功能开发中', icon: 'none' }) },
    toggleLessons() { this.lessonsExpanded = !this.lessonsExpanded },
    onRelatedCourse(course) {
      uni.redirectTo({ url: '/pages/training/course-detail?course_id=' + course.id })
    },
  },
}
```

**style 部分**：
- 使用 `<style lang="scss" scoped>`
- 复用项目全局 SCSS 变量：`$primary`、`$text-primary`、`$text-secondary`、`$text-muted`、`$white`、`$surface`、`$surface-soft`、`$border-soft`、`$shadow-card`、`$shadow-float`、`$gradient-primary`、`$bg-color`、`$danger`、`$success`、`$primary-soft`
- 颜色参考原型：primary `#4F6EF7`、文字 `#2D3436`/`#636E72`/`#B2BEC3`
- 卡片使用 `rounded-2xl` + `shadow-sm` 风格（`border-radius: 32rpx`）
- 动画使用 `fadeInUp` 入场动画（与 `detail.vue` 一致）

### 7.2-7.8 各区域实现细节

各区域在 7.1 的页面框架内一次性实现，关键要点：

**7.2 课程信息卡**：
- 标签使用 `.tag` 组件，热销标签红色背景 `rgba(255,71,87,0.1)`
- 价格区域显示 `¥{price}/课时`
- 评分使用 `★` Unicode 字符

**7.3 教师信息卡**：
- 头像圆形 `rounded-full`（`border-radius: 50%`）
- 认证标识使用绿色圆点 + 对勾
- 整个卡片可点击（占位，暂显示 Toast）

**7.4 课程介绍**：
- 介绍文本从 `course.description` 获取
- 特色亮点网格 2x2（硬编码 4 个示例项）

**7.5 课程目录**：
- 从 API `lessons` 数据渲染
- 默认展示前 4 节，`lessonsExpanded` 控制展开
- 每节显示播放图标 + 标题 + 时长 + 状态
- 无课时显示「暂无课程目录」

**7.6 学员评价**：
- 使用 `data()` 中的静态 `reviews` 数组
- 评分使用 `★` Unicode 字符

**7.7 相关课程**：
- 横向 `scroll-view scroll-x`
- 卡片包含封面图 + 名称 + 价格
- 点击跳转到对应课程详情（`redirectTo`）

**7.8 底部操作栏**：
- 固定定位 `position: fixed; bottom: 0`
- 心形按钮：默认空心（`-webkit-text-stroke`），关注后实心红色
- 价格展示：`¥{price}起`
- 立即预约按钮：渐变蓝色背景

**验证**：
- 页面在 HBuilderX 模拟器中正常渲染
- 所有区域布局正确
- 关注按钮交互正常

---

## 任务 8：前端 — 关注服务与导航

### 8.1 新建 followedCourses.js 服务

**文件**：`br-app/src/services/followedCourses.js`（新建）

**参考**：`br-app/src/services/followedRooms.js` 的模式，但数据结构更简单

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

export function getFollowedCourses() {
  const stored = uni.getStorageSync(FOLLOWED_COURSES_STORAGE_KEY)
  const courses = Array.isArray(stored) ? stored : []
  return courses.map(normalizeCourse).filter(Boolean)
}

function setFollowedCourses(courses) {
  const next = (Array.isArray(courses) ? courses : []).map(normalizeCourse).filter(Boolean)
  uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, next)
  return next
}

export function isCourseFollowed(courseId) {
  const normalizedId = Number(courseId)
  return getFollowedCourses().some((c) => c.id === normalizedId)
}

export async function followCourse(course) {
  const normalized = normalizeCourse(course)
  if (!normalized) return getFollowedCourses()

  const previous = getFollowedCourses()
  const next = [normalized, ...previous.filter((c) => c.id !== normalized.id)]
  uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, next)

  try {
    await persistFollowRoom(normalized.id, 'course')
    return next
  } catch (error) {
    uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, previous)
    throw error
  }
}

export async function unfollowCourse(courseId) {
  const normalizedId = Number(courseId)
  const previous = getFollowedCourses()
  const next = previous.filter((c) => c.id !== normalizedId)
  uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, next)

  try {
    await persistUnfollowRoom(normalizedId, 'course')
  } catch (error) {
    uni.setStorageSync(FOLLOWED_COURSES_STORAGE_KEY, previous)
    throw error
  }
  return next
}

export async function syncFollowedCourses() {
  const data = await fetchPersistedFollowedRooms('course')
  // 后端返回的是 FollowedRoomResponse 格式，需要映射
  const courses = (data?.items || []).map((item) => ({
    id: item.id,
    name: item.name,
    cover_image: item.cover_image,
    price: item.min_price,
    followed_at: item.followed_at,
  }))
  return setFollowedCourses(courses)
}
```

### 8.2 pages.json 注册路由

**文件**：`br-app/src/pages.json`（修改）

**在 `pages` 数组中添加**（放在 `pages/training/index` 之后）：
```json
{
  "path": "pages/training/course-detail",
  "style": {
    "navigationStyle": "custom",
    "navigationBarTitleText": "课程详情"
  }
}
```

**⚠️ BUG-22 规避**：路由定义不带尾部斜杠。

### 8.3 training/index.vue 课程卡片跳转

**文件**：`br-app/src/pages/training/index.vue`（修改）

**修改 1**：在 `<script setup>` 中添加导航函数：
```javascript
function onCourseDetail(course) {
  if (!course || !course.id) return
  uni.navigateTo({ url: '/pages/training/course-detail?course_id=' + course.id })
}
```

**修改 2**：在模板中为热门课程项添加点击事件。

找到 `hot-course-item` 的 `<view>` 标签（约第 148-152 行）：
```html
<!-- 修改前 -->
<view
  v-for="course in room.hot_courses"
  :key="course.id"
  class="hot-course-item"
>
```
改为：
```html
<!-- 修改后 -->
<view
  v-for="course in room.hot_courses"
  :key="course.id"
  class="hot-course-item"
  @tap="onCourseDetail(course)"
>
```

**修改 3**：为分类标签下的课程卡片添加点击事件。

找到分类课程卡片（约第 204-208 行）：
```html
<!-- 修改前 -->
<view
  v-for="(course, index) in courses"
  :key="course.id"
  :class="['course-card', ...]"
>
```
改为：
```html
<!-- 修改后 -->
<view
  v-for="(course, index) in courses"
  :key="course.id"
  :class="['course-card', ...]"
  @tap="onCourseDetail(course)"
>
```

### 8.4 课程详情页关注按钮交互

已在任务 7.1 的 `course-detail.vue` 中实现 `onToggleFav()` 方法，包含：
- 关注/取消关注切换
- 乐观更新 + API 调用 + 失败回滚
- Toast 提示

**验证**：
- 从培训列表页点击课程卡片，成功跳转到课程详情页
- 课程详情页正确加载课程数据
- 关注按钮点击后状态切换，Toast 正常显示
- 返回列表页后关注状态保持

---

## 任务 9：构建验证

### 9.1 后端 pytest 全部通过

```bash
cd br-server && conda activate booking-room
pytest tests/ -v --tb=short
```

**预期**：所有测试通过，包括：
- 新增的 `test_course_detail.py`
- 新增的 `test_course_follow.py`
- 现有的 `test_room_follow.py`（回归验证）
- 其他所有现有测试不受影响

### 9.2 前端 br-app 构建无错误

```bash
cd br-app && nvm use v22.22.0 && npm run build
```

**预期**：构建成功，无编译错误。

**关键检查点**：
- `course-detail.vue` 正确编译
- `followedCourses.js` 正确导入
- `pages.json` 路由注册正确
- API 调用路径正确

---

## 文件变更汇总

| 文件 | 操作 | 任务 |
|------|------|------|
| `br-server/alembic/versions/2026_08_17_*.py` | 新建 | 2 |
| `br-server/app/models/course_lesson.py` | 新建 | 3.1 |
| `br-server/app/models/__init__.py` | 修改 | 3.1 |
| `br-server/app/models/course.py` | 修改 | 4.1 |
| `br-server/app/models/room_follow.py` | 修改 | 4.2 |
| `br-server/app/schemas/course.py` | 修改 | 3.2, 4.3 |
| `br-server/app/services/training_service.py` | 修改 | 4.4 |
| `br-server/app/api/routes/training.py` | 修改 | 4.5 |
| `br-server/app/services/room_follow_service.py` | 修改 | 5.1 |
| `br-server/app/api/routes/room_follow.py` | 修改 | 5.2 |
| `br-server/scripts/seed_course_lessons.py` | 新建 | 3.3 |
| `br-server/tests/test_course_detail.py` | 新建 | 6.1 |
| `br-server/tests/test_course_follow.py` | 新建 | 6.2 |
| `br-app/src/api/training.js` | 修改 | 4.6 |
| `br-app/src/api/roomFollows.js` | 修改 | 5.3 |
| `br-app/src/services/followedCourses.js` | 新建 | 8.1 |
| `br-app/src/pages/training/course-detail.vue` | 新建 | 7.x |
| `br-app/src/pages.json` | 修改 | 8.2 |
| `br-app/src/pages/training/index.vue` | 修改 | 8.3 |
