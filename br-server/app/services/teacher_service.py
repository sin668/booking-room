"""教师详情服务"""

from __future__ import annotations

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.teacher_room import TeacherRoom
from app.schemas.teacher import TeacherCourseItem, TeacherDetailResponse, TeacherRoomItem


async def get_teacher_detail(
    db: AsyncSession, teacher_id: int
) -> TeacherDetailResponse | None:
    """获取教师详情，包含关联课程列表和课时计数；停用教师对 C 端不可见"""
    teacher = await db.get(Teacher, teacher_id)
    if teacher is None or teacher.status == "inactive":
        return None

    # 查询所属培训室/综合室
    room_result = await db.execute(
        select(StudyRoom)
        .join(TeacherRoom, TeacherRoom.room_id == StudyRoom.id)
        .where(TeacherRoom.teacher_id == teacher_id)
        .order_by(TeacherRoom.id)
    )
    rooms = [
        TeacherRoomItem(id=r.id, name=r.name, room_type=r.room_type)
        for r in room_result.scalars().all()
    ]

    # 一次查询获取关联课程 + 课时计数，避免 N+1
    query = (
        select(
            Course,
            CourseSchedule,
            StudyRoom.name.label("room_name"),
            func.count(CourseLesson.id).label("lesson_count"),
        )
        .outerjoin(CourseSchedule, Course.id == CourseSchedule.course_id)
        .outerjoin(StudyRoom, Course.room_id == StudyRoom.id)
        .outerjoin(CourseLesson, Course.id == CourseLesson.course_id)
        .where(
            CourseSchedule.teacher_id == teacher_id,
            # 仅展示固定班课排课，定制课时不在 C 端老师简介页展示
            CourseSchedule.schedule_type == "fixed",
            Course.status == "active",
        )
        .group_by(Course.id, CourseSchedule.id, StudyRoom.name)
        .order_by(Course.sort_order, Course.id)
    )
    result = await db.execute(query)
    rows = result.all()

    courses = []
    for row in rows:
        course = row[0]
        schedule = row[1]
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
                price=schedule.price if schedule else 0,
                rating=course.rating,
                enrollment_count=course.enrollment_count,
                schedule=schedule.time_slots if schedule else None,
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
        specialty=teacher.specialty,
        teaching_years=teacher.teaching_years,
        education=teacher.education,
        school=teacher.school,
        status=teacher.status,
        teaching_tags=teacher.teaching_tags,
        qualifications=teacher.qualifications or [],
        rooms=rooms,
        courses=courses,
    )
