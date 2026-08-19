"""管理端老师管理 API 测试。

覆盖：列表分页/筛选、详情、新增、编辑、删除（含排课拒绝）、状态切换、
room_type 校验、权限控制。
"""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, get_current_admin
from app.models.course import Course
from app.models.course_schedule import CourseSchedule
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher


@pytest.fixture
def admin_headers():
    return {"X-Admin-Token": "test-admin-token"}


@pytest.fixture
async def seed_rooms(db_session: AsyncSession) -> dict:
    """Seed 培训室、综合室、自习室各一个。"""
    training_room = StudyRoom(
        name="一号培训室", address="测试路 1 号", room_type="training"
    )
    comprehensive_room = StudyRoom(
        name="综合室A", address="测试路 2 号", room_type="comprehensive"
    )
    study_room = StudyRoom(
        name="自习室B", address="测试路 3 号", room_type="study"
    )
    db_session.add_all([training_room, comprehensive_room, study_room])
    await db_session.flush()
    return {
        "training": training_room,
        "comprehensive": comprehensive_room,
        "study": study_room,
    }


def _payload(**overrides):
    data = {
        "name": "李明华",
        "avatar": "https://example.com/avatar.jpg",
        "title": "金牌讲师",
        "specialty": "考研政治",
        "teaching_years": 8,
        "education": "硕士",
        "school": "中国人民大学",
        "bio": "专注考研政治辅导8年。",
        "teaching_tags": ["逻辑清晰", "押题精准"],
        "qualifications": [{"name": "教师资格证", "sub": "高等教育"}],
        "room_ids": [],
    }
    data.update(overrides)
    return data


