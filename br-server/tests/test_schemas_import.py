"""
培训课程相关 Schema 导入与功能测试

验证以下 schema 能正确导入和使用：
- TeacherResponse, TeacherBrief, HotCourseItem
- TrainingRoomResponse, TrainingRoomListResponse
- CourseResponse, CourseListResponse
- StudyRoomResponse 包含 room_type 字段
"""

from decimal import Decimal


def test_import_teacher_response():
    """TeacherResponse 可正确导入并实例化"""
    from app.schemas.teacher import TeacherResponse

    teacher = TeacherResponse(
        id=1, name="张三", avatar="https://example.com/a.jpg",
        title="高级讲师", rating=Decimal("4.8"),
    )
    assert teacher.id == 1
    assert teacher.name == "张三"
    assert teacher.rating == Decimal("4.8")


def test_import_course_schemas():
    """course.py 中所有 schema 可正确导入"""
    from app.schemas.course import (
        CourseListResponse,
        CourseResponse,
        HotCourseItem,
        TeacherBrief,
        TrainingRoomListResponse,
        TrainingRoomResponse,
    )

    # TeacherBrief 实例化
    tb = TeacherBrief(id=1, name="李四", rating=Decimal("4.5"))
    assert tb.id == 1

    # HotCourseItem 实例化
    hc = HotCourseItem(
        id=10, name="Python入门", price=Decimal("99.00"),
        enrollment_count=120, teacher=tb,
    )
    assert hc.enrollment_count == 120

    # TrainingRoomResponse 实例化
    tr = TrainingRoomResponse(
        id=1, name="培训室A", address="地址1", status="open",
        room_type="training", min_price=Decimal("50.00"),
        rating=Decimal("4.5"),
        hot_courses=[hc],
    )
    assert tr.room_type == "training"
    assert len(tr.hot_courses) == 1

    # TrainingRoomListResponse 实例化
    trl = TrainingRoomListResponse(items=[tr], total=1, page=1, page_size=10)
    assert trl.total == 1


def test_course_response_tags_parsing():
    """CourseResponse.parse_tags 正确解析逗号分隔字符串"""
    from app.schemas.course import CourseResponse

    course = CourseResponse(
        id=1, name="课程A", category="编程", price=Decimal("99"),
        rating=Decimal("4.5"), enrollment_count=50, tags="Python,入门,热门",
        status="active", room_id=1, room_name="培训室A",
    )
    assert course.tags == ["Python", "入门", "热门"]


def test_course_response_tags_empty_string():
    """空字符串 tags 返回空列表"""
    from app.schemas.course import CourseResponse

    course = CourseResponse(
        id=1, name="课程B", category="设计", price=Decimal("50"),
        rating=Decimal("4.0"), enrollment_count=10, tags="",
        status="active", room_id=1, room_name="培训室B",
    )
    assert course.tags == []


def test_course_response_tags_none():
    """None tags 返回空列表"""
    from app.schemas.course import CourseResponse

    course = CourseResponse(
        id=1, name="课程C", category="设计", price=Decimal("50"),
        rating=Decimal("4.0"), enrollment_count=10, tags=None,
        status="active", room_id=1, room_name="培训室C",
    )
    assert course.tags == []


def test_course_response_tags_strip_whitespace():
    """tags 中多余空格被正确去除"""
    from app.schemas.course import CourseResponse

    course = CourseResponse(
        id=1, name="课程D", category="编程", price=Decimal("80"),
        rating=Decimal("4.2"), enrollment_count=30,
        tags=" Python , 进阶 , 实战 ",
        status="active", room_id=1, room_name="培训室D",
    )
    assert course.tags == ["Python", "进阶", "实战"]


def test_study_room_response_has_room_type():
    """StudyRoomResponse 包含 room_type 字段"""
    from app.schemas.study_room import StudyRoomResponse

    room = StudyRoomResponse(
        id=1, name="自习室A", description="描述", cover_image=None,
        address="地址", business_hours=None, status="open", room_type="study",
        min_price=Decimal("10"),
    )
    assert room.room_type == "study"


def test_room_create_has_room_type():
    """RoomCreate 包含 room_type 字段，默认值 study"""
    from app.schemas.study_room import RoomCreate

    room = RoomCreate(name="新室", address="地址", room_type="training")
    assert room.room_type == "training"

    # 默认值
    room2 = RoomCreate(name="新室", address="地址")
    assert room2.room_type == "study"


def test_room_update_has_room_type():
    """RoomUpdate 包含 room_type 字段，默认 None"""
    from app.schemas.study_room import RoomUpdate

    room = RoomUpdate(room_type="comprehensive")
    assert room.room_type == "comprehensive"

    room2 = RoomUpdate()
    assert room2.room_type is None


def test_room_admin_response_has_room_type():
    """RoomAdminResponse 包含 room_type 字段"""
    from datetime import datetime
    from app.schemas.study_room import RoomAdminResponse

    room = RoomAdminResponse(
        id=1, name="室A", description=None, cover_image=None,
        address="地址", business_hours=None, status="open",
        room_type="training", min_price=Decimal("10"),
        created_at=datetime.now(), updated_at=datetime.now(),
    )
    assert room.room_type == "training"
