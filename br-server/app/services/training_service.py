"""培训室与课程查询服务。"""

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
    """返回分页培训室列表，每间培训室附带最多 3 门热门课程。

    两步查询：
    Step1: 查询培训室（分页）
    Step2: 批量查询热门课程（JOIN teachers），Python 分组限制每间 3 门
    """
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    filters = [
        StudyRoom.status == "open",
        StudyRoom.room_type.in_(["training", "comprehensive"]),
    ]
    if city_id is not None:
        filters.append(StudyRoom.city_id == city_id)

    # Step1: 统计总数 + 分页查询培训室
    count_result = await db.execute(
        select(func.count()).select_from(StudyRoom).where(*filters)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(StudyRoom, City.name.label("city_name"))
        .outerjoin(City, StudyRoom.city_id == City.id)
        .where(*filters)
        .order_by(StudyRoom.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    rooms = result.all()

    if not rooms:
        return TrainingRoomListResponse(
            items=[], total=total, page=page, page_size=page_size
        )

    # Step2: 批量查询热门课程（JOIN teachers），按 room_id 分组限制 3 门
    room_ids = [room.id for room, _ in rooms]

    hot_result = await db.execute(
        select(Course, Teacher)
        .outerjoin(Teacher, Course.teacher_id == Teacher.id)
        .where(
            Course.room_id.in_(room_ids),
            Course.is_hot == True,  # noqa: E712
            Course.status == "active",
        )
        .order_by(Course.room_id.asc(), Course.sort_order.asc(), Course.id.asc())
    )
    hot_rows = hot_result.all()

    # Python 分组，每间房最多 3 门热门课程
    hot_by_room: dict[int, list[HotCourseItem]] = {}
    for course, teacher in hot_rows:
        if course.room_id not in hot_by_room:
            hot_by_room[course.room_id] = []
        if len(hot_by_room[course.room_id]) < 3:
            hot_by_room[course.room_id].append(
                HotCourseItem(
                    id=course.id,
                    name=course.name,
                    cover_image=course.cover_image,
                    teacher=TeacherResponse.model_validate(teacher) if teacher else None,
                    price=course.price,
                    enrollment_count=course.enrollment_count,
                )
            )

    # 组装响应
    items = []
    for room, city_name in rooms:
        item = TrainingRoomResponse.model_validate(room)
        item.city_name = city_name
        item.hot_courses = hot_by_room.get(room.id, [])
        items.append(item)

    return TrainingRoomListResponse(
        items=items, total=total, page=page, page_size=page_size
    )


async def list_courses(
    db: AsyncSession,
    page: int = 1,
    page_size: int = DEFAULT_PAGE_SIZE,
    category: str | None = None,
) -> CourseListResponse:
    """返回分页课程列表，附带教室名和教师信息。

    单条查询：JOIN StudyRoom + Teacher。
    """
    page_size = min(page_size, MAX_PAGE_SIZE)
    offset = (page - 1) * page_size

    filters = [Course.status == "active"]
    if category is not None:
        filters.append(Course.category == category)

    count_result = await db.execute(
        select(func.count()).select_from(Course).where(*filters)
    )
    total = count_result.scalar_one()

    result = await db.execute(
        select(Course, StudyRoom.name.label("room_name"), Teacher)
        .join(StudyRoom, Course.room_id == StudyRoom.id)
        .outerjoin(Teacher, Course.teacher_id == Teacher.id)
        .where(*filters)
        .order_by(Course.sort_order.asc(), Course.id.asc())
        .offset(offset)
        .limit(page_size)
    )
    rows = result.all()

    items = []
    for course, room_name, teacher in rows:
        course_data = {c.name: getattr(course, c.name) for c in course.__table__.columns}
        course_data["room_name"] = room_name
        course_data["teacher"] = TeacherResponse.model_validate(teacher) if teacher else None
        items.append(CourseResponse(**course_data))

    return CourseListResponse(
        items=items, total=total, page=page, page_size=page_size
    )
