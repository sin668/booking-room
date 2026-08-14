---
change: training-room-overview
design-doc: docs/superpowers/specs/2026-08-14-training-room-overview-design.md
base-ref: 4ecad224175e2279d7e824f8c6292e1000b137b5
---

# 培训室概况功能 实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在 booking/detail.vue 详情页中，根据 `room_type` 字段条件渲染培训室概况（教室统计、名师团队、课程列表），同时保持自习室原有行为不变。

**Architecture:** 后端新增 `TrainingService.get_training_room_detail()` 方法，查询 `study_rooms`（room_type 为 training/comprehensive）关联 `courses` + `teachers` 表，聚合统计后返回 `TrainingRoomDetailResponse`。前端 `detail.vue` 根据 `room_type` 条件调用不同 API 并渲染对应 UI 模块。

**Tech Stack:** FastAPI + SQLAlchemy async + Pydantic v2（后端）；uni-app + Vue 2 Options API + SCSS（前端）

**Design Doc:** `docs/superpowers/specs/2026-08-14-training-room-overview-design.md`

## Global Constraints

- 路由定义**不使用尾部斜杠**（参考 bug-fixed.md BUG-22），如 `@router.get("/{room_id}")` 而非 `@router.get("/{room_id}/")`
- Vue3 生命周期钩子从 `vue` 包导入，uni-app 钩子从 `@dcloudio/uni-app` 导入（参考 bug-fixed.md BUG-14）
- Vue 模板中**不使用** `&lt;` `&gt;` HTML 实体，用 Unicode 字符 `‹` `›` 替代（参考 bug-fixed.md BUG-20）
- 不使用列表接口 `page_size=100` 获取单条数据，使用详情接口（参考 bug-fixed.md BUG-13）
- 后端 Clean Architecture 分层：routes 仅处理 HTTP → services 处理业务逻辑 → models 定义数据 → schemas 定义响应
- 复用 `training-course-list` change 定义的 `TeacherResponse` 和 `CourseResponse`，不重复定义
- 数据库迁移需要先执行（依赖 `training-course-list` 的 `room_type` 列等）

---

## 文件结构

### 新建文件

| 文件路径 | 职责 |
|---------|------|
| `br-server/app/models/teacher.py` | Teacher ORM 模型（teachers 表） |
| `br-server/app/models/course.py` | Course ORM 模型（courses 表） |
| `br-server/app/schemas/teacher.py` | TeacherResponse Pydantic schema |
| `br-server/app/schemas/course.py` | CourseResponse + TrainingRoomDetailResponse schema |
| `br-server/app/services/training_service.py` | TrainingService（培训室详情业务逻辑） |
| `br-server/app/api/routes/training.py` | 培训模块 API 路由（prefix=/api/v1/training/rooms） |
| `br-server/alembic/versions/2026_08_14_1000-e3f4a5b6c7d8_add_training_tables.py` | 数据库迁移：room_type/rating 列 + teachers/courses 表 |
| `br-server/tests/test_training_api.py` | 培训室详情接口测试 |
| `br-app/src/api/training.js` | 前端培训 API 模块 |

### 修改文件

| 文件路径 | 修改内容 |
|---------|---------|
| `br-server/app/models/study_room.py` | 新增 `room_type`、`rating` 列 + `city` relationship |
| `br-server/app/models/__init__.py` | 注册 Teacher、Course 模型 |
| `br-server/app/main.py` | 注册 training_router |
| `br-app/src/pages/booking/detail.vue` | data/computed/template/methods/style 全面重构 |
| `docs/api.md` | 补充培训室详情接口文档 |

---

### Task 1: 后端 Model 扩展与迁移（前置依赖）

> 对应 tasks.md 前置依赖（training-course-list change 的数据库基础设施）。当前 StudyRoom 模型缺少 `room_type`、`rating` 字段，且无 Teacher/Course 模型。

**Files:**
- Modify: `br-server/app/models/study_room.py`
- Create: `br-server/app/models/teacher.py`
- Create: `br-server/app/models/course.py`
- Modify: `br-server/app/models/__init__.py`
- Create: `br-server/alembic/versions/2026_08_14_1000-e3f4a5b6c7d8_add_training_tables.py`

**Interfaces:**
- Produces: `StudyRoom.room_type` (str, 默认 "study"), `StudyRoom.rating` (float, 默认 0), `StudyRoom.city` (relationship → City)
- Produces: `Teacher` model (id, name, avatar, title, rating, created_at, updated_at)
- Produces: `Course` model (id, room_id, teacher_id, name, cover_image, category, price, rating, enrollment_count, schedule, tags, status, is_hot, sort_order, created_at, updated_at)

**Bug 防护：**
- BUG-22: 迁移中不涉及路由，无尾部斜杠问题
- 参考现有迁移文件格式（如 `2026_06_02_1000-c9d0e1f2a3b4_add_room_follows.py`），`down_revision` 指向最新迁移 `a2b3c4d5e6f7`

- [x] **Step 1: 修改 StudyRoom 模型，新增 room_type、rating 列和 city relationship**

修改 `br-server/app/models/study_room.py`，在 `min_price` 之后添加 `room_type` 和 `rating` 列，并添加 `city` relationship：

```python
from sqlalchemy import DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

class StudyRoom(Base):
    __tablename__ = "study_rooms"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    address: Mapped[str] = mapped_column(String(255), nullable=False)
    city_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("cities.id"), nullable=True
    )
    business_hours: Mapped[str | None] = mapped_column(String(50), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False)
    room_type: Mapped[str] = mapped_column(String(20), default="study", nullable=False)
    min_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    city = relationship("City")
```

- [x] **Step 2: 创建 Teacher 模型**

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
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [x] **Step 3: 创建 Course 模型**

创建 `br-server/app/models/course.py`：

```python
from datetime import datetime
from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class Course(Base):
    __tablename__ = "courses"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_rooms.id"), nullable=False
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id"), nullable=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    cover_image: Mapped[str | None] = mapped_column(String(512), nullable=True)
    category: Mapped[str] = mapped_column(String(30), nullable=False)
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    rating: Mapped[float] = mapped_column(Numeric(3, 1), default=0, nullable=False)
    enrollment_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schedule: Mapped[str | None] = mapped_column(String(200), nullable=True)
    tags: Mapped[str | None] = mapped_column(String(200), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="active", nullable=False)
    is_hot: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    sort_order: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
```

