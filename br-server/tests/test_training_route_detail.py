"""API 路由测试：培训室详情 GET /api/v1/training/rooms/{room_id}。

覆盖 8 个场景（tasks.md 4.1–4.8）：
  4.1 正常培训室详情（全字段验证）
  4.2 综合室返回相同结构
  4.3 自习室 room_id → 404
  4.4 不存在的 room_id → 404
  4.5 教师去重（多门课程同一教师）
  4.6 空课程场景
  4.7 tags 解析（逗号分隔 → 数组）
  4.8 无教师课程（teacher 字段为 null）
"""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.city import City
from app.models.course import Course
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
async def seed_detail_data(db_session: AsyncSession):
    """播种培训室详情测试数据，覆盖全部 8 个场景。"""
    city = City(name="茂名市", province="广东", sort_order=1, status="active")
    db_session.add(city)
    await db_session.flush()

    # ── 培训室（training） ───────────────────────────────────────
    training_room = StudyRoom(
        name="去K书培训中心",
        description="专业培训环境",
        cover_image="https://example.com/cover.jpg",
        address="茂南区光谷大道88号3楼",
        city_id=city.id,
        business_hours="09:00-21:00",
        status="open",
        room_type="training",
        min_price=50.0,
        rating=4.8,
    )
    db_session.add(training_room)

    # ── 综合室（comprehensive） ──────────────────────────────────
    comprehensive_room = StudyRoom(
        name="综合学习中心",
        description="综合学习环境",
        address="茂南区YY路2号",
        business_hours="07:00-23:00",
        status="open",
        room_type="comprehensive",
        min_price=10.0,
        rating=4.5,
        city_id=city.id,
    )
    db_session.add(comprehensive_room)

    # ── 自习室（study）—— 应返回 404 ────────────────────────────
    study_room = StudyRoom(
        name="普通自习室",
        address="某处",
        status="open",
        room_type="study",
        min_price=8.0,
        city_id=city.id,
    )
    db_session.add(study_room)

    # ── 空培训室（无课程） ──────────────────────────────────────
    empty_room = StudyRoom(
        name="空培训室",
        description="暂无课程",
        address="地址D",
        status="open",
        room_type="training",
        min_price=30.0,
        rating=4.0,
        city_id=city.id,
    )
    db_session.add(empty_room)
    await db_session.flush()

    # ── 教师 ────────────────────────────────────────────────────
    teacher1 = Teacher(name="李明华", avatar="https://example.com/t1.jpg",
                       title="考研政治 · 8年教龄", rating=4.9)
    teacher2 = Teacher(name="王晓雯", avatar="https://example.com/t2.jpg",
                       title="公考行测 · 6年教龄", rating=4.8)
    db_session.add_all([teacher1, teacher2])
    await db_session.flush()

    # ── 课程 ────────────────────────────────────────────────────
    courses = [
        # 培训室课程 1：teacher1，有 tags
        Course(
            room_id=training_room.id, teacher_id=teacher1.id,
            name="考研政治冲刺班",
            cover_image="https://example.com/c1.jpg",
            category="postgraduate", price=80.0, rating=4.9,
            enrollment_count=120, schedule="每周二 14:00",
            tags="热销,小班", status="active", is_hot=True, sort_order=1,
        ),
        # 培训室课程 2：同一 teacher1（用于去重测试），有 tags
        Course(
            room_id=training_room.id, teacher_id=teacher1.id,
            name="考研政治基础班",
            cover_image="https://example.com/c2.jpg",
            category="postgraduate", price=60.0, rating=4.7,
            enrollment_count=80, schedule="每周三 19:00",
            tags="基础", status="active", is_hot=False, sort_order=2,
        ),
        # 培训室课程 3：teacher2
        Course(
            room_id=training_room.id, teacher_id=teacher2.id,
            name="公务员行测精讲",
            cover_image="https://example.com/c3.jpg",
            category="civil_service", price=60.0, rating=4.8,
            enrollment_count=95, schedule="每周三 19:00",
            tags="新课,行测", status="active", is_hot=True, sort_order=3,
        ),
        # 培训室课程 4：无教师，tags=None
        Course(
            room_id=training_room.id, teacher_id=None,
            name="自习辅导",
            cover_image=None, category="skills",
            price=30.0, rating=4.5, enrollment_count=40,
            schedule="每日", tags=None, status="active",
            is_hot=False, sort_order=4,
        ),
        # 综合室课程 1
        Course(
            room_id=comprehensive_room.id, teacher_id=teacher1.id,
            name="考研综合辅导",
            category="postgraduate", price=70.0, rating=4.6,
            enrollment_count=60, status="active",
            is_hot=False, sort_order=1, tags="考研",
        ),
    ]
    db_session.add_all(courses)
    await db_session.commit()

    return {
        "city": city,
        "training_room": training_room,
        "comprehensive_room": comprehensive_room,
        "study_room": study_room,
        "empty_room": empty_room,
        "teacher1": teacher1,
        "teacher2": teacher2,
    }