class TestAdminTeacherApi:
    @pytest.mark.asyncio
    async def test_create_and_detail(self, client: AsyncClient, admin_headers, seed_rooms):
        rooms = seed_rooms
        payload = _payload(room_ids=[rooms["training"].id, rooms["comprehensive"].id])
        resp = await client.post(
            "/api/v1/admin/teachers", json=payload, headers=admin_headers
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["name"] == "李明华"
        assert body["specialty"] == "考研政治"
        assert body["teaching_years"] == 8
        assert body["education"] == "硕士"
        assert body["teaching_tags"] == ["逻辑清晰", "押题精准"]
        assert body["qualifications"] == [{"name": "教师资格证", "sub": "高等教育"}]
        assert sorted(body["room_ids"]) == sorted(
            [rooms["training"].id, rooms["comprehensive"].id]
        )
        assert len(body["rooms"]) == 2
        assert {r["room_type"] for r in body["rooms"]} == {"training", "comprehensive"}
        assert body["status"] == "active"
        assert body["course_count"] == 0

        detail_resp = await client.get(
            f"/api/v1/admin/teachers/{body['id']}", headers=admin_headers
        )
        assert detail_resp.status_code == 200
        assert detail_resp.json()["name"] == "李明华"

    @pytest.mark.asyncio
    async def test_create_with_study_room_returns_400(
        self, client: AsyncClient, admin_headers, seed_rooms
    ):
        payload = _payload(room_ids=[seed_rooms["study"].id])
        resp = await client.post(
            "/api/v1/admin/teachers", json=payload, headers=admin_headers
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_with_missing_room_returns_400(
        self, client: AsyncClient, admin_headers, seed_rooms
    ):
        payload = _payload(room_ids=[99999])
        resp = await client.post(
            "/api/v1/admin/teachers", json=payload, headers=admin_headers
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_create_invalid_education_returns_422(
        self, client: AsyncClient, admin_headers
    ):
        resp = await client.post(
            "/api/v1/admin/teachers",
            json=_payload(education="博士后"),
            headers=admin_headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_filters_and_course_count(
        self, client: AsyncClient, admin_headers, db_session: AsyncSession, seed_rooms
    ):
        t1 = Teacher(name="李明华", specialty="考研政治", status="active")
        t2 = Teacher(name="王芳", specialty="英语", status="inactive")
        db_session.add_all([t1, t2])
        await db_session.flush()

        room = seed_rooms["training"]
        course = Course(name="政治冲刺班", room_id=room.id, category="postgraduate")
        db_session.add(course)
        await db_session.flush()
        db_session.add(
            CourseSchedule(course_id=course.id, teacher_id=t1.id, price=80)
        )
        await db_session.flush()

        resp = await client.get("/api/v1/admin/teachers", headers=admin_headers)
        assert resp.status_code == 200
        body = resp.json()
        assert body["total"] == 2
        item1 = next(i for i in body["items"] if i["id"] == t1.id)
        assert item1["course_count"] == 1
        # 兼容排课下拉字段
        assert item1["name"] == "李明华"

        kw_resp = await client.get(
            "/api/v1/admin/teachers?keyword=王芳", headers=admin_headers
        )
        assert kw_resp.json()["total"] == 1
        assert kw_resp.json()["items"][0]["name"] == "王芳"

        st_resp = await client.get(
            "/api/v1/admin/teachers?status=inactive", headers=admin_headers
        )
        assert st_resp.json()["total"] == 1
        assert st_resp.json()["items"][0]["id"] == t2.id

    @pytest.mark.asyncio
    async def test_update_teacher(self, client: AsyncClient, admin_headers, seed_rooms):
        rooms = seed_rooms
        create_resp = await client.post(
            "/api/v1/admin/teachers",
            json=_payload(room_ids=[rooms["training"].id]),
            headers=admin_headers,
        )
        teacher_id = create_resp.json()["id"]

        update_resp = await client.put(
            f"/api/v1/admin/teachers/{teacher_id}",
            json={
                "name": "李明华（更新）",
                "teaching_years": 10,
                "teaching_tags": ["新版标签"],
                "room_ids": [rooms["comprehensive"].id],
            },
            headers=admin_headers,
        )
        assert update_resp.status_code == 200
        body = update_resp.json()
        assert body["name"] == "李明华（更新）"
        assert body["teaching_years"] == 10
        assert body["teaching_tags"] == ["新版标签"]
        assert body["room_ids"] == [rooms["comprehensive"].id]
        # 未更新字段保持不变
        assert body["school"] == "中国人民大学"

    @pytest.mark.asyncio
    async def test_update_with_study_room_returns_400(
        self, client: AsyncClient, admin_headers, seed_rooms
    ):
        rooms = seed_rooms
        create_resp = await client.post(
            "/api/v1/admin/teachers", json=_payload(), headers=admin_headers
        )
        teacher_id = create_resp.json()["id"]
        resp = await client.put(
            f"/api/v1/admin/teachers/{teacher_id}",
            json={"room_ids": [rooms["study"].id]},
            headers=admin_headers,
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_update_missing_teacher_returns_404(
        self, client: AsyncClient, admin_headers
    ):
        resp = await client.put(
            "/api/v1/admin/teachers/99999",
            json={"name": "不存在"},
            headers=admin_headers,
        )
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_toggle_status(self, client: AsyncClient, admin_headers):
        create_resp = await client.post(
            "/api/v1/admin/teachers", json=_payload(), headers=admin_headers
        )
        teacher_id = create_resp.json()["id"]

        resp = await client.patch(
            f"/api/v1/admin/teachers/{teacher_id}/status",
            json={"status": "inactive"},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "inactive"

        # 停用后 C 端不可见
        c_resp = await client.get(f"/api/v1/teachers/{teacher_id}")
        assert c_resp.status_code == 404

        resp2 = await client.patch(
            f"/api/v1/admin/teachers/{teacher_id}/status",
            json={"status": "active"},
            headers=admin_headers,
        )
        assert resp2.status_code == 200
        assert resp2.json()["status"] == "active"

    @pytest.mark.asyncio
    async def test_delete_teacher(self, client: AsyncClient, admin_headers, seed_rooms):
        rooms = seed_rooms
        create_resp = await client.post(
            "/api/v1/admin/teachers",
            json=_payload(room_ids=[rooms["training"].id]),
            headers=admin_headers,
        )
        teacher_id = create_resp.json()["id"]

        del_resp = await client.delete(
            f"/api/v1/admin/teachers/{teacher_id}", headers=admin_headers
        )
        assert del_resp.status_code == 200

        detail_resp = await client.get(
            f"/api/v1/admin/teachers/{teacher_id}", headers=admin_headers
        )
        assert detail_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_delete_with_schedules_returns_400(
        self, client: AsyncClient, admin_headers, db_session: AsyncSession, seed_rooms
    ):
        create_resp = await client.post(
            "/api/v1/admin/teachers", json=_payload(), headers=admin_headers
        )
        teacher_id = create_resp.json()["id"]

        room = seed_rooms["training"]
        course = Course(name="英语班", room_id=room.id, category="english")
        db_session.add(course)
        await db_session.flush()
        db_session.add(CourseSchedule(course_id=course.id, teacher_id=teacher_id, price=60))
        await db_session.flush()

        del_resp = await client.delete(
            f"/api/v1/admin/teachers/{teacher_id}", headers=admin_headers
        )
        assert del_resp.status_code == 400

    @pytest.mark.asyncio
    async def test_delete_missing_returns_404(self, client: AsyncClient, admin_headers):
        resp = await client.delete("/api/v1/admin/teachers/99999", headers=admin_headers)
        assert resp.status_code == 404

    @pytest.mark.asyncio
    async def test_missing_permission_returns_403(self, client: AsyncClient):
        from app.main import app

        app.dependency_overrides[get_current_admin] = lambda: AdminContext(
            admin_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            username="limited-admin",
            is_super_admin=False,
            permission_codes=set(),
            menu_ids=set(),
        )
        try:
            resp = await client.get("/api/v1/admin/teachers")
            assert resp.status_code == 403
            create_resp = await client.post(
                "/api/v1/admin/teachers", json=_payload()
            )
            assert create_resp.status_code == 403
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None