- [x] **Step 4: 注册新模型到 __init__.py**

修改 `br-server/app/models/__init__.py`，添加导入和 __all__ 条目：

```python
from app.models.course import Course
from app.models.teacher import Teacher
```

在 `__all__` 列表中添加 `"Course"` 和 `"Teacher"`。

- [x] **Step 5: 创建 Alembic 迁移文件**

创建 `br-server/alembic/versions/2026_08_14_1000-e3f4a5b6c7d8_add_training_tables.py`：

```python
"""add training tables and room_type/rating columns

Revision ID: e3f4a5b6c7d8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-14 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "e3f4a5b6c7d8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name

    # Add room_type and rating columns to study_rooms
    if dialect_name == "sqlite":
        with op.batch_alter_table("study_rooms") as batch_op:
            batch_op.add_column(
                sa.Column("room_type", sa.String(20), nullable=False, server_default="study")
            )
            batch_op.add_column(
                sa.Column("rating", sa.Numeric(3, 1), nullable=False, server_default="0")
            )
    else:
        op.add_column(
            "study_rooms",
            sa.Column("room_type", sa.String(20), nullable=False, server_default="study"),
        )
        op.add_column(
            "study_rooms",
            sa.Column("rating", sa.Numeric(3, 1), nullable=False, server_default="0"),
        )

    # Create teachers table
    op.create_table(
        "teachers",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("avatar", sa.String(512), nullable=True),
        sa.Column("title", sa.String(50), nullable=True),
        sa.Column("rating", sa.Numeric(3, 1), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # Create courses table
    op.create_table(
        "courses",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("teacher_id", sa.Integer(), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cover_image", sa.String(512), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("rating", sa.Numeric(3, 1), nullable=False, server_default="0"),
        sa.Column("enrollment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("schedule", sa.String(200), nullable=True),
        sa.Column("tags", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), nullable=False, server_default="active"),
        sa.Column("is_hot", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["study_rooms.id"]),
        sa.ForeignKeyConstraint(["teacher_id"], ["teachers.id"]),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_courses_room_id", "courses", ["room_id"], unique=False)
    op.create_index("ix_courses_category", "courses", ["category"], unique=False)
    op.create_index("ix_courses_status", "courses", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_courses_status", table_name="courses")
    op.drop_index("ix_courses_category", table_name="courses")
    op.drop_index("ix_courses_room_id", table_name="courses")
    op.drop_table("courses")
    op.drop_table("teachers")

    dialect_name = op.get_bind().dialect.name
    if dialect_name == "sqlite":
        with op.batch_alter_table("study_rooms") as batch_op:
            batch_op.drop_column("rating")
            batch_op.drop_column("room_type")
    else:
        op.drop_column("study_rooms", "rating")
        op.drop_column("study_rooms", "room_type")
```

- [x] **Step 6: 运行迁移**

```bash
cd br-server && conda activate booking-room && alembic upgrade head
```

Expected: 迁移成功，无报错。

- [x] **Step 7: Commit**

```bash
git add br-server/app/models/study_room.py br-server/app/models/teacher.py br-server/app/models/course.py br-server/app/models/__init__.py br-server/alembic/versions/2026_08_14_1000-e3f4a5b6c7d8_add_training_tables.py
git commit -m "feat: add Teacher/Course models, room_type/rating columns, migration"
```

---

### Task 2: 后端 Schema（tasks.md 1.1-1.3）

**Files:**
- Create: `br-server/app/schemas/teacher.py`
- Create: `br-server/app/schemas/course.py`

**Interfaces:**
- Produces: `TeacherResponse`（id: int, name: str, avatar: str|None, title: str|None, rating: float）
- Produces: `CourseResponse`（id, name, cover_image, teacher: TeacherResponse|None, category, price, rating, enrollment_count, schedule, tags: list[str], status, room_id, room_name）
- Produces: `TrainingRoomDetailResponse`（房间基本信息 + teachers 数组 + courses 数组 + 教室概况统计字段）

**Bug 防护：**
- 复用 schema，不在多个文件重复定义（参考 bug-fixed.md BUG-7 DRY 原则）

- [x] **Step 1: 创建 TeacherResponse schema**

创建 `br-server/app/schemas/teacher.py`：

```python
from pydantic import BaseModel, ConfigDict


class TeacherResponse(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: float

    model_config = ConfigDict(from_attributes=True)
```

- [x] **Step 2: 创建 CourseResponse 和 TrainingRoomDetailResponse schema**

创建 `br-server/app/schemas/course.py`：

```python
from typing import Optional

from pydantic import BaseModel, ConfigDict

from app.schemas.teacher import TeacherResponse


class CourseResponse(BaseModel):
    id: int
    name: str
    cover_image: str | None = None
    teacher: TeacherResponse | None = None
    category: str
    price: float
    rating: float
    enrollment_count: int
    schedule: str | None = None
    tags: list[str] = []
    status: str
    room_id: int
    room_name: str

    model_config = ConfigDict(from_attributes=True)


class TrainingRoomDetailResponse(BaseModel):
    # 房间基本信息
    id: int
    name: str
    description: Optional[str] = None
    cover_image: Optional[str] = None
    address: str
    business_hours: Optional[str] = None
    status: str
    room_type: str
    min_price: float
    city_id: Optional[int] = None
    city_name: Optional[str] = None
    rating: float

    # 教室概况统计
    classroom_count: int
    class_capacity: str
    teacher_count: int
    total_students: int

    # 名师团队
    teachers: list[TeacherResponse]

    # 课程列表
    courses: list[CourseResponse]
```

- [x] **Step 3: Commit**

```bash
git add br-server/app/schemas/teacher.py br-server/app/schemas/course.py
git commit -m "feat: add TeacherResponse, CourseResponse, TrainingRoomDetailResponse schemas"
```

---

### Task 3: 后端 Service（tasks.md 2.1-2.5）

**Files:**
- Create: `br-server/app/services/training_service.py`

**Interfaces:**
- Consumes: `StudyRoom`（含 room_type, rating, city relationship）, `Course`, `Teacher` 模型；`TeacherResponse`, `CourseResponse`, `TrainingRoomDetailResponse` schemas
- Produces: `TrainingService.get_training_room_detail(room_id: int) -> Optional[TrainingRoomDetailResponse]`

