"""全局模糊搜索服务。"""

from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.schemas.search import (
    SearchCourseItem,
    SearchResponse,
    SearchRoomItem,
    SearchTeacherItem,
)

SEARCH_LIMIT = 5


async def search_all(
    db: AsyncSession,
    keyword: str,
    city_id: int | None = None,
) -> SearchResponse:
    """统一搜索自习室、培训室、课程、老师。"""
    pattern = f"%{keyword}%"

    room_result = await db.execute(
        select(StudyRoom)
        .where(
            StudyRoom.status == "open",
            or_(
                StudyRoom.name.ilike(pattern),
                StudyRoom.address.ilike(pattern),
            ),
            *([StudyRoom.city_id == city_id] if city_id else []),
        )
        .order_by(StudyRoom.id.asc())
        .limit(SEARCH_LIMIT)
    )
    rooms = [
        SearchRoomItem(
            id=r.id,
            name=r.name,
            address=r.address or "",
            cover_image=r.cover_image,
            room_type=r.room_type,
            min_price=r.min_price,
        )
        for r in room_result.scalars().all()
    ]

    course_result = await db.execute(
        select(Course, StudyRoom.name, Teacher.name, CourseSchedule.price)
        .join(StudyRoom, Course.room_id == StudyRoom.id)
        .outerjoin(
            CourseSchedule,
            (Course.id == CourseSchedule.course_id)
            & (CourseSchedule.schedule_type == "fixed")
            & (CourseSchedule.schedule_status == "in_progress"),
        )
        .outerjoin(Teacher, CourseSchedule.teacher_id == Teacher.id)
        .where(
            Course.status == "active",
            or_(
                Course.name.ilike(pattern),
                Teacher.name.ilike(pattern),
            ),
        )
        .order_by(Course.id.asc())
        .limit(SEARCH_LIMIT)
    )
    courses = [
        SearchCourseItem(
            id=c.id,
            name=c.name,
            cover_image=c.cover_image,
            room_name=room_name or "",
            teacher_name=teacher_name,
            price=price or 0,
            category=c.category,
        )
        for c, room_name, teacher_name, price in course_result.all()
    ]

    teacher_result = await db.execute(
        select(Teacher)
        .where(
            Teacher.status == "active",
            Teacher.name.ilike(pattern),
        )
        .order_by(Teacher.id.asc())
        .limit(SEARCH_LIMIT)
    )
    teachers = [
        SearchTeacherItem(
            id=t.id,
            name=t.name,
            avatar=t.avatar,
            title=t.title,
            specialty=t.specialty,
        )
        for t in teacher_result.scalars().all()
    ]

    return SearchResponse(rooms=rooms, courses=courses, teachers=teachers)