class TestTrainingRoomDetailAPI:
    """培训室详情 API 测试（8 个场景）。"""

    # ── 4.1 正常请求培训室详情：验证响应字段完整性 ──────────────
    async def test_training_room_detail_all_fields(self, client, seed_detail_data):
        """4.1 正常培训室详情：验证房间信息、教师、课程、统计全字段。"""
        room = seed_detail_data["training_room"]
        resp = await client.get(f"/api/v1/training/rooms/{room.id}")
        assert resp.status_code == 200

        data = resp.json()
        # 房间基本信息
        assert data["id"] == room.id
        assert data["name"] == "去K书培训中心"
        assert data["description"] == "专业培训环境"
        assert data["cover_image"] == "https://example.com/cover.jpg"
        assert data["address"] == "茂南区光谷大道88号3楼"
        assert data["business_hours"] == "09:00-21:00"
        assert data["status"] == "open"
        assert data["room_type"] == "training"
        assert float(data["min_price"]) == 50.0
        assert float(data["rating"]) == 4.8
        assert data["city_name"] == "茂名市"

        # 教室概况统计：4 门 active 课程
        assert data["classroom_count"] == 4
        assert data["class_capacity"] == "8-12"
        # 教师去重：teacher1 出现 2 次但只计 1 人
        assert data["teacher_count"] == 2
        # 总学生数 = 120 + 80 + 95 + 40 = 335
        assert data["total_students"] == 335

        # 名师团队
        assert len(data["teachers"]) == 2
        teacher_names = {t["name"] for t in data["teachers"]}
        assert teacher_names == {"李明华", "王晓雯"}

        # 课程列表（按 sort_order 排序）
        assert len(data["courses"]) == 4
        assert data["courses"][0]["name"] == "考研政治冲刺班"
        assert data["courses"][1]["name"] == "考研政治基础班"
        assert data["courses"][2]["name"] == "公务员行测精讲"
        assert data["courses"][3]["name"] == "自习辅导"

    # ── 4.2 综合室返回相同结构 ───────────────────────────────────
    async def test_comprehensive_room_detail(self, client, seed_detail_data):
        """4.2 综合室详情返回与培训室相同的结构。"""
        room = seed_detail_data["comprehensive_room"]
        resp = await client.get(f"/api/v1/training/rooms/{room.id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["room_type"] == "comprehensive"
        assert data["name"] == "综合学习中心"
        # 必须有相同 key 结构
        assert "classroom_count" in data
        assert "teacher_count" in data
        assert "total_students" in data
        assert "teachers" in data
        assert "courses" in data
        # 有 1 门课程
        assert data["classroom_count"] == 1
        assert data["teacher_count"] == 1
        assert len(data["courses"]) == 1

    # ── 4.3 自习室 room_id → 404 ────────────────────────────────
    async def test_404_for_study_room(self, client, seed_detail_data):
        """4.3 请求自习室 room_id 返回 404。"""
        room = seed_detail_data["study_room"]
        resp = await client.get(f"/api/v1/training/rooms/{room.id}")
        assert resp.status_code == 404

    # ── 4.4 不存在的 room_id → 404 ──────────────────────────────
    async def test_404_for_non_existent_room(self, client, seed_detail_data):
        """4.4 请求不存在的 room_id 返回 404。"""
        resp = await client.get("/api/v1/training/rooms/999999")
        assert resp.status_code == 404

    # ── 4.5 教师去重 ─────────────────────────────────────────────
    async def test_teacher_deduplication(self, client, seed_detail_data):
        """4.5 多门课程关联同一教师时 teachers 数组去重。"""
        room = seed_detail_data["training_room"]
        resp = await client.get(f"/api/v1/training/rooms/{room.id}")
        data = resp.json()

        teacher_ids = [t["id"] for t in data["teachers"]]
        # 无重复
        assert len(teacher_ids) == len(set(teacher_ids))
        # 只有 2 位教师（teacher1 关联了 2 门课程但不重复）
        assert len(teacher_ids) == 2

    # ── 4.6 空课程场景 ───────────────────────────────────────────
    async def test_empty_courses_scenario(self, client, seed_detail_data):
        """4.6 培训室无课程时 teachers 和 courses 数组为空，统计值为 0。"""
        room = seed_detail_data["empty_room"]
        resp = await client.get(f"/api/v1/training/rooms/{room.id}")
        assert resp.status_code == 200

        data = resp.json()
        assert data["classroom_count"] == 0
        assert data["teacher_count"] == 0
        assert data["total_students"] == 0
        assert data["teachers"] == []
        assert data["courses"] == []

    # ── 4.7 tags 解析：逗号分隔字符串 → 数组 ────────────────────
    async def test_tags_parsing(self, client, seed_detail_data):
        """4.7 tags 字段从逗号分隔字符串解析为数组，None 转为空数组。"""
        room = seed_detail_data["training_room"]
        resp = await client.get(f"/api/v1/training/rooms/{room.id}")
        data = resp.json()

        # 多 tag 课程
        course1 = next(c for c in data["courses"] if c["name"] == "考研政治冲刺班")
        assert course1["tags"] == ["热销", "小班"]

        # 单 tag 课程
        course2 = next(c for c in data["courses"] if c["name"] == "考研政治基础班")
        assert course2["tags"] == ["基础"]

        # tags=None → 空数组
        course4 = next(c for c in data["courses"] if c["name"] == "自习辅导")
        assert course4["tags"] == []

    # ── 4.8 无教师课程：teacher 字段为 null ──────────────────────
    async def test_course_without_teacher(self, client, seed_detail_data):
        """4.8 课程未关联教师时 teacher 字段为 null，有教师的课程正常返回。"""
        room = seed_detail_data["training_room"]
        resp = await client.get(f"/api/v1/training/rooms/{room.id}")
        data = resp.json()

        # 无教师课程
        course_no_teacher = next(c for c in data["courses"] if c["name"] == "自习辅导")
        assert course_no_teacher["teacher"] is None

        # 有教师课程
        course_with_teacher = next(c for c in data["courses"] if c["name"] == "考研政治冲刺班")
        assert course_with_teacher["teacher"] is not None
        assert course_with_teacher["teacher"]["name"] == "李明华"