**Bug 防护：**
- BUG-16: 不返回 ORM 对象，所有数据组装为 Pydantic schema 返回，避免 SQLAlchemy 懒加载/greenlet 问题
- 教师去重使用 `teachers_map` 字典按 `teacher_id` 去重
- LEFT JOIN 使用 `outerjoin` 确保未关联教师的课程也被查询到
- tags 解析：`course.tags.split(',') if course.tags else []`

- [ ] **Step 1: 创建 TrainingService 类**

创建 `br-server/app/services/training_service.py`：

```python
from typing import Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.schemas.course import CourseResponse, TrainingRoomDetailResponse
from app.schemas.teacher import TeacherResponse


class TrainingService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_training_room_detail(
        self, room_id: int
    ) -> Optional[TrainingRoomDetailResponse]:
        # Step 1: 查询房间，验证 room_type
        room_result = await self.db.execute(
            select(StudyRoom).where(
                StudyRoom.id == room_id,
                StudyRoom.room_type.in_(["training", "comprehensive"]),
            )
        )
        room_obj = room_result.scalar_one_or_none()
        if not room_obj:
            return None

        # Step 2: 查询该房间下 status=active 的课程，LEFT JOIN teachers
        courses_result = await self.db.execute(
            select(Course, Teacher)
            .outerjoin(Teacher, Course.teacher_id == Teacher.id)
            .where(Course.room_id == room_id, Course.status == "active")
            .order_by(Course.sort_order)
        )
        rows = courses_result.all()

        # Step 3: 组装课程列表 + 去重教师
        courses_data = []
        teachers_map = {}
        total_students = 0

        for course, teacher in rows:
            teacher_response = None
            if teacher:
                if teacher.id not in teachers_map:
                    teachers_map[teacher.id] = TeacherResponse(
                        id=teacher.id,
                        name=teacher.name,
                        avatar=teacher.avatar,
                        title=teacher.title,
                        rating=float(teacher.rating),
                    )
                teacher_response = teachers_map[teacher.id]

            tags = course.tags.split(",") if course.tags else []
            courses_data.append(
                CourseResponse(
                    id=course.id,
                    name=course.name,
                    cover_image=course.cover_image,
                    teacher=teacher_response,
                    category=course.category,
                    price=float(course.price),
                    rating=float(course.rating),
                    enrollment_count=course.enrollment_count,
                    schedule=course.schedule,
                    tags=tags,
                    status=course.status,
                    room_id=course.room_id,
                    room_name=room_obj.name,
                )
            )
            total_students += course.enrollment_count

        # Step 4: 聚合统计
        classroom_count = len(courses_data)
        teacher_count = len(teachers_map)

        # 获取城市名（通过 relationship）
        city_name = None
        if room_obj.city:
            city_name = room_obj.city.name

        return TrainingRoomDetailResponse(
            id=room_obj.id,
            name=room_obj.name,
            description=room_obj.description,
            cover_image=room_obj.cover_image,
            address=room_obj.address,
            business_hours=room_obj.business_hours,
            status=room_obj.status,
            room_type=room_obj.room_type,
            min_price=float(room_obj.min_price or 0),
            city_id=room_obj.city_id,
            city_name=city_name,
            rating=float(room_obj.rating or 0),
            classroom_count=classroom_count,
            class_capacity="8-12",
            teacher_count=teacher_count,
            total_students=total_students,
            teachers=list(teachers_map.values()),
            courses=courses_data,
        )
```

- [ ] **Step 2: Commit**

```bash
git add br-server/app/services/training_service.py
git commit -m "feat: add TrainingService.get_training_room_detail method"
```

---

### Task 4: 后端 API Routes（tasks.md 3.1-3.3）

**Files:**
- Create: `br-server/app/api/routes/training.py`
- Modify: `br-server/app/main.py`

**Interfaces:**
- Consumes: `TrainingService.get_training_room_detail(room_id: int)`
- Produces: `GET /api/v1/training/rooms/{room_id}` 路由

**Bug 防护：**
- **BUG-22（关键）**: 路由定义 `@router.get("/{room_id}")` 不使用尾部斜杠
- 404 处理：房间不存在或类型不是 training/comprehensive 时返回 HTTP 404

- [ ] **Step 1: 创建 training 路由文件**

创建 `br-server/app/api/routes/training.py`：

```python
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.course import TrainingRoomDetailResponse
from app.services.training_service import TrainingService

router = APIRouter(prefix="/api/v1/training/rooms", tags=["training"])


@router.get("/{room_id}", response_model=TrainingRoomDetailResponse)
async def get_training_room_detail(
    room_id: int,
    db: AsyncSession = Depends(get_db),
) -> TrainingRoomDetailResponse:
    service = TrainingService(db)
    result = await service.get_training_room_detail(room_id)
    if not result:
        raise HTTPException(
            status_code=404,
            detail="培训室不存在或不是培训室类型",
        )
    return result
```

- [ ] **Step 2: 在 main.py 中注册路由**

在 `br-server/app/main.py` 的 import 区域添加：

```python
from app.api.routes.training import router as training_router
```

在 `app.include_router(...)` 区域添加（在 `study_room_router` 附近）：

```python
app.include_router(training_router)
```

- [ ] **Step 3: 验证路由注册**

```bash
cd br-server && conda activate booking-room && python -c "from app.main import app; print([r.path for r in app.routes if 'training' in str(r.path)])"
```

Expected: 输出包含 `/api/v1/training/rooms/{room_id}`

- [ ] **Step 4: Commit**

```bash
git add br-server/app/api/routes/training.py br-server/app/main.py
git commit -m "feat: add GET /api/v1/training/rooms/{room_id} route"
```

---

### Task 5: 后端测试（tasks.md 4.1-4.8）

**Files:**
- Create: `br-server/tests/test_training_api.py`

**Interfaces:**
- Consumes: `client` fixture（来自 conftest.py，基于 in-memory SQLite + ASGITransport）
- Consumes: `StudyRoom`, `Teacher`, `Course` 模型

**Bug 防护：**
- BUG-16: 测试验证返回的是 Pydantic schema 数据，非 ORM 对象
- 教师去重测试：多门课程关联同一教师时 teachers 数组去重
- tags 解析测试：逗号分隔字符串正确解析为数组
- 无教师课程测试：teacher 字段为 null

- [ ] **Step 1: 创建测试文件，包含所有测试用例**

