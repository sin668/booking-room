"""教师详情服务"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.schemas.teacher import TeacherCourseItem, TeacherDetailResponse


async def get_teacher_detail(
    db: AsyncSession, teacher_id: int
) -> TeacherDetailResponse | None:
    """获取教师详情，包含关联课程列表和课时计数"""
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None:
        return None

    # 一次查询获取关联课程 + 课时计数，避免 N+1
    query = (
        select(
            Course,
            StudyRoom.name.label("room_name"),
            func.count(CourseLesson.id).label("lesson_count"),
        )
        .outerjoin(StudyRoom, Course.room_id == StudyRoom.id)
        .outerjoin(CourseLesson, Course.id == CourseLesson.course_id)
        .where(
            Course.teacher_id == teacher_id,
            Course.status == "active",
        )
        .group_by(Course.id, StudyRoom.name)
        .order_by(Course.sort_order, Course.id)
    )
    result = await db.execute(query)
    rows = result.all()

    courses = []
    for row in rows:
        course = row[0]
        room_name = row.room_name or ""
        lesson_count = row.lesson_count or 0

        # 解析 tags
        tags_val = course.tags
        if tags_val is None or tags_val == "":
            tags_list: list[str] = []
        elif isinstance(tags_val, list):
            tags_list = tags_val
        else:
            tags_list = [t.strip() for t in tags_val.split(",") if t.strip()]

        courses.append(
            TeacherCourseItem(
                id=course.id,
                name=course.name,
                cover_image=course.cover_image,
                category=course.category,
                price=course.price,
                rating=course.rating,
                enrollment_count=course.enrollment_count,
                schedule=course.schedule,
                tags=tags_list,
                status=course.status,
                room_id=course.room_id,
                room_name=room_name,
                lesson_count=lesson_count,
            )
        )

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
