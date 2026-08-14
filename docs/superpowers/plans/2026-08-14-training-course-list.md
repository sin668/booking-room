---
change: training-course-list
design-doc: docs/superpowers/specs/2026-08-14-training-course-list-design.md
base-ref: d44876bfddcb2cece0156851fc79abbef62ddd3e
---

# 培训课程列表页 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 实现培训课程列表页功能，包含培训室列表（含热门课程展开）、课程分类列表、前端页面和底部导航。

**Architecture:** 后端采用 Clean Architecture 分层（routes → services → models/schemas），新增 Teacher 和 Course 数据模型，通过显式 JOIN 查询（不使用 ORM relationship，参考 BUG-16）实现培训室和课程的复合查询。前端基于 uni-app Vue 3 实现，参考高保真原型 `prototype/training.html`。

**Tech Stack:** Python 3.12 + FastAPI + SQLAlchemy 2.0 async + Pydantic v2 + Alembic；Vue 3 + uni-app + Vite

## Global Constraints

- Python 3.12.11 (conda): `conda activate booking-room`
- Node v22.22.0 (nvm): `nvm use v22.22.0`
- 不使用 ORM relationship，service 层通过显式 `select().join()` 完成（BUG-16 防范）
- 迁移和种子数据中 timestamps 使用 `func.now()`，不传 `datetime.now(UTC)`（BUG-15 防范）
- 新路由不得使用尾部斜杠（BUG-22 防范）
- Vue3 生命周期钩子从 `vue` 导入，uni-app 页面钩子从 `@dcloudio/uni-app` 导入（BUG-14 防范）
- 前端模板中不使用 `&lt;`/`&gt;`，使用 Unicode 字符（BUG-20 防范）
- 前端 API 中 page_size 不超过 50（BUG-13 防范）

---

## 文件结构

### 后端新建文件

| 文件 | 职责 |
|------|------|
| `br-server/app/models/teacher.py` | Teacher ORM 模型 |
| `br-server/app/models/course.py` | Course ORM 模型 |
| `br-server/app/schemas/teacher.py` | TeacherResponse Schema |
| `br-server/app/schemas/course.py` | Course/TrainingRoom 系列 Schema |
| `br-server/app/services/training_service.py` | 培训室和课程查询业务逻辑 |
| `br-server/app/api/routes/training.py` | 培训室和课程 API 路由 |
| `br-server/alembic/versions/2026_08_14_1000-add_room_type_teachers_courses.py` | 数据库迁移 |
| `br-server/tests/test_training_api.py` | 培训 API 集成测试 |

### 后端修改文件

| 文件 | 修改内容 |
|------|---------|
| `br-server/app/models/study_room.py` | 增加 `room_type` 字段 |
| `br-server/app/models/__init__.py` | 注册 Teacher、Course 导出 |
| `br-server/app/schemas/study_room.py` | StudyRoomResponse 增加 `room_type`，RoomCreate/RoomUpdate 增加 `room_type` 可选字段 |
| `br-server/app/services/study_room_service.py` | `list_study_rooms`/`admin_list_rooms` 增加 `room_type` 过滤 |
| `br-server/app/services/seed_data.py` | 增加培训室、教师、课程种子数据 |
| `br-server/app/api/routes/study_room.py` | `list_study_rooms` 增加 `room_type` 查询参数 |
| `br-server/app/main.py` | 注册 `training_router` |
| `br-server/tests/test_api_homepage.py` | 增加 `room_type` 过滤和响应字段测试 |

### 前端新建文件

| 文件 | 职责 |
|------|------|
| `br-app/src/api/training.js` | 培训室和课程 API 封装 |
| `br-app/src/pages/training/index.vue` | 培训课程列表页 |

### 前端修改文件

| 文件 | 修改内容 |
|------|---------|
| `br-app/src/pages.json` | 注册培训页面路由和 tabBar 入口 |

### 文档修改文件

| 文件 | 修改内容 |
|------|---------|
| `docs/api.md` | 补充培训室、课程接口和 room_type 参数文档 |

---

## Task 1: 数据库迁移与模型

**Files:**
- Create: `br-server/app/models/teacher.py`
- Create: `br-server/app/models/course.py`
- Modify: `br-server/app/models/study_room.py`
- Modify: `br-server/app/models/__init__.py`
- Create: `br-server/alembic/versions/2026_08_14_1000-add_room_type_teachers_courses.py`

**Interfaces:**
- Consumes: `app.core.database.Base`（现有 Base 声明）
- Produces: `Teacher` 模型（id, name, avatar, title, rating, created_at, updated_at）、`Course` 模型（id, room_id, teacher_id, name, cover_image, category, price, rating, enrollment_count, schedule, tags, status, is_hot, sort_order, created_at, updated_at）、`StudyRoom.room_type` 字段

- [x] **Step 1: 创建 Teacher 模型**

创建 `br-server/app/models/teacher.py`：

```python
from datetime import datetime

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Teacher(Base):
    __tablename__ = "teachers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)
    avatar: Mapped[str | None] = mapped_column(String(512), nullable=True)
    title: Mapped[str | None] = mapped_column(String(50), nullable=True)
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0.0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

- [x] **Step 2: 创建 Course 模型**

创建 `br-server/app/models/course.py`：

```python
from datetime import datetime

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(Integer, ForeignKey("study_rooms.id"), nullable=False)
    teacher_id: Mapped[int | None] = mapped_column(Integer, ForeignKey("teachers.id"), nullable=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0.0, nullable=False)
    enrollment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schedule: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), onupdate=func.now(), nullable=False)
```

- [x] **Step 3: 修改 StudyRoom 模型，增加 room_type 字段**

在 `br-server/app/models/study_room.py` 的 `status` 字段行之后、`min_price` 之前插入：

```python
    room_type: Mapped[str] = mapped_column(String(20), default="study", nullable=False)