创建 `br-server/tests/test_training_api.py`：

```python
import pytest
from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


async def _seed_training_room(db_session, room_type="training"):
    """创建培训室 + 教师 + 课程的测试数据"""
    city = City(name="茂名市", province="广东省", sort_order=0, status="active")
    db_session.add(city)
    await db_session.flush()

    room = StudyRoom(
        name="去K书培训中心",
        description="专业培训环境",
        cover_image="https://example.com/cover.jpg",
        address="茂南区光谷大道88号3楼",
        city_id=city.id,
        business_hours="09:00 - 21:00",
        status="open",
        room_type=room_type,
        min_price=50,
        rating=4.8,
    )
    db_session.add(room)
    await db_session.flush()

    teacher1 = Teacher(name="李明华", avatar="https://example.com/t1.jpg",
                       title="考研政治 · 8年教龄", rating=4.9)
    teacher2 = Teacher(name="王晓雯", avatar="https://example.com/t2.jpg",
                       title="公考行测 · 6年教龄", rating=4.8)
    db_session.add_all([teacher1, teacher2])
    await db_session.flush()

    course1 = Course(
        room_id=room.id, teacher_id=teacher1.id, name="考研政治冲刺班",
        cover_image="https://example.com/c1.jpg", category="postgraduate",
        price=80, rating=4.9, enrollment_count=120,
        schedule="每周二 14:00", tags="热销,小班", status="active",
        is_hot=True, sort_order=1,
    )
    course2 = Course(
        room_id=room.id, teacher_id=teacher1.id, name="考研政治基础班",
        cover_image="https://example.com/c2.jpg", category="postgraduate",
        price=60, rating=4.7, enrollment_count=80,
        schedule="每周三 19:00", tags="基础", status="active",
        is_hot=False, sort_order=2,
    )
    course3 = Course(
        room_id=room.id, teacher_id=teacher2.id, name="公务员行测精讲",
        cover_image="https://example.com/c3.jpg", category="civil_service",
        price=60, rating=4.8, enrollment_count=95,
        schedule="每周三 19:00", tags="新课,行测", status="active",
        is_hot=True, sort_order=3,
    )
    course4 = Course(
        room_id=room.id, teacher_id=None, name="自习辅导",
        cover_image=None, category="skills",
        price=30, rating=4.5, enrollment_count=40,
        schedule="每日", tags=None, status="active",
        is_hot=False, sort_order=4,
    )
    db_session.add_all([course1, course2, course3, course4])
    await db_session.commit()
    return room, [teacher1, teacher2], [course1, course2, course3, course4]


@pytest.mark.asyncio
async def test_get_training_room_detail_success(client, db_session):
    """4.1 正常请求培训室详情：验证响应字段完整性"""
    room, teachers, courses = await _seed_training_room(db_session)

    resp = await client.get(f"/api/v1/training/rooms/{room.id}")
    assert resp.status_code == 200

    data = resp.json()
    # 房间基本信息
    assert data["id"] == room.id
    assert data["name"] == "去K书培训中心"
    assert data["room_type"] == "training"
    assert data["status"] == "open"
    assert data["address"] == "茂南区光谷大道88号3楼"
    assert data["rating"] == 4.8
    assert data["city_name"] == "茂名市"
    # 教室概况统计
    assert data["classroom_count"] == 4
    assert data["class_capacity"] == "8-12"
    assert data["teacher_count"] == 2  # teacher1 重复出现但去重
    assert data["total_students"] == 120 + 80 + 95 + 40
    # 名师团队
    assert len(data["teachers"]) == 2
    # 课程列表
    assert len(data["courses"]) == 4


@pytest.mark.asyncio
async def test_get_comprehensive_room_detail(client, db_session):
    """4.2 综合室详情请求：验证综合室返回与培训室相同的结构"""
    room, _, _ = await _seed_training_room(db_session, room_type="comprehensive")

    resp = await client.get(f"/api/v1/training/rooms/{room.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["room_type"] == "comprehensive"
    assert "classroom_count" in data
    assert "teachers" in data
    assert "courses" in data


@pytest.mark.asyncio
async def test_get_training_room_404_for_study_room(client, db_session):
    """4.3 请求自习室 room_id 返回 404"""
    room = StudyRoom(
        name="普通自习室", address="某处", status="open",
        room_type="study", min_price=8, rating=4.5,
    )
    db_session.add(room)
    await db_session.commit()

    resp = await client.get(f"/api/v1/training/rooms/{room.id}")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_get_training_room_404_for_nonexistent(client):
    """4.3 请求不存在的 room_id 返回 404"""
    resp = await client.get("/api/v1/training/rooms/99999")
    assert resp.status_code == 404


@pytest.mark.asyncio
async def test_teacher_deduplication(client, db_session):
    """4.4 教师去重：多门课程关联同一教师时 teachers 数组去重"""
    room, teachers, courses = await _seed_training_room(db_session)

    resp = await client.get(f"/api/v1/training/rooms/{room.id}")
    data = resp.json()
    teacher_ids = [t["id"] for t in data["teachers"]]
    assert len(teacher_ids) == len(set(teacher_ids))  # 无重复
    assert len(teacher_ids) == 2  # 只有 2 位教师


@pytest.mark.asyncio
async def test_empty_courses_scenario(client, db_session):
    """4.5 空课程场景：培训室无课程时 teachers 和 courses 数组为空"""
    city = City(name="北京市", province="北京市", sort_order=0, status="active")
    db_session.add(city)
    await db_session.flush()

    room = StudyRoom(
        name="空培训室", address="某处", status="open",
        room_type="training", min_price=50, rating=0, city_id=city.id,
    )
    db_session.add(room)
    await db_session.commit()

    resp = await client.get(f"/api/v1/training/rooms/{room.id}")
    assert resp.status_code == 200
    data = resp.json()
    assert data["classroom_count"] == 0
    assert data["teacher_count"] == 0
    assert data["total_students"] == 0
    assert data["teachers"] == []
    assert data["courses"] == []


@pytest.mark.asyncio
async def test_tags_parsing(client, db_session):
    """4.6 tags 解析：课程 tags 字段从逗号分隔字符串解析为数组"""
    room, _, courses = await _seed_training_room(db_session)

    resp = await client.get(f"/api/v1/training/rooms/{room.id}")
    data = resp.json()
    course1 = next(c for c in data["courses"] if c["name"] == "考研政治冲刺班")
    assert course1["tags"] == ["热销", "小班"]

    course4 = next(c for c in data["courses"] if c["name"] == "自习辅导")
    assert course4["tags"] == []  # tags=None → 空数组


@pytest.mark.asyncio
async def test_course_without_teacher(client, db_session):
    """4.7 无教师课程：课程未关联教师时 teacher 字段为 null"""
    room, _, courses = await _seed_training_room(db_session)

    resp = await client.get(f"/api/v1/training/rooms/{room.id}")
    data = resp.json()
    course4 = next(c for c in data["courses"] if c["name"] == "自习辅导")
    assert course4["teacher"] is None

    course1 = next(c for c in data["courses"] if c["name"] == "考研政治冲刺班")
    assert course1["teacher"] is not None
    assert course1["teacher"]["name"] == "李明华"
```

