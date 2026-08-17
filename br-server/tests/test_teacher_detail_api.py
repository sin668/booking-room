"""教师详情 API 测试。

覆盖：有课程、无课程、不存在教师、bio 为 null、tags 解析。
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.course_lesson import CourseLesson
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.user import User


USER_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
async def seed_teacher_data(db_session: AsyncSession) -> dict:
    """Seed teacher, room, courses, and lessons."""
    teacher = Teacher(
        name="李明华",
        avatar="https://example.com/avatar.jpg",
        title="考研政治 · 8年教龄",
        rating=4.9,
        bio="毕业于中国人民大学，专注考研政治辅导8年。",
        student_count=328,
    )
    db_session.add(teacher)
    await db_session.flush()

    teacher_no_bio = Teacher(
        name="王芳",
        title="英语讲师",
        rating=4.5,
    )
    db_session.add(teacher_no_bio)
    await db_session.flush()

    room = StudyRoom(
        name="测试教室",
        address="测试路 1 号",
        status="open",
        min_price=10,
    )
    db_session.add(room)
    await db_session.flush()

    course1 = Course(
        name="考研政治冲刺班",
        room_id=room.id,
        teacher_id=teacher.id,
        category="postgraduate",
        price=80.0,
        rating=4.9,
        enrollment_count=328,
        status="active",
        tags="政治,冲刺",
        sort_order=1,
    )
    db_session.add(course1)
    await db_session.flush()

    course2 = Course(
        name="考研政治基础强化",
        room_id=room.id,
        teacher_id=teacher.id,
        category="postgraduate",
        price=60.0,
        rating=4.8,
        enrollment_count=256,
        status="active",
        sort_order=2,
    )
    db_session.add(course2)
    await db_session.flush()

    # Add lessons for course1
    for i in range(1, 13):
        db_session.add(CourseLesson(
            course_id=course1.id,
            title=f"第{i}讲",
            sort_order=i,
        ))
    await db_session.flush()

    return {
        "teacher": teacher,
        "teacher_no_bio": teacher_no_bio,
        "room": room,
        "course1": course1,
        "course2": course2,
    }


# ---------------------------------------------------------------------------
# 有课程的教师详情
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teacher_detail_with_courses(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_teacher_data: dict,
) -> None:
    data = seed_teacher_data
    response = await client.get(f"/api/v1/teachers/{data['teacher'].id}")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "李明华"
    assert body["bio"] is not None
    assert body["student_count"] == 328
    assert len(body["courses"]) == 2

    # Check lesson_count for course1
    course1_data = next(c for c in body["courses"] if c["id"] == data["course1"].id)
    assert course1_data["lesson_count"] == 12
    assert course1_data["name"] == "考研政治冲刺班"
    assert course1_data["room_name"] == "测试教室"

    # Check tags parsed
    assert course1_data["tags"] == ["政治", "冲刺"]

    # course2 has no lessons
    course2_data = next(c for c in body["courses"] if c["id"] == data["course2"].id)
    assert course2_data["lesson_count"] == 0


# ---------------------------------------------------------------------------
# 无课程的教师
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teacher_detail_no_courses(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_teacher_data: dict,
) -> None:
    teacher = seed_teacher_data["teacher_no_bio"]
    response = await client.get(f"/api/v1/teachers/{teacher.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "王芳"
    assert body["courses"] == []


# ---------------------------------------------------------------------------
# 不存在的教师
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teacher_detail_not_found(
    client: AsyncClient,
) -> None:
    response = await client.get("/api/v1/teachers/99999")
    assert response.status_code == 404


# ---------------------------------------------------------------------------
# bio 为 null
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_teacher_detail_bio_null(
    client: AsyncClient,
    db_session: AsyncSession,
    seed_teacher_data: dict,
) -> None:
    teacher = seed_teacher_data["teacher_no_bio"]
    response = await client.get(f"/api/v1/teachers/{teacher.id}")

    assert response.status_code == 200
    body = response.json()
    assert body["bio"] is None
    assert body["student_count"] == 0