```

- [x] **Step 4: 在 models/__init__.py 注册 Teacher 和 Course**

在 `br-server/app/models/__init__.py` 中：
- 在 `from app.models.study_room import StudyRoom` 之后增加两行导入
- 在 `__all__` 列表中按字母顺序增加 `"Course"` 和 `"Teacher"`

导入增加：

```python
from app.models.course import Course
from app.models.teacher import Teacher
```

`__all__` 中在 `"City"` 之后增加 `"Course"`，在 `"SystemSetting"` 之后增加 `"Teacher"`（按字母顺序）。

- [x] **Step 5: 创建 Alembic 迁移文件**

创建 `br-server/alembic/versions/2026_08_14_1000-add_room_type_teachers_courses.py`：

```python
"""add room_type, teachers, courses

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("study_rooms",
        sa.Column("room_type", sa.String(20), server_default="study", nullable=False))

    op.create_table("teachers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("avatar", sa.String(512), nullable=True),
        sa.Column("title", sa.String(50), nullable=True),
        sa.Column("rating", sa.Numeric(3, 1), server_default="0.0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table("courses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.Integer, sa.ForeignKey("study_rooms.id"), nullable=False),
        sa.Column("teacher_id", sa.Integer, sa.ForeignKey("teachers.id"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cover_image", sa.String(512), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("rating", sa.Numeric(3, 1), server_default="0.0", nullable=False),
        sa.Column("enrollment_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("schedule", sa.String(200), nullable=True),
        sa.Column("tags", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("is_hot", sa.Boolean, server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_courses_room_id", "courses", ["room_id"])
    op.create_index("ix_courses_teacher_id", "courses", ["teacher_id"])
    op.create_index("ix_courses_category", "courses", ["category"])


def downgrade() -> None:
    op.drop_index("ix_courses_category", table_name="courses")
    op.drop_index("ix_courses_teacher_id", table_name="courses")
    op.drop_index("ix_courses_room_id", table_name="courses")
    op.drop_table("courses")
    op.drop_table("teachers")
    op.drop_column("study_rooms", "room_type")
```

- [x] **Step 6: 执行迁移并验证**

Run: `cd br-server && conda activate booking-room && alembic upgrade head`
Expected: 输出 `Running upgrade a2b3c4d5e6f7 -> b3c4d5e6f7a8, add room_type, teachers, courses`

- [x] **Step 7: Commit**

```bash
git add br-server/app/models/teacher.py br-server/app/models/course.py \
  br-server/app/models/study_room.py br-server/app/models/__init__.py \
  br-server/alembic/versions/2026_08_14_1000-add_room_type_teachers_courses.py
git commit -m "feat: add Teacher/Course models and room_type migration"
```

---

## Task 2: 后端 Schema

**Files:**
- Create: `br-server/app/schemas/teacher.py`
- Create: `br-server/app/schemas/course.py`
- Modify: `br-server/app/schemas/study_room.py`

**Interfaces:**
- Consumes: Task 1 的 `Teacher`、`Course`、`StudyRoom.room_type`
- Produces: `TeacherResponse`、`TeacherBrief`、`HotCourseItem`、`TrainingRoomResponse`、`TrainingRoomListResponse`、`CourseResponse`、`CourseListResponse`

- [x] **Step 1: 创建 Teacher Schema**

创建 `br-server/app/schemas/teacher.py`：

```python
from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TeacherResponse(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal

    model_config = ConfigDict(from_attributes=True)
```

- [x] **Step 2: 创建 Course Schema**

创建 `br-server/app/schemas/course.py`：

```python
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class TeacherBrief(BaseModel):
    """教师简要信息，嵌套在课程响应中"""
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal

    model_config = ConfigDict(from_attributes=True)


class HotCourseItem(BaseModel):
    """热门课程简要信息，嵌套在培训室响应中"""
    id: int
    name: str
    cover_image: str | None = None
    teacher: TeacherBrief | None = None
    price: Decimal
    enrollment_count: int


class TrainingRoomResponse(BaseModel):
    """培训室列表响应中的单个培训室"""
    id: int
    name: str
    description: str | None = None
    cover_image: str | None = None
    address: str
    city_id: int | None = None
    city_name: str | None = None
    business_hours: str | None = None
    status: str
    room_type: str
    min_price: Decimal
    hot_courses: list[HotCourseItem] = []

    model_config = ConfigDict(from_attributes=True)


class TrainingRoomListResponse(BaseModel):
    items: list[TrainingRoomResponse]
    total: int
    page: int
    page_size: int


class CourseResponse(BaseModel):
    """课程列表响应中的单个课程"""
    id: int
    name: str
    cover_image: str | None = None
    teacher: TeacherBrief | None = None
    category: str
    price: Decimal
    rating: Decimal
    enrollment_count: int
    schedule: str | None = None
    tags: list[str] = []
    status: str
    room_id: int
    room_name: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """将逗号分隔字符串解析为列表，None 或空字符串返回空列表"""
        if v is None or v == "":
            return []
        return [tag.strip() for tag in v.split(",") if tag.strip()]


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
```

- [x] **Step 3: 修改 StudyRoom Schema，增加 room_type 字段**

在 `br-server/app/schemas/study_room.py` 中：

1. 在 `StudyRoomResponse` 的 `status` 字段之后增加：
```python
    room_type: str
```

2. 在 `RoomCreate` 的 `min_price` 之前增加：
```python
    room_type: str = Field("study", pattern="^(study|training|comprehensive)$")
```

3. 在 `RoomUpdate` 的 `min_price` 之前增加：
```python
    room_type: str | None = Field(None, pattern="^(study|training|comprehensive)$")
```

4. 在 `RoomAdminResponse` 的 `status` 字段之后增加：
```python
    room_type: str
```

- [x] **Step 4: Commit**

```bash
git add br-server/app/schemas/teacher.py br-server/app/schemas/course.py \
  br-server/app/schemas/study_room.py
git commit -m "feat: add Teacher/Course schemas and room_type in StudyRoom schemas"
```

---

## Task 3: 后端 Service

**Files:**
- Create: `br-server/app/services/training_service.py`
- Modify: `br-server/app/services/study_room_service.py`
- Modify: `br-server/app/services/seed_data.py`

**Interfaces:**
- Consumes: Task 1 的 `Teacher`、`Course`、`StudyRoom.room_type`；Task 2 的全部 Schema
- Produces: `training_service.list_training_rooms(db, page, page_size, city_id) -> TrainingRoomListResponse`、`training_service.list_courses(db, page, page_size, category) -> CourseListResponse`；`study_room_service.list_study_rooms` 和 `admin_list_rooms` 增加 `room_type` 参数

- [x] **Step 1: 创建 training_service.py**

创建 `br-server/app/services/training_service.py`：

```python
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.schemas.course import (
    CourseListResponse,
    CourseResponse,
    HotCourseItem,
    TrainingRoomListResponse,
    TrainingRoomResponse,
)
from app.schemas.teacher import TeacherResponse

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


async def list_training_rooms(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    city_id: int | None = None,
) -> TrainingRoomListResponse:
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    filters = [
        StudyRoom.status == "open",
        StudyRoom.room_type.in_(["training", "comprehensive"]),
    ]
    if city_id is not None:
        filters.append(StudyRoom.city_id == city_id)

    count_result = await db.execute(
        select(func.count()).select_from(StudyRoom).where(*filters))
    total = count_result.scalar_one()

    result = await db.execute(
        select(StudyRoom, City.name.label("city_name"))
        .outerjoin(City, StudyRoom.city_id == City.id)
        .where(*filters)
        .order_by(StudyRoom.id.asc())
        .offset(offset).limit(page_size))
    rooms = result.all()

    if not rooms:
        return TrainingRoomListResponse(items=[], total=total, page=page, page_size=page_size)

    room_ids = [room.id for room, _ in rooms]

    hot_result = await db.execute(
        select(Course, Teacher)
        .outerjoin(Teacher, Course.teacher_id == Teacher.id)
        .where(
            Course.room_id.in_(room_ids),
            Course.is_hot == True,
            Course.status == "active",
        )
        .order_by(Course.room_id.asc(), Course.sort_order.asc(), Course.id.asc()))
    hot_rows = hot_result.all()

    hot_by_room = {}
    for course, teacher in hot_rows:
        if course.room_id not in hot_by_room:
            hot_by_room[course.room_id] = []
        if len(hot_by_room[course.room_id]) < 3:
            hot_by_room[course.room_id].append(
                HotCourseItem(
                    id=course.id, name=course.name, cover_image=course.cover_image,
                    teacher=TeacherResponse.model_validate(teacher) if teacher else None,
                    price=course.price, enrollment_count=course.enrollment_count,
                ))

    items = []
    for room, city_name in rooms:
        item = TrainingRoomResponse.model_validate(room)
        item.city_name = city_name
        item.hot_courses = hot_by_room.get(room.id, [])
        items.append(item)

    return TrainingRoomListResponse(items=items, total=total, page=page, page_size=page_size)


async def list_courses(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    category: str | None = None,
) -> CourseListResponse:
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    filters = [Course.status == "active"]
    if category is not None:
        filters.append(Course.category == category)

    count_result = await db.execute(
        select(func.count()).select_from(Course).where(*filters))
    total = count_result.scalar_one()

    result = await db.execute(
        select(Course, StudyRoom.name.label("room_name"), Teacher)
        .join(StudyRoom, Course.room_id == StudyRoom.id)
        .outerjoin(Teacher, Course.teacher_id == Teacher.id)
        .where(*filters)
        .order_by(Course.sort_order.asc(), Course.id.asc())
        .offset(offset).limit(page_size))
    rows = result.all()

    items = []
    for course, room_name, teacher in rows:
        item = CourseResponse.model_validate(course)
        item.room_name = room_name
        item.teacher = TeacherResponse.model_validate(teacher) if teacher else None
        items.append(item)

    return CourseListResponse(items=items, total=total, page=page, page_size=page_size)
```

- [x] **Step 2: 修改 study_room_service.py，增加 room_type 过滤**

在 `br-server/app/services/study_room_service.py` 中：

1. `list_study_rooms` 函数签名增加参数：
```python
async def list_study_rooms(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    city_id: int | None = None,
    room_type: str | None = None,
) -> StudyRoomListResponse:
```

2. 在 `filters` 列表构建处增加 room_type 过滤（在 `if city_id` 之后）：
```python
    if room_type is not None:
        filters.append(StudyRoom.room_type == room_type)
```

3. `admin_list_rooms` 函数签名增加参数：
```python
async def admin_list_rooms(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    status: str | None = None,
    room_type: str | None = None,
) -> RoomAdminListResponse:
```

4. 在 `admin_list_rooms` 的 status 过滤之后增加：
```python
    if room_type is not None:
        query = query.where(StudyRoom.room_type == room_type)
        count_query = count_query.where(StudyRoom.room_type == room_type)
```

- [x] **Step 3: 修改 seed_data.py，增加培训相关种子数据**

在 `br-server/app/services/seed_data.py` 中：

1. 在文件顶部导入区增加：
```python
from app.models.course import Course
from app.models.teacher import Teacher
```

2. 在 `SEED_STUDY_ROOMS` 列表之后增加培训室和教师、课程数据：

```python
SEED_TRAINING_ROOMS = [
    StudyRoom(
        name="去K书培训中心",
        description="名师一对一辅导，考研公考全方位提升",
        cover_image="https://images.unsplash.com/photo-1580582932705-ff3c3993141f?w=400&h=300&fit=crop",
        address="茂名市茂南区光谷大道88号3楼",
        business_hours="08:00-22:00",
        status="open",
        min_price=50.00,
        room_type="training",
    ),
    StudyRoom(
        name="去K书·星火教室",
        description="大班投影教学，英语技能专项训练",
        cover_image="https://images.unsplash.com/photo-1497366754035-f200968a6e72?w=400&h=300&fit=crop",
        address="茂名市茂南区文明中路56号2楼",
        business_hours="08:00-21:00",
        status="open",
        min_price=40.00,
        room_type="training",
    ),
    StudyRoom(
        name="去K书·精英学堂",
        description="一对一隔音教室，雅思托福专项辅导",
        cover_image="https://images.unsplash.com/photo-1531542151005-2ec6f3e3a4e3?w=400&h=300&fit=crop",
        address="茂名市茂南区站前路120号5楼",
        business_hours="09:00-21:00",
        status="open",
        min_price=80.00,
        room_type="training",
    ),
    StudyRoom(
        name="去K书·综合学习中心",
        description="自习+培训一体化空间，满足多样化学习需求",
        cover_image="https://images.unsplash.com/photo-1522202176988-662241b9a3ee?w=400&h=300&fit=crop",
        address="茂名市茂南区光华南路200号",
        business_hours="07:00-23:00",
        status="open",
        min_price=10.00,
        room_type="comprehensive",
    ),
]

SEED_TEACHERS = [
    Teacher(name="李明华", avatar="https://images.unsplash.com/photo-1568602471122-3b6f0c1c3f9a?w=200&h=200&fit=crop&crop=face", title="考研政治名师", rating=4.9),
    Teacher(name="王晓雯", avatar="https://images.unsplash.com/photo-1494790108377-be9c29b29330?w=200&h=200&fit=crop&crop=face", title="公考行测专家", rating=4.8),
    Teacher(name="陈雅琪", avatar="https://images.unsplash.com/photo-1573496359662-720d0fc0e725?w=200&h=200&fit=crop&crop=face", title="雅思口语讲师", rating=5.0),
    Teacher(name="张伟强", avatar="https://images.unsplash.com/photo-1507006616952-0e0531ab0e1e?w=200&h=200&fit=crop&crop=face", title="英语四级讲师", rating=4.7),
    Teacher(name="刘芳芳", avatar="https://images.unsplash.com/photo-1438761681033-6461ffade8d5?w=200&h=200&fit=crop&crop=face", title="教师资格证面试官", rating=4.8),
]
```

3. 在 `seed_all()` 函数中（在 `await seed_coupons(session)` 之前）增加教师、培训室和课程种子逻辑：

```python
        # Seed teachers
        teacher_map = {}
        for teacher in SEED_TEACHERS:
            existing = await session.execute(
                select(Teacher).where(Teacher.name == teacher.name)
            )
            obj = existing.scalar_one_or_none()
            if obj is None:
                session.add(teacher)
                await session.flush()
                obj = teacher
                print(f"  + Teacher: {obj.name}")
            teacher_map[obj.name] = obj

        # Seed training rooms
        training_room_map = {}
        for room in SEED_TRAINING_ROOMS:
            existing = await session.execute(
                select(StudyRoom).where(StudyRoom.name == room.name)
            )
            obj = existing.scalar_one_or_none()
            if obj is None:
                session.add(room)
                await session.flush()
                obj = room
                print(f"  + TrainingRoom: {obj.name}")
            training_room_map[obj.name] = obj

        # Seed courses
        seed_courses_data = [
            {"room_name": "去K书培训中心", "teacher_name": "李明华", "name": "考研政治冲刺班", "category": "postgraduate", "price": 80.00, "rating": 4.9, "enrollment_count": 328, "schedule": "周六 9:00-12:00", "tags": "考研,政治,冲刺", "is_hot": True, "sort_order": 1},
            {"room_name": "去K书培训中心", "teacher_name": "王晓雯", "name": "公务员行测精讲", "category": "civil_service", "price": 60.00, "rating": 4.8, "enrollment_count": 156, "schedule": "周日 14:00-17:00", "tags": "公考,行测", "is_hot": True, "sort_order": 2},
            {"room_name": "去K书培训中心", "teacher_name": "陈雅琪", "name": "雅思口语1v1冲刺", "category": "language", "price": 120.00, "rating": 5.0, "enrollment_count": 89, "schedule": "预约制", "tags": "雅思,口语,一对一", "is_hot": True, "sort_order": 3},
            {"room_name": "去K书·星火教室", "teacher_name": "张伟强", "name": "英语四级冲刺密训", "category": "language", "price": 50.00, "rating": 4.7, "enrollment_count": 512, "schedule": "周六 9:00-11:30", "tags": "英语,四级,冲刺", "is_hot": True, "sort_order": 1},
            {"room_name": "去K书·星火教室", "teacher_name": "刘芳芳", "name": "教师资格证面试辅导", "category": "professional", "price": 90.00, "rating": 4.8, "enrollment_count": 203, "schedule": "周日 9:00-12:00", "tags": "教师资格,面试", "is_hot": True, "sort_order": 2},
            {"room_name": "去K书·精英学堂", "teacher_name": "陈雅琪", "name": "雅思口语1v1冲刺", "category": "language", "price": 120.00, "rating": 5.0, "enrollment_count": 89, "schedule": "预约制", "tags": "雅思,口语", "is_hot": True, "sort_order": 1},
            {"room_name": "去K书·精英学堂", "teacher_name": "李明华", "name": "考研政治冲刺班", "category": "postgraduate", "price": 80.00, "rating": 4.9, "enrollment_count": 328, "schedule": "周六 14:00-17:00", "tags": "考研,政治", "is_hot": True, "sort_order": 2},
            {"room_name": "去K书·精英学堂", "teacher_name": "刘芳芳", "name": "教师资格证面试辅导", "category": "professional", "price": 90.00, "rating": 4.8, "enrollment_count": 203, "schedule": "周日 14:00-17:00", "tags": "教师资格", "is_hot": True, "sort_order": 3},
            {"room_name": "去K书培训中心", "teacher_name": None, "name": "小学数学同步辅导", "category": "primaryschool", "price": 45.00, "rating": 4.6, "enrollment_count": 78, "schedule": "工作日 18:00-20:00", "tags": "小学,数学", "is_hot": False, "sort_order": 4},
            {"room_name": "去K书培训中心", "teacher_name": None, "name": "初中物理提升班", "category": "middleschool", "price": 55.00, "rating": 4.7, "enrollment_count": 95, "schedule": "工作日 19:00-21:00", "tags": "初中,物理", "is_hot": False, "sort_order": 5},
            {"room_name": "去K书·综合学习中心", "teacher_name": "张伟强", "name": "英语六级冲刺班", "category": "language", "price": 55.00, "rating": 4.7, "enrollment_count": 120, "schedule": "周六 14:00-16:30", "tags": "英语,六级", "is_hot": False, "sort_order": 1},
            {"room_name": "去K书·综合学习中心", "teacher_name": "王晓雯", "name": "公务员申论精讲", "category": "civil_service", "price": 65.00, "rating": 4.8, "enrollment_count": 110, "schedule": "周日 9:00-12:00", "tags": "公考,申论", "is_hot": False, "sort_order": 2},
        ]
        for cd in seed_courses_data:
            existing = await session.execute(
                select(Course).where(Course.name == cd["name"], Course.room_id == training_room_map[cd["room_name"]].id)
            )
            if existing.scalar_one_or_none() is not None:
                continue
            teacher_id = teacher_map[cd["teacher_name"]].id if cd["teacher_name"] else None
            session.add(Course(
                room_id=training_room_map[cd["room_name"]].id,
                teacher_id=teacher_id,
                name=cd["name"], cover_image=cd.get("cover_image"),
                category=cd["category"], price=cd["price"], rating=cd["rating"],
                enrollment_count=cd["enrollment_count"], schedule=cd["schedule"],
                tags=cd["tags"], status="active", is_hot=cd["is_hot"], sort_order=cd["sort_order"],
            ))
            print(f"  + Course: {cd['name']}")
```

- [x] **Step 4: Commit**

```bash
git add br-server/app/services/training_service.py \
  br-server/app/services/study_room_service.py \
  br-server/app/services/seed_data.py
git commit -m "feat: add training service, room_type filter, and seed data"
```

---

## Task 4: 后端 API Routes

**Files:**
- Create: `br-server/app/api/routes/training.py`
- Modify: `br-server/app/api/routes/study_room.py`
- Modify: `br-server/app/main.py`

**Interfaces:**
- Consumes: Task 3 的 `training_service.list_training_rooms`、`training_service.list_courses`、`study_room_service.list_study_rooms`
- Produces: `GET /api/v1/training/rooms`、`GET /api/v1/training/courses`；`GET /api/v1/rooms` 增加 `room_type` 查询参数

- [x] **Step 1: 创建 training 路由**

创建 `br-server/app/api/routes/training.py`：

```python
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.course import CourseListResponse, TrainingRoomListResponse
from app.services import training_service

router = APIRouter(prefix="/api/v1/training", tags=["training"])


@router.get("/rooms", response_model=TrainingRoomListResponse)
async def list_training_rooms(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    city_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> TrainingRoomListResponse:
    return await training_service.list_training_rooms(
        db, page=page, page_size=page_size, city_id=city_id
    )


@router.get("/courses", response_model=CourseListResponse)
async def list_training_courses(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1),
    category: str | None = Query(
        None,
        pattern="^(primaryschool|middleschool|postgraduate|civil_service|language|skills|professional)$",
    ),
    db: AsyncSession = Depends(get_db),
) -> CourseListResponse:
    return await training_service.list_courses(
        db, page=page, page_size=page_size, category=category
    )
```

- [x] **Step 2: 修改 study_room 路由，增加 room_type 参数**

在 `br-server/app/api/routes/study_room.py` 的 `list_study_rooms` 函数签名中，在 `city_id` 参数之后增加：

```python
    room_type: str | None = Query(None, pattern="^(study|training|comprehensive)$"),
```

并在函数调用中传递该参数：

```python
    return await study_room_service.list_study_rooms(
        db, page=page, page_size=page_size, city_id=city_id, room_type=room_type
    )
```

- [x] **Step 3: 在 main.py 注册 training_router**

在 `br-server/app/main.py` 中：

1. 在导入区（`from app.api.routes.study_room import router as study_room_router` 之后）增加：
```python
from app.api.routes.training import router as training_router
```

2. 在路由注册区（`app.include_router(study_room_router)` 之后）增加：
```python
app.include_router(training_router)
```

- [x] **Step 4: 验证路由可访问**

Run: `cd br-server && conda activate booking-room && python -c "from app.main import app; routes = [r.path for r in app.routes]; print('/api/v1/training/rooms' in routes, '/api/v1/training/courses' in routes)"`
Expected: `True True`

- [x] **Step 5: Commit**

```bash
git add br-server/app/api/routes/training.py \
  br-server/app/api/routes/study_room.py \
  br-server/app/main.py
git commit -m "feat: add training routes and room_type query param"
```

---

## Task 5: 后端测试

**Files:**
- Create: `br-server/tests/test_training_api.py`
- Modify: `br-server/tests/test_api_homepage.py`

**Interfaces:**
- Consumes: Task 1-4 的全部模型、Schema、Service、Route
- Produces: 13 个培训 API 测试用例 + 2 个 room_type 测试用例

- [x] **Step 1: 创建培训 API 测试文件**

创建 `br-server/tests/test_training_api.py`：

```python
"""Integration tests for training room and course APIs."""

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
async def seed_training_data(db_session: AsyncSession):
    """Insert training rooms, teachers, and courses into the test database."""
    # Cities
    maoming = City(name="茂名市", province="广东省", sort_order=1)
    db_session.add(maoming)
    await db_session.flush()

    # Teachers
    t1 = Teacher(name="李明华", title="考研政治名师", rating=4.9)
    t2 = Teacher(name="王晓雯", title="公考行测专家", rating=4.8)
    t3 = Teacher(name="陈雅琪", title="雅思口语讲师", rating=5.0)
    db_session.add_all([t1, t2, t3])
    await db_session.flush()

    # Training rooms (room_type=training or comprehensive)
    r1 = StudyRoom(name="去K书培训中心", address="茂名市光谷大道88号", status="open", min_price=50.00, room_type="training", city_id=maoming.id)
    r2 = StudyRoom(name="去K书·星火教室", address="茂名市文明中路56号", status="open", min_price=40.00, room_type="training")
    r3 = StudyRoom(name="去K书·综合学习中心", address="茂名市光华南路200号", status="open", min_price=10.00, room_type="comprehensive")
    # Study room (should NOT appear in training list)
    r4 = StudyRoom(name="安静自习室", address="茂名市油城三路", status="open", min_price=8.00, room_type="study")
    # Closed training room (should NOT appear)
    r5 = StudyRoom(name="关闭的培训室", address="某地址", status="closed", min_price=30.00, room_type="training")
    db_session.add_all([r1, r2, r3, r4, r5])
    await db_session.flush()

    # Courses
    courses = [
        Course(room_id=r1.id, teacher_id=t1.id, name="考研政治冲刺班", category="postgraduate", price=80.00, rating=4.9, enrollment_count=328, tags="考研,政治", status="active", is_hot=True, sort_order=1),
        Course(room_id=r1.id, teacher_id=t2.id, name="公务员行测精讲", category="civil_service", price=60.00, rating=4.8, enrollment_count=156, tags="公考,行测", status="active", is_hot=True, sort_order=2),
        Course(room_id=r1.id, teacher_id=t3.id, name="雅思口语1v1冲刺", category="language", price=120.00, rating=5.0, enrollment_count=89, tags="雅思,口语", status="active", is_hot=True, sort_order=3),
        Course(room_id=r1.id, teacher_id=t3.id, name="雅思口语进阶班", category="language", price=100.00, rating=4.8, enrollment_count=50, tags="雅思,口语", status="active", is_hot=True, sort_order=4),
        Course(room_id=r2.id, teacher_id=None, name="小学数学同步辅导", category="primaryschool", price=45.00, rating=4.6, enrollment_count=78, tags="小学,数学", status="active", is_hot=True, sort_order=1),
        Course(room_id=r3.id, teacher_id=t1.id, name="考研政治冲刺班", category="postgraduate", price=80.00, rating=4.9, enrollment_count=200, tags=None, status="active", is_hot=False, sort_order=1),
        Course(room_id=r3.id, teacher_id=None, name="初中物理提升班", category="middleschool", price=55.00, rating=4.7, enrollment_count=95, tags="", status="active", is_hot=False, sort_order=2),
    ]
    db_session.add_all(courses)
    await db_session.flush()


class TestTrainingRoomsAPI:
    @pytest.mark.asyncio
    async def test_list_training_rooms_default(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 3
        assert len(data["items"]) == 3

    @pytest.mark.asyncio
    async def test_list_training_rooms_filter_city(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms?city_id=1")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "去K书培训中心"

    @pytest.mark.asyncio
    async def test_comprehensive_room_appears(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        names = [item["name"] for item in resp.json()["items"]]
        assert "去K书·综合学习中心" in names

    @pytest.mark.asyncio
    async def test_study_room_excluded(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        names = [item["name"] for item in resp.json()["items"]]
        assert "安静自习室" not in names
        assert "关闭的培训室" not in names

    @pytest.mark.asyncio
    async def test_hot_courses_limit_3(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room1 = [r for r in data["items"] if r["name"] == "去K书培训中心"][0]
        assert len(room1["hot_courses"]) == 3

    @pytest.mark.asyncio
    async def test_hot_courses_include_teacher(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room1 = [r for r in data["items"] if r["name"] == "去K书培训中心"][0]
        hot = room1["hot_courses"][0]
        assert hot["teacher"] is not None
        assert hot["teacher"]["name"] == "李明华"

    @pytest.mark.asyncio
    async def test_training_room_no_hot_courses(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/rooms")
        data = resp.json()
        room2 = [r for r in data["items"] if r["name"] == "去K书·星火教室"][0]
        assert len(room2["hot_courses"]) >= 1


class TestCoursesAPI:
    @pytest.mark.asyncio
    async def test_list_courses_default(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 7
        assert len(data["items"]) == 7

    @pytest.mark.asyncio
    async def test_list_courses_filter_category(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=postgraduate")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 2
        for item in data["items"]:
            assert item["category"] == "postgraduate"

    @pytest.mark.asyncio
    async def test_course_teacher_nested(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=postgraduate")
        data = resp.json()
        course = [c for c in data["items"] if c["name"] == "考研政治冲刺班"][0]
        assert course["teacher"] is not None
        assert course["teacher"]["name"] == "李明华"

    @pytest.mark.asyncio
    async def test_course_without_teacher(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=primaryschool")
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["teacher"] is None

    @pytest.mark.asyncio
    async def test_course_tags_parsing(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=postgraduate")
        data = resp.json()
        course = [c for c in data["items"] if c["room_name"] == "去K书培训中心"][0]
        assert course["tags"] == ["考研", "政治"]

    @pytest.mark.asyncio
    async def test_course_empty_tags(self, client: AsyncClient, seed_training_data):
        resp = await client.get("/api/v1/training/courses?category=middleschool")
        data = resp.json()
        assert data["items"][0]["tags"] == []
```

- [x] **Step 2: 修改 test_api_homepage.py，增加 room_type 测试**

在 `br-server/tests/test_api_homepage.py` 的 `TestStudyRoomAPI` 类中增加两个测试方法：

```python
    @pytest.mark.asyncio
    async def test_room_type_filter(self, client: AsyncClient, db_session: AsyncSession):
        db_session.add(StudyRoom(name="Study Room", address="Addr A", status="open", min_price=10.00, room_type="study"))
        db_session.add(StudyRoom(name="Training Room", address="Addr B", status="open", min_price=50.00, room_type="training"))
        await db_session.flush()

        resp = await client.get("/api/v1/rooms?room_type=study")
        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["name"] == "Study Room"

    @pytest.mark.asyncio
    async def test_room_type_in_response(self, client: AsyncClient, db_session: AsyncSession):
        db_session.add(StudyRoom(name="Test Room", address="Addr", status="open", min_price=10.00, room_type="training"))
        await db_session.flush()

        resp = await client.get("/api/v1/rooms")
        assert resp.status_code == 200
        assert resp.json()["items"][0]["room_type"] == "training"
```

- [x] **Step 3: 运行全部测试**

Run: `cd br-server && conda activate booking-room && pytest tests/ -q`
Expected: 全部测试通过，无 FAIL

- [x] **Step 4: Commit**

```bash
git add br-server/tests/test_training_api.py br-server/tests/test_api_homepage.py
git commit -m "test: add training API and room_type tests"
```

---

## Task 6: 前端 API 模块

**Files:**
- Create: `br-app/src/api/training.js`

**Interfaces:**
- Consumes: `@/utils/request` 的 `get` 函数
- Produces: `getTrainingRooms(params)` → `GET /api/v1/training/rooms`；`getTrainingCourses(params)` → `GET /api/v1/training/courses`

- [x] **Step 1: 创建 training API 模块**

创建 `br-app/src/api/training.js`：

```javascript
import { get } from '@/utils/request'

/**
 * 获取培训室列表（含热门课程）
 * @param {Object} params - { page, page_size, city_id }
 */
export function getTrainingRooms(params) {
  return get('/api/v1/training/rooms', params)
}

/**
 * 获取培训课程列表
 * @param {Object} params - { page, page_size, category }
 */
export function getTrainingCourses(params) {
  return get('/api/v1/training/courses', params)
}
```

- [x] **Step 2: Commit**

```bash
git add br-app/src/api/training.js
git commit -m "feat: add training API module"
```

---

## Task 7: 前端页面实现

**Files:**
- Create: `br-app/src/pages/training/index.vue`

**Interfaces:**
- Consumes: Task 6 的 `getTrainingRooms`、`getTrainingCourses`；`@/utils/request` 间接通过 API 模块
- Produces: 培训课程列表页 Vue 组件，包含搜索栏、分类 TAB、培训室卡片（可展开热门课程）、课程卡片列表

- [ ] **Step 1: 创建培训课程列表页**

创建 `br-app/src/pages/training/index.vue`（注意：`onMounted` 从 `vue` 导入——BUG-14 防范；模板中不使用 `&lt;`/`&gt;`——BUG-20 防范）：

```vue
<template>
  <view class="page">
    <!-- 自定义导航栏 -->
    <view class="nav-bar">
      <text class="nav-title">培训课程</text>
    </view>

    <!-- 搜索栏 -->
    <view class="search-bar">
      <view class="search-input-wrap">
        <text class="search-icon">🔍</text>
        <input
          class="search-input"
          type="text"
          placeholder="搜索课程、老师"
          placeholder-class="search-placeholder"
        />
      </view>
    </view>

    <!-- 分类 TAB -->
    <scroll-view class="tab-bar" scroll-x :show-scrollbar="false">
      <view
        v-for="tab in tabs"
        :key="tab.key"
        :class="['tab-item', { 'tab-active': activeTab === tab.key }]"
        @tap="switchTab(tab.key)"
      >
        <text class="tab-text">{{ tab.label }}</text>
      </view>
    </scroll-view>

    <!-- 内容区域 -->
    <view class="content">
      <!-- 加载状态 -->
      <view v-if="loading && trainingRooms.length === 0 && courses.length === 0" class="loading-state">
        <text class="loading-text">加载中...</text>
      </view>

      <!-- 空状态 -->
      <view v-else-if="!loading && activeTab === 'all' && trainingRooms.length === 0" class="empty-state">
        <text class="empty-text">暂无培训室</text>
      </view>
      <view v-else-if="!loading && activeTab !== 'all' && courses.length === 0" class="empty-state">
        <text class="empty-text">暂无课程</text>
      </view>

      <!-- 全部：培训室列表 -->
      <template v-else-if="activeTab === 'all'">
        <view
          v-for="room in trainingRooms"
          :key="room.id"
          class="room-card"
        >
          <view class="room-header" @tap="toggleExpand(room.id)">
            <image
              class="room-cover"
              :src="room.cover_image || 'https://images.unsplash.com/photo-1580582932705-ff3c3993141f?w=300&h=400&fit=crop'"
              mode="aspectFill"
            />
            <view class="room-info">
              <view class="room-name-row">
                <text class="room-name">{{ room.name }}</text>
                <text :class="['room-status', room.status === 'open' ? 'status-open' : 'status-closed']">
                  {{ room.status === 'open' ? '营业中' : '休息中' }}
                </text>
              </view>
              <view class="room-meta">
                <text class="meta-rating">★ {{ room.min_price }}起</text>
                <text class="meta-dot">·</text>
                <text class="meta-address">{{ room.address }}</text>
              </view>
              <view class="hot-courses-label">
                <text class="hot-label-text">热门推荐课程</text>
                <text :class="['expand-icon', { 'expand-icon-rotated': expandedRooms.has(room.id) }]">▼</text>
              </view>
            </view>
          </view>
          <view :class="['room-courses', { 'room-courses-expanded': expandedRooms.has(room.id) }]">
            <view
              v-for="course in room.hot_courses"
              :key="course.id"
              class="hot-course-item"
            >
              <image
                class="hot-course-cover"
                :src="course.cover_image || 'https://images.unsplash.com/photo-1546410531-bb4caa6b5cb9?w=100&h=100&fit=crop'"
                mode="aspectFill"
              />
              <view class="hot-course-info">
                <text class="hot-course-name">{{ course.name }}</text>
                <text class="hot-course-meta">
                  {{ course.teacher ? course.teacher.name : '未知讲师' }} · {{ course.enrollment_count }}人
                </text>
              </view>
              <text class="hot-course-price">¥{{ course.price }}</text>
            </view>
          </view>
        </view>
      </template>

      <!-- 分类：课程列表 -->
      <template v-else>
        <view
          v-for="course in courses"
          :key="course.id"
          class="course-card"
        >
          <image
            class="course-cover"
            :src="course.cover_image || 'https://images.unsplash.com/photo-1546410531-bb4caa6b5cb9?w=300&h=300&fit=crop'"
            mode="aspectFill"
          />
          <view class="course-info">
            <view class="course-name-row">
              <text class="course-name">{{ course.name }}</text>
              <text v-if="course.is_hot" class="course-badge badge-hot">热销</text>
            </view>
            <view class="course-teacher">
              <text class="teacher-name">{{ course.teacher ? course.teacher.name + ' 老师' : '未知老师' }}</text>
              <text class="course-dot">·</text>
              <text class="room-name-text">{{ course.room_name }}</text>
            </view>
            <view class="course-stats">
              <text class="stats-rating">★ {{ course.rating }}</text>
              <text class="stats-count">{{ course.enrollment_count }}人已学</text>
            </view>
            <view class="course-footer">
              <view class="course-price-wrap">
                <text class="course-price">¥{{ course.price }}</text>
                <text class="course-price-unit">/课时</text>
              </view>
              <view class="course-book-btn">
                <text class="book-btn-text">预约</text>
              </view>
            </view>
          </view>
        </view>
      </template>
    </view>
  </view>
</template>

<script setup>
import { ref, watch } from 'vue'
import { onMounted } from 'vue'
import { onReachBottom } from '@dcloudio/uni-app'
import { getTrainingRooms, getTrainingCourses } from '@/api/training'

const activeTab = ref('all')
const trainingRooms = ref([])
const courses = ref([])
const loading = ref(false)
const expandedRooms = ref(new Set())
const roomPage = ref(1)
const roomTotal = ref(0)
const coursePage = ref(1)
const courseTotal = ref(0)

const tabs = [
  { key: 'all', label: '全部' },
  { key: 'primaryschool', label: '小学辅导' },
  { key: 'middleschool', label: '中学辅导' },
  { key: 'civil_service', label: '公考备考' },
  { key: 'skills', label: '技能提升' },
]

function switchTab(key) {
  activeTab.value = key
}

function toggleExpand(roomId) {
  if (expandedRooms.value.has(roomId)) {
    expandedRooms.value.delete(roomId)
  } else {
    expandedRooms.value.add(roomId)
  }
  expandedRooms.value = new Set(expandedRooms.value)
}

async function fetchTrainingRooms(reset = false) {
  if (loading.value) return
  if (reset) {
    roomPage.value = 1
    trainingRooms.value = []
  }
  loading.value = true
  try {
    const data = await getTrainingRooms({
      page: roomPage.value,
      page_size: 10,
    })
    trainingRooms.value = reset ? data.items : trainingRooms.value.concat(data.items)
    roomTotal.value = data.total || 0
    if (!reset) roomPage.value++
  } catch {
    if (reset) trainingRooms.value = []
  } finally {
    loading.value = false
  }
}

async function fetchCourses(reset = false) {
  if (loading.value) return
  if (reset) {
    coursePage.value = 1
    courses.value = []
  }
  loading.value = true
  try {
    const data = await getTrainingCourses({
      page: coursePage.value,
      page_size: 10,
      category: activeTab.value !== 'all' ? activeTab.value : undefined,
    })
    courses.value = reset ? data.items : courses.value.concat(data.items)
    courseTotal.value = data.total || 0
    if (!reset) coursePage.value++
  } catch {
    if (reset) courses.value = []
  } finally {
    loading.value = false
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'all') {
    fetchTrainingRooms(true)
  } else {
    fetchCourses(true)
  }
})

onMounted(() => {
  fetchTrainingRooms(true)
})

onReachBottom(() => {
  if (activeTab.value === 'all') {
    if (trainingRooms.value.length < roomTotal.value) {
      fetchTrainingRooms(false)
    }
  } else {
    if (courses.value.length < courseTotal.value) {
      fetchCourses(false)
    }
  }
})
</script>

<style lang="scss" scoped>
.page {
  min-height: 100vh;
  background: #F5F6FA;
  padding-bottom: 120rpx;
}

.nav-bar {
  position: fixed;
  top: 0;
  left: 0;
  right: 0;
  z-index: 100;
  height: 88rpx;
  background: #ffffff;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: 0 1rpx 0 rgba(0, 0, 0, 0.04);
}

.nav-title {
  font-size: 34rpx;
  font-weight: 600;
  color: #2D3436;
}

.search-bar {
  position: fixed;
  top: 88rpx;
  left: 0;
  right: 0;
  z-index: 90;
  background: #ffffff;
  padding: 16rpx 32rpx;
  border-bottom: 1rpx solid #F0F0F0;
}

.search-input-wrap {
  background: #F1F2F6;
  border-radius: 999rpx;
  padding: 16rpx 28rpx;
  display: flex;
  align-items: center;
  gap: 12rpx;
}

.search-icon {
  font-size: 24rpx;
  color: #B2BEC3;
}

.search-input {
  flex: 1;
  font-size: 28rpx;
  color: #2D3436;
}

.search-placeholder {
  color: #C8C9CB;
}

.tab-bar {
  position: fixed;
  top: 176rpx;
  left: 0;
  right: 0;
  z-index: 80;
  background: #ffffff;
  white-space: nowrap;
  border-bottom: 1rpx solid #F0F0F0;
}

.tab-item {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  padding: 16rpx 0;
  margin: 0 24rpx;
  position: relative;
}

.tab-text {
  font-size: 28rpx;
  color: #636E72;
}

.tab-active .tab-text {
  color: #4F6EF7;
  font-weight: 600;
}

.tab-active::after {
  content: '';
  position: absolute;
  bottom: 0;
  left: 50%;
  transform: translateX(-50%);
  width: 40rpx;
  height: 4rpx;
  background: #4F6EF7;
  border-radius: 2rpx;
}

.content {
  padding-top: 248rpx;
}

.loading-state,
.empty-state {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 120rpx 0;
}

.loading-text,
.empty-text {
  font-size: 28rpx;
  color: #B2BEC3;
}

.room-card {
  margin: 24rpx 32rpx;
  background: #ffffff;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
}

.room-header {
  display: flex;
  padding: 0;
}

.room-cover {
  width: 224rpx;
  height: 256rpx;
  flex-shrink: 0;
}

.room-info {
  flex: 1;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.room-name-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.room-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #2D3436;
  flex: 1;
}

.room-status {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  margin-left: 12rpx;
}

.status-open {
  background: #E8F8E8;
  color: #00B894;
}

.status-closed {
  background: #FFF3E0;
  color: #FF9500;
}

.room-meta {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 12rpx;
}

.meta-rating {
  font-size: 24rpx;
  font-weight: 500;
  color: #2D3436;
}

.meta-dot {
  font-size: 20rpx;
  color: #B2BEC3;
}

.meta-address {
  font-size: 22rpx;
  color: #636E72;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-courses-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-top: 16rpx;
}

.hot-label-text {
  font-size: 24rpx;
  color: #4F6EF7;
  background: #F0F1F8;
  padding: 6rpx 16rpx;
  border-radius: 8rpx;
}

.expand-icon {
  font-size: 20rpx;
  color: #B2BEC3;
  transition: transform 0.3s ease;
}

.expand-icon-rotated {
  transform: rotate(180deg);
}

.room-courses {
  max-height: 0;
  overflow: hidden;
  transition: max-height 0.35s ease;
}

.room-courses-expanded {
  max-height: 1000rpx;
}

.hot-course-item {
  display: flex;
  align-items: center;
  gap: 16rpx;
  padding: 12rpx 24rpx;
  border-top: 1rpx solid #F8F8F8;
}

.hot-course-cover {
  width: 72rpx;
  height: 72rpx;
  border-radius: 12rpx;
  flex-shrink: 0;
}

.hot-course-info {
  flex: 1;
  min-width: 0;
}

.hot-course-name {
  font-size: 26rpx;
  font-weight: 500;
  color: #2D3436;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.hot-course-meta {
  font-size: 22rpx;
  color: #B2BEC3;
  margin-top: 4rpx;
}

.hot-course-price {
  font-size: 30rpx;
  font-weight: 600;
  color: #4F6EF7;
  flex-shrink: 0;
}

.course-card {
  margin: 24rpx 32rpx;
  background: #ffffff;
  border-radius: 28rpx;
  overflow: hidden;
  box-shadow: 0 4rpx 16rpx rgba(0, 0, 0, 0.04);
  display: flex;
}

.course-cover {
  width: 224rpx;
  height: 224rpx;
  flex-shrink: 0;
}

.course-info {
  flex: 1;
  padding: 24rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
}

.course-name-row {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
}

.course-name {
  font-size: 28rpx;
  font-weight: 600;
  color: #2D3436;
  flex: 1;
}

.course-badge {
  font-size: 20rpx;
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
  margin-left: 12rpx;
}

.badge-hot {
  background: #FFEAEA;
  color: #FF4757;
}

.course-teacher {
  display: flex;
  align-items: center;
  gap: 8rpx;
  margin-top: 12rpx;
}

.teacher-name {
  font-size: 24rpx;
  color: #636E72;
}

.course-dot {
  font-size: 20rpx;
  color: #B2BEC3;
}

.room-name-text {
  font-size: 22rpx;
  color: #636E72;
}

.course-stats {
  display: flex;
  align-items: center;
  gap: 16rpx;
  margin-top: 12rpx;
}

.stats-rating {
  font-size: 24rpx;
  font-weight: 500;
  color: #2D3436;
}

.stats-count {
  font-size: 22rpx;
  color: #B2BEC3;
}

.course-footer {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 12rpx;
}

.course-price-wrap {
  display: flex;
  align-items: baseline;
  gap: 4rpx;
}

.course-price {
  font-size: 36rpx;
  font-weight: 700;
  color: #4F6EF7;
}

.course-price-unit {
  font-size: 22rpx;
  color: #B2BEC3;
}

.course-book-btn {
  background: rgba(79, 110, 247, 0.1);
  border-radius: 999rpx;
  padding: 10rpx 24rpx;
}

.book-btn-text {
  font-size: 24rpx;
  color: #4F6EF7;
  font-weight: 500;
}
</style>
```

- [ ] **Step 2: Commit**

```bash
git add br-app/src/pages/training/index.vue
git commit -m "feat: add training course list page"
```

---

## Task 8: 前端底部导航

**Files:**
- Modify: `br-app/src/pages.json`

**Interfaces:**
- Consumes: Task 7 的 `pages/training/index` 页面
- Produces: tabBar 中第 3 位插入"培训"入口

- [ ] **Step 1: 在 pages.json 注册培训页面路由**

在 `br-app/src/pages.json` 的 `pages` 数组中增加培训页面注册条目（建议放在 `pages/index/index` 之后）：

```json
{
  "path": "pages/training/index",
  "style": {
    "navigationBarTitleText": "培训课程",
    "navigationStyle": "custom"
  }
}
```

- [ ] **Step 2: 在 tabBar 中第 3 位插入培训入口**

在 `br-app/src/pages.json` 的 `tabBar.list` 数组中，在"预约"和"订单"之间插入：

```json
{
  "pagePath": "pages/training/index",
  "text": "培训",
  "iconPath": "static/tab/training.png",
  "selectedIconPath": "static/tab/training-active.png"
}
```

**图标文件**：需准备 `br-app/src/static/tab/training.png` 和 `br-app/src/static/tab/training-active.png`（graduation-cap 风格，81x81px PNG，灰色和蓝色版本，参考现有 `booking.png`/`booking-active.png` 的风格和尺寸）。

- [ ] **Step 3: 验证前端构建**

Run: `nvm use v22.22.0 && cd br-app && npm run build`
Expected: 构建成功，无错误

- [ ] **Step 4: Commit**

```bash
git add br-app/src/pages.json br-app/src/static/tab/training.png \
  br-app/src/static/tab/training-active.png
git commit -m "feat: add training tab to bottom navigation"
```

---

## Task 9: 代码审查与重构

**Files:**
- Review: 全部新建和修改的文件

**Interfaces:**
- Consumes: Task 1-8 的全部产出
- Produces: 代码质量确认，必要时进行小范围重构

- [ ] **Step 1: 验证后端 Clean Architecture 分层**

检查以下分层约束：
- `br-server/app/api/routes/training.py`：仅处理 HTTP 请求/响应，调用 service 层，不直接操作 ORM
- `br-server/app/services/training_service.py`：处理业务逻辑，调用 model 层查询，组装 schema 响应
- `br-server/app/models/teacher.py` 和 `course.py`：仅定义数据模型，不含业务逻辑
- `br-server/app/schemas/course.py`：仅定义响应结构，不含业务逻辑（`parse_tags` 验证器除外）

如发现分层违规，在此步骤修正。

- [ ] **Step 2: 消除重复代码 — 提取枚举常量**

检查 `room_type` 枚举值（`study`/`training`/`comprehensive`）和 `category` 枚举值（`primaryschool`/`middleschool`/`postgraduate`/`civil_service`/`language`/`skills`/`professional`）是否在多处硬编码。

如发现在 3 处以上重复，提取为常量模块。例如可在 `br-server/app/models/constants.py` 中定义：

```python
ROOM_TYPES = ("study", "training", "comprehensive")
COURSE_CATEGORIES = ("primaryschool", "middleschool", "postgraduate", "civil_service", "language", "skills", "professional")
```

并在路由的 `pattern` 参数和 service 层的 `in_()` 过滤中引用。

- [ ] **Step 3: 验证前端组件分层**

检查：
- `br-app/src/pages/training/index.vue` 调用 `@/api/training.js`
- `br-app/src/api/training.js` 调用 `@/utils/request.js` 的 `get` 函数
- 页面不直接调用 `uni.request`，API 模块不包含 UI 逻辑

- [ ] **Step 4: 检查路由无尾部斜杠**

验证 `br-server/app/api/routes/training.py` 中：
- `@router.get("/rooms")` — 无尾部斜杠 ✓
- `@router.get("/courses")` — 无尾部斜杠 ✓

验证 `br-server/app/api/routes/study_room.py` 中新增的 `room_type` 参数不引入尾部斜杠问题。

- [ ] **Step 5: Commit（如有修改）**

```bash
git add -A
git commit -m "refactor: code review fixes for training feature"
```

---

## Task 10: API 文档更新

**Files:**
- Modify: `docs/api.md`

**Interfaces:**
- Consumes: Task 4 的路由定义
- Produces: `docs/api.md` 中 3 个接口文档段落

- [ ] **Step 1: 补充 GET /api/v1/training/rooms 接口文档**

在 `docs/api.md` 中适当位置（如"自习室"章节之后）增加：

```markdown
## 培训课程

### GET /api/v1/training/rooms

获取培训室分页列表（含热门课程），返回 room_type 为 training 或 comprehensive 且 status 为 open 的培训室。

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码，最小 1 |
| page_size | integer | 10 | 每页数量，最大 50 |
| city_id | integer | - | 可选城市 ID 过滤 |

**响应 200：**

```json
{
  "items": [
    {
      "id": 1,
      "name": "去K书培训中心",
      "description": "名师一对一辅导",
      "cover_image": "https://...",
      "address": "茂名市茂南区光谷大道88号3楼",
      "city_id": 1,
      "city_name": "茂名市",
      "business_hours": "08:00-22:00",
      "status": "open",
      "room_type": "training",
      "min_price": 50.00,
      "hot_courses": [
        {
          "id": 1,
          "name": "考研政治冲刺班",
          "cover_image": "https://...",
          "teacher": {
            "id": 1,
            "name": "李明华",
            "avatar": "https://...",
            "title": "考研政治名师",
            "rating": 4.9
          },
          "price": 80.00,
          "enrollment_count": 328
        }
      ]
    }
  ],
  "total": 3,
  "page": 1,
  "page_size": 10
}
```
```

- [ ] **Step 2: 补充 GET /api/v1/training/courses 接口文档**

紧接上一步之后增加：

```markdown
### GET /api/v1/training/courses

获取培训课程分页列表，仅返回 status 为 active 的课程。

**查询参数：**

| 字段 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| page | integer | 1 | 页码，最小 1 |
| page_size | integer | 10 | 每页数量，最大 50 |
| category | string | - | 可选分类：`primaryschool`/`middleschool`/`postgraduate`/`civil_service`/`language`/`skills`/`professional` |

**响应 200：**

```json
{
  "items": [
    {
      "id": 1,
      "name": "考研政治冲刺班",
      "cover_image": "https://...",
      "teacher": {
        "id": 1,
        "name": "李明华",
        "avatar": "https://...",
        "title": "考研政治名师",
        "rating": 4.9
      },
      "category": "postgraduate",
      "price": 80.00,
      "rating": 4.9,
      "enrollment_count": 328,
      "schedule": "周六 9:00-12:00",
      "tags": ["考研", "政治"],
      "status": "active",
      "room_id": 1,
      "room_name": "去K书培训中心"
    }
  ],
  "total": 10,
  "page": 1,
  "page_size": 10
}
```
```

- [ ] **Step 3: 更新 GET /api/v1/rooms 接口文档**

在 `docs/api.md` 中现有的 `GET /api/v1/rooms` 文档的查询参数表格中增加 `room_type` 行：

```markdown
| room_type | string | - | 可选房间类型：`study`/`training`/`comprehensive` |
```

在响应示例中增加 `room_type` 字段：

```json
"room_type": "study"
```

- [ ] **Step 4: Commit**

```bash
git add docs/api.md
git commit -m "docs: add training API documentation and room_type param"
```

---

## Task 11: 最终验证

**Files:**
- 无文件修改，仅运行验证命令

**Interfaces:**
- Consumes: Task 1-10 的全部产出

- [ ] **Step 1: 运行后端全部测试**

Run: `cd br-server && conda activate booking-room && pytest tests/ -q`
Expected: 全部测试通过，0 FAIL，0 ERROR

- [ ] **Step 2: 前端构建验证**

Run: `nvm use v22.22.0 && cd br-app && npm run build`
Expected: 构建成功，无 error

- [ ] **Step 3: 验证现有自习室预约功能不受影响**

手动验证（或通过现有测试覆盖）：
- `GET /api/v1/rooms` 不带 `room_type` 参数时返回所有类型房间（行为不变）
- `GET /api/v1/rooms/{room_id}` 详情接口正常返回（增加了 `room_type` 字段但不影响现有字段）
- 现有的 `test_api_homepage.py` 中原有测试仍然通过（Step 1 已覆盖）

- [ ] **Step 4: 最终 Commit（如有遗漏的修改）**

```bash
git add -A
git commit -m "chore: final verification for training course list feature"
```

---

## BUG 防范清单

| BUG | 防范措施 | 涉及 Task |
|-----|---------|-----------|
| BUG-14 | `onMounted` 从 `vue` 导入，`onReachBottom` 从 `@dcloudio/uni-app` 导入 | Task 7 |
| BUG-15 | 迁移和种子数据中 timestamps 使用 `func.now()`，不传 `datetime.now(UTC)` | Task 1, 3 |
| BUG-20 | 前端模板中不使用 `&lt;`/`&gt;`，使用 Unicode 字符 `‹`/`›` 或 `▼` | Task 7 |
| BUG-22 | 新路由 `@router.get("/rooms")` 和 `@router.get("/courses")` 无尾部斜杠 | Task 4 |
| BUG-16 | 不使用 ORM relationship，service 层显式 JOIN | Task 1, 3 |
| BUG-13 | 前端 API 中 page_size 不超过 50（MAX_PAGE_SIZE = 50） | Task 3, 6 |