- [ ] **Step 2: 运行测试**

```bash
cd br-server && conda activate booking-room && pytest tests/test_training_api.py -v
```

Expected: 全部 7 个测试通过（对应 tasks.md 4.1-4.7）。如失败，检查迁移是否已执行、模型是否正确注册。

- [ ] **Step 3: Commit**

```bash
git add br-server/tests/test_training_api.py
git commit -m "test: add training room detail API tests"
```

---

### Task 6: 前端 API 模块（tasks.md 5.1）

**Files:**
- Create: `br-app/src/api/training.js`

**Interfaces:**
- Produces: `getTrainingRoomDetail(roomId)` → 调用 `GET /api/v1/training/rooms/{roomId}`

**Bug 防护：**
- **BUG-22（关键）**: URL 不使用尾部斜杠，路径为 `/api/v1/training/rooms/${roomId}`
- **BUG-13**: 使用详情接口而非列表接口获取数据

- [ ] **Step 1: 创建 training.js API 模块**

创建 `br-app/src/api/training.js`：

```javascript
import { get } from '@/utils/request'

/**
 * 获取培训室详情（含教室概况、名师团队、课程列表）
 * @param {number} roomId - 培训室ID
 */
export function getTrainingRoomDetail(roomId) {
  return get(`/api/v1/training/rooms/${roomId}`)
}
```

- [ ] **Step 2: Commit**

```bash
git add br-app/src/api/training.js
git commit -m "feat: add getTrainingRoomDetail API function"
```

---

### Task 7: 前端页面 data & loadData 重构（tasks.md 6.1-6.2）

**Files:**
- Modify: `br-app/src/pages/booking/detail.vue`

**Interfaces:**
- Consumes: `fetchBookingRoom(roomId)` → 获取房间基本信息（含 room_type）
- Consumes: `getSeatStats(roomId)` → 获取座位统计（study/comprehensive）
- Consumes: `getTrainingRoomDetail(roomId)` → 获取培训室详情（training/comprehensive）

**Bug 防护：**
- **BUG-14**: 不涉及 `<script setup>`，当前 detail.vue 使用 Options API + `onLoad` 钩子，无 onMounted 导入问题
- **BUG-13**: 使用详情接口获取房间信息，不使用列表接口

- [ ] **Step 1: 修改 data()，新增 trainingData 和 roomType**

在 `detail.vue` 的 `<script>` 部分，修改 `data()` 返回对象，在现有字段后添加：

```javascript
data() {
  return {
    statusBarHeight: 0,
    roomId: null,
    room: {},
    seatStatsData: null,
    trainingData: null,    // 新增：培训室详情数据
    roomType: '',          // 新增：房间类型 study/training/comprehensive
    loading: true,
    isFav: false,
    reviewCount: 0,
  }
},
```

- [ ] **Step 2: 添加 import 语句**

在 `<script>` 顶部的 import 区域添加：

```javascript
import { getTrainingRoomDetail } from '@/api/training'
```

完整 import 区域应为：

```javascript
import { getSeatStats } from '@/api/seats'
import { getTrainingRoomDetail } from '@/api/training'
import { followRoom, isRoomFollowed, unfollowRoom } from '@/services/followedRooms'
import { fetchBookingRoom } from '@/services/bookingPageService'
```

- [ ] **Step 3: 重构 loadData() 方法**

将现有 `loadData()` 方法替换为条件加载逻辑：

```javascript
async loadData() {
  this.loading = true
  try {
    // Step 1: 获取房间基本信息（含 room_type）
    await this.loadRoom()
    if (!this.room || !this.room.id) return

    this.roomType = this.room.room_type || 'study'

    // Step 2: 根据 room_type 条件调用后续 API
    const tasks = []
    if (this.roomType === 'study' || this.roomType === 'comprehensive') {
      tasks.push(this.loadSeatStats())
    }
    if (this.roomType === 'training' || this.roomType === 'comprehensive') {
      tasks.push(this.loadTrainingDetail())
    }
    await Promise.all(tasks)
  } finally {
    this.loading = false
  }
},

async loadTrainingDetail() {
  try {
    const data = await getTrainingRoomDetail(this.roomId)
    this.trainingData = data || null
  } catch {
    this.trainingData = null
  }
},
```

- [ ] **Step 4: Commit**

```bash
git add br-app/src/pages/booking/detail.vue
git commit -m "feat: add roomType conditional API loading in detail.vue"
```

---

### Task 8: 前端页面 computed 属性（tasks.md 6.3）

**Files:**
- Modify: `br-app/src/pages/booking/detail.vue`

**Interfaces:**
- Produces: `isStudyRoom`, `isTrainingRoom`, `isComprehensiveRoom` (boolean)
- Produces: `trainingStats` (object: classroom_count, class_capacity, teacher_count, total_students)
- Produces: `teachers` (array)
- Produces: `trainingCourses` (array)

- [ ] **Step 1: 在 computed 对象中新增计算属性**

在 `computed: { ... }` 对象中，在现有 `seatStats` 之后添加：

```javascript
isStudyRoom() {
  return this.roomType === 'study'
},
isTrainingRoom() {
  return this.roomType === 'training'
},
isComprehensiveRoom() {
  return this.roomType === 'comprehensive'
},
trainingStats() {
  if (!this.trainingData) return null
  return {
    classroom_count: this.trainingData.classroom_count || 0,
    class_capacity: this.trainingData.class_capacity || '8-12',
    teacher_count: this.trainingData.teacher_count || 0,
    total_students: this.trainingData.total_students || 0,
  }
},
teachers() {
  return this.trainingData?.teachers || []
},
trainingCourses() {
  return this.trainingData?.courses || []
},
```

