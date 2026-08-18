"""Admin course management service."""

import json
from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.schemas.admin_course import (
    AdminCourseCreate,
    AdminCourseDetailResponse,
    AdminCourseItem,
    AdminCourseListResponse,
    AdminCourseUpdate,
    AdminLessonItem,
    AdminTeacherBrief,
    CourseScheduleCreate,
    CourseScheduleItem,
    CourseScheduleResponse,
    CourseScheduleUpdate,
)

MAX_PAGE_SIZE = 50
DEFAULT_PAGE_SIZE = 10


class AdminCourseService:
    """Admin 课程管理服务。"""

    async def list_courses(
        self,
        db: AsyncSession,
        page: int = 1,
        page_size: int = DEFAULT_PAGE_SIZE,
        category: str | None = None,
        status: str | None = None,
        keyword: str | None = None,
        teacher_id: int | None = None,
    ) -> AdminCourseListResponse:
        """分页查询课程列表，附带排课信息。"""
        page_size = min(page_size, MAX_PAGE_SIZE)
        offset = (page - 1) * page_size

        filters = []
        if category:
            filters.append(Course.category == category)
        if status:
            filters.append(Course.status == status)
        if keyword:
            filters.append(Course.name.ilike(f"%{keyword}%"))

        # 统计总数
        count_query = select(func.count()).select_from(Course)
        if filters:
            count_query = count_query.where(*filters)
        count_result = await db.execute(count_query)
        total = count_result.scalar_one()

        # 分页查询
        query = (
            select(Course, StudyRoom.name.label("room_name"))
            .outerjoin(StudyRoom, Course.room_id == StudyRoom.id)
        )
        if filters:
            query = query.where(*filters)
        query = query.order_by(Course.sort_order.asc(), Course.id.asc()).offset(offset).limit(page_size)

        result = await db.execute(query)
        rows = result.all()

        items = []
        for course, room_name in rows:
            # 查询该课程的排课记录
            schedules_result = await db.execute(
                select(CourseSchedule)
                .where(CourseSchedule.course_id == course.id)
                .order_by(CourseSchedule.created_at)
            )
            schedules = list(schedules_result.scalars().all())

            schedule_items = [
                CourseScheduleItem(
                    id=s.id,
                    teacher_id=s.teacher_id,
                    start_date=str(s.start_date) if s.start_date else None,
                    time_slots=s.time_slots,
                    price=Decimal(str(s.price)),
                    custom_price=Decimal(str(s.custom_price)),
                    full_package_price=Decimal(str(s.full_package_price)) if s.full_package_price else None,
                    full_custom_price=Decimal(str(s.full_custom_price)) if s.full_custom_price else None,
                )
                for s in schedules
            ]

            tags = course.tags.split(",") if course.tags else []
            item = AdminCourseItem(
                id=course.id,
                name=course.name,
                cover_image=course.cover_image,
                category=course.category,
                rating=course.rating,
                enrollment_count=course.enrollment_count,
                tags=tags,
                status=course.status,
                is_hot=course.is_hot,
                sort_order=course.sort_order,
                room_id=course.room_id,
                room_name=room_name,
                schedules=schedule_items,
                created_at=course.created_at.isoformat() if isinstance(course.created_at, datetime) else str(course.created_at),
                updated_at=course.updated_at.isoformat() if isinstance(course.updated_at, datetime) else str(course.updated_at),
            )
            items.append(item)

        return AdminCourseListResponse(
            items=items, total=total, page=page, page_size=page_size
        )

    async def get_course_detail(self, db: AsyncSession, course_id: int) -> AdminCourseDetailResponse | None:
        """获取课程详情，包含所有排课记录和教师信息。"""
        course_result = await db.execute(select(Course).where(Course.id == course_id))
        course = course_result.scalar_one_or_none()
        if not course:
            return None

        # 查询排课记录
        schedules_result = await db.execute(
            select(CourseSchedule)
            .where(CourseSchedule.course_id == course_id)
            .order_by(CourseSchedule.created_at)
        )
        schedules = list(schedules_result.scalars().all())

        schedule_items = [
            CourseScheduleItem(
                id=s.id,
                teacher_id=s.teacher_id,
                start_date=str(s.start_date) if s.start_date else None,
                time_slots=s.time_slots,
                price=Decimal(str(s.price)),
                custom_price=Decimal(str(s.custom_price)),
                full_package_price=Decimal(str(s.full_package_price)) if s.full_package_price else None,
                full_custom_price=Decimal(str(s.full_custom_price)) if s.full_custom_price else None,
            )
            for s in schedules
        ]

        # 查询教师信息（取第一条排课的教师）
        teacher_brief = None
        if schedules and schedules[0].teacher_id:
            teacher_result = await db.execute(
                select(Teacher).where(Teacher.id == schedules[0].teacher_id)
            )
            teacher = teacher_result.scalar_one_or_none()
            if teacher:
                teacher_brief = AdminTeacherBrief(
                    id=teacher.id,
                    name=teacher.name,
                    avatar=teacher.avatar,
                    title=teacher.title,
                )

        # 查询教室名称
        room_result = await db.execute(select(StudyRoom.name).where(StudyRoom.id == course.room_id))
        room_name = room_result.scalar_one_or_none()

        tags = course.tags.split(",") if course.tags else []

        # 查询课时列表
        lessons_result = await db.execute(
            select(CourseLesson)
            .where(CourseLesson.course_id == course_id)
            .order_by(CourseLesson.sort_order.asc())
        )
        lessons = [AdminLessonItem.model_validate(l) for l in lessons_result.scalars().all()]

        return AdminCourseDetailResponse(
            id=course.id,
            name=course.name,
            cover_image=course.cover_image,
            category=course.category,
            rating=course.rating,
            enrollment_count=course.enrollment_count,
            tags=tags,
            status=course.status,
            is_hot=course.is_hot,
            sort_order=course.sort_order,
            room_id=course.room_id,
            room_name=room_name,
            schedules=schedule_items,
            created_at=course.created_at.isoformat() if isinstance(course.created_at, datetime) else str(course.created_at),
            updated_at=course.updated_at.isoformat() if isinstance(course.updated_at, datetime) else str(course.updated_at),
            teacher=teacher_brief,
            description=course.description,
            lessons=lessons,
        )

    async def create_course(self, db: AsyncSession, data: AdminCourseCreate) -> Course:
        """创建新课程及其排课记录。"""
        course = Course(
            name=data.name,
            cover_image=data.cover_image,
            category=data.category,
            room_id=data.room_id,
            tags=data.tags,
            description=data.description,
            is_hot=data.is_hot,
            sort_order=data.sort_order,
            status=data.status,
        )
        db.add(course)
        await db.flush()

        # 创建排课记录
        for sched_data in data.schedules:
            schedule = CourseSchedule(
                course_id=course.id,
                teacher_id=sched_data.teacher_id,
                start_date=date.fromisoformat(sched_data.start_date) if sched_data.start_date else None,
                time_slots=sched_data.time_slots,
                price=float(sched_data.price),
                custom_price=float(sched_data.custom_price),
                full_package_price=float(sched_data.full_package_price) if sched_data.full_package_price else None,
                full_custom_price=float(sched_data.full_custom_price) if sched_data.full_custom_price else None,
            )
            db.add(schedule)

        await db.flush()
        return course

    async def update_course(
        self, db: AsyncSession, course_id: int, data: AdminCourseUpdate
    ) -> Course | None:
        """更新课程信息及排课记录。"""
        course_result = await db.execute(select(Course).where(Course.id == course_id))
        course = course_result.scalar_one_or_none()
        if not course:
            return None

        # 更新课程基本信息
        if data.name is not None:
            course.name = data.name
        if data.cover_image is not None:
            course.cover_image = data.cover_image
        if data.category is not None:
            course.category = data.category
        if data.room_id is not None:
            course.room_id = data.room_id
        if data.tags is not None:
            course.tags = data.tags
        if data.description is not None:
            course.description = data.description
        if data.is_hot is not None:
            course.is_hot = data.is_hot
        if data.sort_order is not None:
            course.sort_order = data.sort_order
        if data.status is not None:
            course.status = data.status

        # 更新排课记录
        if data.schedules is not None:
            # 删除旧排课
            await db.execute(
                select(CourseSchedule).where(CourseSchedule.course_id == course_id)
            )
            existing_schedules_result = await db.execute(
                select(CourseSchedule).where(CourseSchedule.course_id == course_id)
            )
            existing_schedules = list(existing_schedules_result.scalars().all())
            for s in existing_schedules:
                await db.delete(s)

            # 创建新排课
            for sched_data in data.schedules:
                schedule = CourseSchedule(
                    course_id=course_id,
                    teacher_id=sched_data.teacher_id,
                    start_date=date.fromisoformat(sched_data.start_date) if sched_data.start_date else None,
                    time_slots=sched_data.time_slots,
                    price=float(sched_data.price),
                    custom_price=float(sched_data.custom_price),
                    full_package_price=float(sched_data.full_package_price) if sched_data.full_package_price else None,
                    full_custom_price=float(sched_data.full_custom_price) if sched_data.full_custom_price else None,
                )
                db.add(schedule)

        await db.flush()
        return course

    async def delete_course(self, db: AsyncSession, course_id: int) -> bool:
        """删除课程及其排课记录（级联删除）。"""
        course_result = await db.execute(select(Course).where(Course.id == course_id))
        course = course_result.scalar_one_or_none()
        if not course:
            return False
        await db.delete(course)
        await db.flush()
        return True

    async def toggle_course_status(self, db: AsyncSession, course_id: int, status: str) -> Course | None:
        """切换课程状态。"""
        course_result = await db.execute(select(Course).where(Course.id == course_id))
        course = course_result.scalar_one_or_none()
        if not course:
            return None
        course.status = status
        await db.flush()
        return course

    # ── 课时 CRUD ──────────────────────────────────────────────

    async def list_lessons(self, db: AsyncSession, course_id: int) -> list[AdminLessonItem]:
        """查询课程的课时列表。"""
        result = await db.execute(
            select(CourseLesson)
            .where(CourseLesson.course_id == course_id)
            .order_by(CourseLesson.sort_order.asc())
        )
        return [AdminLessonItem.model_validate(l) for l in result.scalars().all()]

    async def create_lesson(
        self, db: AsyncSession, course_id: int, data: "AdminLessonCreate"
    ) -> AdminLessonItem:
        """创建课时。"""
        from app.schemas.admin_course import AdminLessonCreate  # noqa: F811

        # 自动设置 sort_order
        if data.sort_order == 0:
            max_result = await db.execute(
                select(func.coalesce(func.max(CourseLesson.sort_order), 0))
                .where(CourseLesson.course_id == course_id)
            )
            auto_order = (max_result.scalar() or 0) + 1
        else:
            auto_order = data.sort_order

        lesson = CourseLesson(
            course_id=course_id,
            title=data.title,
            description=data.description,
            duration_minutes=data.duration_minutes,
            sort_order=auto_order,
            is_free_preview=data.is_free_preview,
        )
        db.add(lesson)
        await db.flush()
        return AdminLessonItem.model_validate(lesson)

    async def update_lesson(
        self, db: AsyncSession, lesson_id: int, data: "AdminLessonUpdate"
    ) -> AdminLessonItem | None:
        """更新课时。"""
        result = await db.execute(
            select(CourseLesson).where(CourseLesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()
        if not lesson:
            return None

        if data.title is not None:
            lesson.title = data.title
        if data.description is not None:
            lesson.description = data.description
        if data.duration_minutes is not None:
            lesson.duration_minutes = data.duration_minutes
        if data.sort_order is not None:
            lesson.sort_order = data.sort_order
        if data.is_free_preview is not None:
            lesson.is_free_preview = data.is_free_preview

        await db.flush()
        return AdminLessonItem.model_validate(lesson)

    async def delete_lesson(self, db: AsyncSession, lesson_id: int) -> bool:
        """删除课时。"""
        result = await db.execute(
            select(CourseLesson).where(CourseLesson.id == lesson_id)
        )
        lesson = result.scalar_one_or_none()
        if not lesson:
            return False
        await db.delete(lesson)
        await db.flush()
        return True

    # ── 排课 CRUD ──────────────────────────────────────────────────

    async def list_schedules(
        self, db: AsyncSession, course_id: int
    ) -> list[CourseScheduleResponse]:
        """查询课程的所有排课记录。"""
        result = await db.execute(
            select(CourseSchedule)
            .where(CourseSchedule.course_id == course_id)
            .order_by(CourseSchedule.created_at)
        )
        schedules = list(result.scalars().all())
        return [
            CourseScheduleResponse(
                id=s.id,
                course_id=s.course_id,
                teacher_id=s.teacher_id,
                start_date=str(s.start_date) if s.start_date else None,
                time_slots=s.time_slots,
                price=float(s.price),
                custom_price=float(s.custom_price),
                full_package_price=float(s.full_package_price) if s.full_package_price else None,
                full_custom_price=float(s.full_custom_price) if s.full_custom_price else None,
            )
            for s in schedules
        ]

    async def create_schedule(
        self, db: AsyncSession, course_id: int, data: CourseScheduleCreate
    ) -> CourseScheduleResponse:
        """新增排课记录。"""
        # 确认课程存在
        course_result = await db.execute(select(Course).where(Course.id == course_id))
        if not course_result.scalar_one_or_none():
            raise ValueError("课程不存在")

        schedule = CourseSchedule(
            course_id=course_id,
            teacher_id=data.teacher_id,
            start_date=date.fromisoformat(data.start_date) if data.start_date else None,
            time_slots=data.time_slots,
            price=data.price,
            custom_price=data.custom_price,
            full_package_price=data.full_package_price,
            full_custom_price=data.full_custom_price,
        )
        db.add(schedule)
        await db.flush()
        return CourseScheduleResponse(
            id=schedule.id,
            course_id=schedule.course_id,
            teacher_id=schedule.teacher_id,
            start_date=str(schedule.start_date) if schedule.start_date else None,
            time_slots=schedule.time_slots,
            price=float(schedule.price),
            custom_price=float(schedule.custom_price),
            full_package_price=float(schedule.full_package_price) if schedule.full_package_price else None,
            full_custom_price=float(schedule.full_custom_price) if schedule.full_custom_price else None,
        )

    async def update_schedule(
        self, db: AsyncSession, schedule_id: int, data: CourseScheduleUpdate
    ) -> CourseScheduleResponse | None:
        """更新排课记录。"""
        result = await db.execute(
            select(CourseSchedule).where(CourseSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            return None

        if data.teacher_id is not None:
            schedule.teacher_id = data.teacher_id
        if data.start_date is not None:
            schedule.start_date = date.fromisoformat(data.start_date) if data.start_date else None
        if data.time_slots is not None:
            schedule.time_slots = data.time_slots
        if data.price is not None:
            schedule.price = data.price
        if data.custom_price is not None:
            schedule.custom_price = data.custom_price
        if data.full_package_price is not None:
            schedule.full_package_price = data.full_package_price
        if data.full_custom_price is not None:
            schedule.full_custom_price = data.full_custom_price

        await db.flush()
        return CourseScheduleResponse(
            id=schedule.id,
            course_id=schedule.course_id,
            teacher_id=schedule.teacher_id,
            start_date=str(schedule.start_date) if schedule.start_date else None,
            time_slots=schedule.time_slots,
            price=float(schedule.price),
            custom_price=float(schedule.custom_price),
            full_package_price=float(schedule.full_package_price) if schedule.full_package_price else None,
            full_custom_price=float(schedule.full_custom_price) if schedule.full_custom_price else None,
        )

    async def delete_schedule(self, db: AsyncSession, schedule_id: int) -> bool:
        """删除排课记录。"""
        result = await db.execute(
            select(CourseSchedule).where(CourseSchedule.id == schedule_id)
        )
        schedule = result.scalar_one_or_none()
        if not schedule:
            return False
        await db.delete(schedule)
        await db.flush()
        return True