- [ ] **Step 2: Commit**

```bash
git add br-app/src/pages/booking/detail.vue
git commit -m "feat: add computed properties for training room rendering"
```

---

### Task 9: 前端页面模板条件渲染（tasks.md 6.4-6.8, 6.10, 6.12）

**Files:**
- Modify: `br-app/src/pages/booking/detail.vue`（template 区域）

**Bug 防护：**
- **BUG-20（关键）**: 模板中不使用 `&lt;` `&gt;` HTML 实体，如需箭头字符用 Unicode `‹` `›`
- 空状态：培训室无课程时显示"暂无课程"
- 参考 prototype/training-room.html 的 UI 结构

- [ ] **Step 1: 在座位概况 section 之前添加培训室简介**

在 `<view class="info-card ...">` 结束后、`<view class="section animate-in" ...>环境照片</view>` 之前插入：

```html
<!-- 培训室简介（仅 training/comprehensive） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section intro-section animate-in" style="animation-delay: 0.05s;">
  <view class="section-header">
    <view class="section-bar" />
    <text class="section-title">培训室简介</text>
  </view>
  <text class="intro-text">{{ room.description || '暂无简介' }}</text>
</view>
```

- [ ] **Step 2: 将座位概况 section 包裹在条件渲染中**

将现有座位概况 `<view class="section seat-section animate-in" ...>` 修改为：

```html
<!-- 座位概况（仅 study/comprehensive） -->
<view v-if="isStudyRoom || isComprehensiveRoom" class="section seat-section animate-in" style="animation-delay: 0.2s;">
  <!-- 原有座位概况内容保持不变 -->
  ...
</view>
```

- [ ] **Step 3: 在座位概况之后添加教室概况 section**

在座位概况 section 之后添加（仅 training/comprehensive 显示）：

```html
<!-- 教室概况（仅 training/comprehensive） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section classroom-section animate-in" style="animation-delay: 0.2s;">
  <view class="section-header">
    <view class="section-bar" />
    <text class="section-title">教室概况</text>
  </view>
  <view class="stats-grid">
    <view class="stat-card">
      <view class="stat-icon stat-classroom">
        <view class="door-icon" />
      </view>
      <view class="stat-body">
        <text class="stat-count">{{ trainingStats?.classroom_count || 0 }}</text>
        <text class="stat-label">培训教室</text>
      </view>
    </view>
    <view class="stat-card">
      <view class="stat-icon stat-capacity">
        <view class="group-icon" />
      </view>
      <view class="stat-body">
        <text class="stat-count">{{ trainingStats?.class_capacity || '8-12' }}</text>
        <text class="stat-label">小班容量</text>
      </view>
    </view>
    <view class="stat-card">
      <view class="stat-icon stat-teacher">
        <view class="board-icon" />
      </view>
      <view class="stat-body">
        <text class="stat-count">{{ trainingStats?.teacher_count || 0 }}</text>
        <text class="stat-label">认证讲师</text>
      </view>
    </view>
    <view class="stat-card">
      <view class="stat-icon stat-students">
        <view class="cap-icon" />
      </view>
      <view class="stat-body">
        <text class="stat-count">{{ trainingStats?.total_students || 0 }}</text>
        <text class="stat-label">累计学员</text>
      </view>
    </view>
  </view>
</view>
```

- [ ] **Step 4: 添加名师团队 section**

在教室概况之后添加：

```html
<!-- 名师团队（仅 training/comprehensive） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section animate-in" style="animation-delay: 0.3s;">
  <view class="section-header">
    <view class="section-bar" />
    <text class="section-title">名师团队</text>
  </view>
  <view v-if="teachers.length === 0" class="empty-state">
    <text class="empty-text">暂无讲师</text>
  </view>
  <scroll-view v-else scroll-x :show-scrollbar="false" class="teacher-scroll">
    <view class="teacher-list">
      <view v-for="teacher in teachers" :key="teacher.id" class="teacher-card">
        <image class="teacher-avatar" :src="teacher.avatar || ''" mode="aspectFill" />
        <text class="teacher-name">{{ teacher.name }}</text>
        <text class="teacher-title">{{ teacher.title || '' }}</text>
        <view class="teacher-rating">
          <text class="star">★</text>
          <text class="rating-text">{{ teacher.rating }}</text>
        </view>
      </view>
    </view>
  </scroll-view>
</view>
```

- [ ] **Step 5: 添加本培训室课程 section**

在名师团队之后添加：

```html
<!-- 本培训室课程（仅 training/comprehensive） -->
<view v-if="isTrainingRoom || isComprehensiveRoom" class="section animate-in" style="animation-delay: 0.4s;">
  <view class="section-header">
    <view class="section-bar" />
    <text class="section-title">本培训室课程</text>
    <text class="section-sub">共{{ trainingCourses.length }}门</text>
  </view>
  <view v-if="trainingCourses.length === 0" class="empty-state">
    <text class="empty-text">暂无课程</text>
  </view>
  <view v-else class="course-list">
    <view v-for="course in trainingCourses" :key="course.id" class="course-card" @tap="onCourseDetail(course)">
      <image class="course-cover" :src="course.cover_image || ''" mode="aspectFill" />
      <view class="course-body">
        <view class="course-top">
          <text class="course-name">{{ course.name }}</text>
          <view v-if="course.is_hot" class="course-tag tag-hot">
            <text class="tag-text">热销</text>
          </view>
        </view>
        <view v-if="course.teacher" class="course-teacher">
          <text class="teacher-name-sm">{{ course.teacher.name }}</text>
        </view>
        <view class="course-schedule">
          <text class="schedule-text">{{ course.schedule || '排课待定' }}</text>
        </view>
        <view class="course-bottom">
          <text class="course-price">¥{{ course.price }}</text>
          <text class="price-unit">/课时</text>
          <view class="book-pill">
            <text class="book-pill-text">预约</text>
          </view>
        </view>
      </view>
    </view>
  </view>
</view>
```

- [ ] **Step 6: Commit**

```bash
git add br-app/src/pages/booking/detail.vue
git commit -m "feat: add training room conditional template sections"
```

---

### Task 10: 底部操作栏条件渲染 & 新增方法（tasks.md 6.9, 6.11）

**Files:**
- Modify: `br-app/src/pages/booking/detail.vue`

**Bug 防护：**
- 综合室底部按钮跳转到座位选择页，不是课程列表

- [ ] **Step 1: 修改底部操作栏为条件渲染**

将现有 `<view class="bottom-bar">` 内容替换为：

```html
<view class="bottom-bar">
  <!-- 心状关注按钮（所有类型通用） -->
  <view class="fav-btn" @tap="onToggleFav">
    <text :class="['heart-icon', { active: isFav }]">♥</text>
  </view>

  <!-- 自习室：立即预约 -->
  <view v-if="isStudyRoom" class="book-btn" @tap="onBook">
    <text class="book-btn-sub">{{ seatStats.available }} 个座位可选</text>
    <text class="book-btn-text">立即预约</text>
  </view>

  <!-- 培训室：返回课程 -->
  <view v-else-if="isTrainingRoom" class="back-btn" @tap="onBackToCourses">
    <text class="back-btn-text">返回课程</text>
  </view>

  <!-- 综合室：预约自习室 -->
  <view v-else-if="isComprehensiveRoom" class="book-btn" @tap="onBookStudy">
    <text class="book-btn-sub">{{ seatStats.available }} 个座位可选</text>
    <text class="book-btn-text">预约自习室</text>
  </view>
</view>
```

- [ ] **Step 2: 在 methods 中新增方法**

在 `methods: { ... }` 对象中添加（在 `onBook` 方法之后）：

```javascript
onBackToCourses() {
  uni.navigateTo({ url: '/pages/training/index' })
},

onBookStudy() {
  uni.navigateTo({ url: '/pages/booking/seat-select?room_id=' + this.roomId })
},

onCourseDetail(course) {
  if (course && course.id) {
    uni.navigateTo({ url: '/pages/training/course-detail?id=' + course.id })
  }
},
```

- [ ] **Step 3: Commit**

```bash
git add br-app/src/pages/booking/detail.vue
git commit -m "feat: add conditional bottom bar and navigation methods"
```

---

### Task 11: 前端 SCSS 样式（tasks.md 6.13）

**Files:**
- Modify: `br-app/src/pages/booking/detail.vue`（`<style lang="scss" scoped>` 区域）

**Bug 防护：**
- 不使用 `@import '@/uni.scss'`（参考 bug-fixed.md BUG-1，uni-app 自动注入）
- 使用 rpx 单位、SCSS 变量、与现有 detail.vue 风格一致（rounded-2xl shadow-sm 对应 32rpx 圆角 + $shadow-card）

- [ ] **Step 1: 在 `<style>` 末尾添加培训室相关样式**

在现有样式之后（`@keyframes loadingPulse` 之前）添加：

```scss
/* === 培训室简介 === */
.intro-section {
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.intro-text {
  font-size: 26rpx;
  line-height: 1.6;
  color: $text-secondary;
}

/* === 教室概况 === */
.classroom-section {
  background: $surface;
  border-radius: 32rpx;
  padding: 28rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.section-bar {
  width: 6rpx;
  height: 28rpx;
  border-radius: 6rpx;
  background: $primary;
  margin-right: 12rpx;
}

.stat-classroom {
  background: rgba(79, 110, 247, 0.1);
}

.stat-capacity {
  background: rgba(7, 193, 96, 0.11);
}

.stat-teacher {
  background: rgba(255, 149, 0, 0.13);
}

.stat-students {
  background: rgba(168, 85, 247, 0.12);
}

.door-icon {
  width: 30rpx;
  height: 36rpx;
  border: 4rpx solid $primary;
  border-radius: 8rpx 8rpx 0 0;
}

.group-icon {
  width: 34rpx;
  height: 18rpx;
  border: 3rpx solid $success;
  border-radius: 10rpx;
  position: relative;
}

.group-icon::before,
.group-icon::after {
  content: '';
  position: absolute;
  bottom: -10rpx;
  width: 4rpx;
  height: 10rpx;
  background: $success;
}

.group-icon::before { left: 4rpx; }
.group-icon::after { right: 4rpx; }

.board-icon {
  width: 30rpx;
  height: 22rpx;
  border: 4rpx solid #e67900;
  border-radius: 4rpx;
}

.cap-icon {
  width: 32rpx;
  height: 32rpx;
  border-radius: 50% 50% 50% 0;
  border: 4rpx solid #a855f7;
  transform: rotate(-45deg);
}

/* === 名师团队 === */
.teacher-scroll {
  white-space: nowrap;
}

.teacher-list {
  display: inline-flex;
  gap: 18rpx;
  padding-bottom: 4rpx;
}

.teacher-card {
  width: 200rpx;
  background: $surface;
  border-radius: 24rpx;
  padding: 24rpx 16rpx;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
  display: flex;
  flex-direction: column;
  align-items: center;
  flex-shrink: 0;
}

.teacher-avatar {
  width: 96rpx;
  height: 96rpx;
  border-radius: 50%;
  margin-bottom: 12rpx;
}

.teacher-name {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
}

.teacher-title {
  font-size: 20rpx;
  color: $text-muted;
  margin-top: 4rpx;
  text-align: center;
}

.teacher-rating {
  display: flex;
  align-items: center;
  gap: 4rpx;
  margin-top: 8rpx;
}

.star {
  font-size: 20rpx;
  color: #ffc107;
}

.rating-text {
  font-size: 22rpx;
  font-weight: 500;
  color: $text-primary;
}

/* === 课程列表 === */
.course-list {
  display: flex;
  flex-direction: column;
  gap: 18rpx;
}

.course-card {
  display: flex;
  background: $surface;
  border-radius: 24rpx;
  overflow: hidden;
  box-shadow: $shadow-card;
  border: 1rpx solid $border-soft;
}

.course-cover {
  width: 180rpx;
  height: 180rpx;
  flex-shrink: 0;
}

.course-body {
  flex: 1;
  padding: 18rpx;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  min-width: 0;
}

.course-top {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 8rpx;
}

.course-name {
  font-size: 26rpx;
  font-weight: 600;
  color: $text-primary;
  line-height: 1.3;
  flex: 1;
}

.course-tag {
  padding: 4rpx 12rpx;
  border-radius: 999rpx;
  flex-shrink: 0;
}

.tag-hot {
  background: rgba(255, 107, 107, 0.12);
}

.tag-hot .tag-text {
  color: $danger;
  font-size: 20rpx;
}

.course-teacher {
  margin-top: 8rpx;
}

.teacher-name-sm {
  font-size: 22rpx;
  color: $text-secondary;
}

.course-schedule {
  margin-top: 6rpx;
}

.schedule-text {
  font-size: 22rpx;
  color: $text-muted;
}

.course-bottom {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-top: 8rpx;
}

.course-price {
  font-size: 28rpx;
  font-weight: 700;
  color: $primary;
}

.price-unit {
  font-size: 20rpx;
  color: $text-muted;
}

.book-pill {
  padding: 6rpx 20rpx;
  border-radius: 999rpx;
  background: $primary-soft;
}

.book-pill-text {
  font-size: 22rpx;
  font-weight: 500;
  color: $primary;
}

/* === 空状态 === */
.empty-state {
  padding: 40rpx 0;
  text-align: center;
}

.empty-text {
  font-size: 26rpx;
  color: $text-muted;
}

/* === 返回课程按钮 === */
.back-btn {
  flex: 1;
  height: 92rpx;
  border-radius: 44rpx;
  border: 2rpx solid $border-color;
  background: $white;
  display: flex;
  align-items: center;
  justify-content: center;
  box-shadow: $shadow-card;
}

.back-btn:active {
  background: $surface-soft;
  transform: translateY(1rpx);
}

.back-btn-text {
  font-size: 30rpx;
  font-weight: 600;
  color: $text-secondary;
}
```

- [ ] **Step 2: Commit**

```bash
git add br-app/src/pages/booking/detail.vue
git commit -m "style: add training room SCSS styles"
```

---

### Task 12: 代码审查与重构（tasks.md 7.1-7.4）

**Files:**
- 检查所有新建和修改的文件

- [ ] **Step 1: 验证 Clean Architecture 分层**

确认：
- `br-server/app/api/routes/training.py` — 仅处理 HTTP 请求/响应，不含业务逻辑
- `br-server/app/services/training_service.py` — 处理业务逻辑（查询、聚合、组装）
- `br-server/app/models/teacher.py` / `course.py` — 仅定义数据模型
- `br-server/app/schemas/course.py` / `teacher.py` — 仅定义响应 schema

- [ ] **Step 2: 确认无重复定义**

确认 `TeacherResponse` 只在 `br-server/app/schemas/teacher.py` 定义，`CourseResponse` 只在 `br-server/app/schemas/course.py` 定义，其他文件通过 import 引用。

- [ ] **Step 3: 确认前端分层**

确认 `detail.vue` 调用 `@/api/training.js`，`training.js` 调用 `@/utils/request.js`。

- [ ] **Step 4: 检查所有新路由无尾部斜杠**

```bash
grep -r 'router\.get\|router\.post' br-server/app/api/routes/training.py
```

Expected: 所有路由路径不含尾部斜杠（如 `/{room_id}` 而非 `/{room_id}/`）。

---

### Task 13: API 文档更新（tasks.md 8.1）

**Files:**
- Modify: `docs/api.md`

- [ ] **Step 1: 在 api.md 中补充培训室详情接口文档**

在 `docs/api.md` 适当位置添加：

```markdown
## 培训室详情

### GET /api/v1/training/rooms/{room_id}

获取培训室（或综合室）的详细信息，包含教室概况统计、名师团队、课程列表。

**路径参数：**

| 参数 | 类型 | 必填 | 说明 |
|------|------|------|------|
| room_id | int | 是 | 培训室ID |

**响应示例：**

```json
{
  "id": 1,
  "name": "去K书培训中心",
  "description": "专业培训环境",
  "cover_image": "https://example.com/cover.jpg",
  "address": "茂南区光谷大道88号3楼",
  "business_hours": "09:00 - 21:00",
  "status": "open",
  "room_type": "training",
  "min_price": 50.0,
  "city_id": 1,
  "city_name": "茂名市",
  "rating": 4.8,
  "classroom_count": 4,
  "class_capacity": "8-12",
  "teacher_count": 2,
  "total_students": 335,
  "teachers": [
    {
      "id": 1,
      "name": "李明华",
      "avatar": "https://example.com/t1.jpg",
      "title": "考研政治 · 8年教龄",
      "rating": 4.9
    }
  ],
  "courses": [
    {
      "id": 1,
      "name": "考研政治冲刺班",
      "cover_image": "https://example.com/c1.jpg",
      "teacher": { "id": 1, "name": "李明华", ... },
      "category": "postgraduate",
      "price": 80.0,
      "rating": 4.9,
      "enrollment_count": 120,
      "schedule": "每周二 14:00",
      "tags": ["热销", "小班"],
      "status": "active",
      "room_id": 1,
      "room_name": "去K书培训中心"
    }
  ]
}
```

**错误响应：**

| 状态码 | 说明 |
|--------|------|
| 404 | 培训室不存在或不是培训室类型（room_type 非 training/comprehensive） |
```

- [ ] **Step 2: Commit**

```bash
git add docs/api.md
git commit -m "docs: add training room detail API documentation"
```

---

### Task 14: 最终验证（tasks.md 9.1-9.3）

- [ ] **Step 1: 运行后端全部测试**

```bash
cd br-server && conda activate booking-room && pytest tests/ -q
```

Expected: 全部测试通过，无失败。如 training-course-list 的测试存在，确保不受影响。

- [ ] **Step 2: 前端构建验证**

```bash
nvm use v22.22.0 && cd br-app && npm run build
```

Expected: 构建成功，无编译错误。特别注意无 SCSS @import 警告（BUG-1）、无 HTML 实体编译错误（BUG-20）。

- [ ] **Step 3: 验证现有自习室预约功能不受影响**

人工验证：
1. 打开自习室详情页（room_type=study），确认座位概况、底部"立即预约"按钮行为与修改前完全一致
2. 打开培训室详情页（room_type=training），确认显示教室概况、名师团队、课程列表，底部显示"返回课程"按钮
3. 打开综合室详情页（room_type=comprehensive），确认同时显示座位概况和培训相关区块，底部显示"预约自习室"按钮

- [ ] **Step 4: 最终 Commit**

```bash
git add -A
git commit -m "chore: training-room-overview final verification"
```
