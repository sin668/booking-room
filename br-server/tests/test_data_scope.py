"""数据权限：内容归属记录 + 非超管可见性过滤（含座位/预约/评价的关联归属）。"""

import uuid
from datetime import date, time

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from app.api.dependencies import AdminContext, get_current_admin
from app.main import app
from app.models.booking import Booking
from app.models.course import Course
from app.models.review import Review
from app.models.seat import Seat
from app.models.study_room import StudyRoom
from app.models.user import User

ADMIN_A = uuid.uuid4()
ADMIN_B = uuid.uuid4()
SUPER_ADMIN = uuid.uuid4()

PERMS = {
    "room:view", "room:create", "seat:view", "seat:create",
    "booking:view", "training:reviews:view",
    "coupon:view", "coupon:create", "teacher:view", "teacher:create",
    "room:update", "room:delete", "room:status",
    "seat:update", "seat:delete", "seat:status", "seat:bulk_create",
    "activity:view", "activity:update", "activity:delete", "activity:status",
    "coupon:update", "coupon:delete",
    "teacher:update", "teacher:delete", "teacher:status",
    "booking:cancel", "training:reviews:audit", "training:reviews:reply",
}


def ctx(admin_id: uuid.UUID, super_admin: bool = False) -> AdminContext:
    return AdminContext(
        admin_id=admin_id,
        username="tester",
        is_super_admin=super_admin,
        permission_codes=set(PERMS),
        menu_ids=set(),
    )


def as_admin(context: AdminContext | None):
    app.dependency_overrides[get_current_admin] = lambda: context


def make_room(name: str, created_by=None) -> StudyRoom:
    return StudyRoom(name=name, address="测试地址", created_by=created_by)


def make_course(name: str, room_id: int, created_by=None) -> Course:
    return Course(name=name, category="test", room_id=room_id, created_by=created_by)


def make_booking(room_id: int, user_id: str, course_id=None, booking_type="seat") -> Booking:
    return Booking(
        room_id=room_id,
        user_id=user_id,
        date=date(2026, 11, 17),
        start_time=time(9, 0),
        end_time=time(10, 0),
        total_price=10,
        course_id=course_id,
        booking_type=booking_type,
    )


@pytest.fixture
async def seed_content(db_session):
    """A/B 各一间教室一门课程，另有一份无创建人的存量数据。"""
    room_a = make_room("教室A", ADMIN_A)
    room_b = make_room("教室B", ADMIN_B)
    room_legacy = make_room("存量教室")
    db_session.add_all([room_a, room_b, room_legacy])
    await db_session.flush()

    course_a = make_course("课程A", room_a.id, ADMIN_A)
    course_b = make_course("课程B", room_b.id, ADMIN_B)
    course_legacy = make_course("存量课程", room_legacy.id)
    db_session.add_all([course_a, course_b, course_legacy])
    await db_session.flush()

    seat_a = Seat(room_id=room_a.id, seat_number="A-01", zone="A", price_per_hour=10, row=1, col=1)
    seat_b = Seat(room_id=room_b.id, seat_number="B-01", zone="B", price_per_hour=10, row=1, col=1)
    db_session.add_all([seat_a, seat_b])
    await db_session.flush()

    user = User(user_source="app", phone="13800000001", nickname="学员", password_hash="x")
    db_session.add(user)
    await db_session.flush()

    booking_course = make_booking(room_b.id, str(user.id), course_id=course_a.id, booking_type="course")
    booking_seat = make_booking(room_b.id, str(user.id))
    booking_legacy = make_booking(room_legacy.id, str(user.id))
    db_session.add_all([booking_course, booking_seat, booking_legacy])
    await db_session.flush()

    review_course = Review(booking_id=booking_course.id, user_id=user.id, course_id=course_a.id, rating=5, content="课程评价")
    review_seat = Review(booking_id=booking_seat.id, user_id=user.id, rating=4, content="座位评价")
    db_session.add_all([review_course, review_seat])
    await db_session.commit()

    return {
        "rooms": (room_a, room_b, room_legacy),
        "courses": (course_a, course_b, course_legacy),
        "seats": (seat_a, seat_b),
        "bookings": (booking_course, booking_seat, booking_legacy),
        "reviews": (review_course, review_seat),
        "user": user,
    }


# ---------------------------------------------------------------------------
# 创建接口记录创建人
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_create_course_records_creator(client: AsyncClient, db_session, seed_content):
    as_admin(ctx(ADMIN_A))
    room_a = seed_content["rooms"][0]
    resp = await client.post(
        "/api/v1/admin/courses",
        json={"name": "新建课程", "category": "test", "room_id": room_a.id},
    )
    assert resp.status_code == 201
    course_id = resp.json()["id"]
    created_by = (
        await db_session.execute(select(Course.created_by).where(Course.id == course_id))
    ).scalar_one()
    assert created_by == ADMIN_A


@pytest.mark.asyncio
async def test_create_room_records_creator(client: AsyncClient, db_session):
    as_admin(ctx(ADMIN_B))
    resp = await client.post(
        "/api/v1/admin/rooms",
        json={"name": "新建教室", "address": "测试地址"},
    )
    assert resp.status_code == 201
    room_id = resp.json()["id"]
    created_by = (
        await db_session.execute(select(StudyRoom.created_by).where(StudyRoom.id == room_id))
    ).scalar_one()
    assert created_by == ADMIN_B


@pytest.mark.asyncio
async def test_legacy_token_creator_is_null(client: AsyncClient, db_session, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    as_admin(None)
    resp = await client.post(
        "/api/v1/admin/rooms",
        json={"name": "legacy教室", "address": "测试地址"},
        headers={"X-Admin-Token": "test-admin-token"},
    )
    assert resp.status_code == 201
    room_id = resp.json()["id"]
    created_by = (
        await db_session.execute(select(StudyRoom.created_by).where(StudyRoom.id == room_id))
    ).scalar_one()
    assert created_by is None


# ---------------------------------------------------------------------------
# 内容型列表/详情过滤
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_course_list_scope(client: AsyncClient, seed_content):
    course_a, course_b, course_legacy = seed_content["courses"]

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/courses")).json()
    assert {item["id"] for item in body["items"]} == {course_a.id, course_legacy.id}

    as_admin(ctx(ADMIN_B))
    body = (await client.get("/api/v1/admin/courses")).json()
    assert {item["id"] for item in body["items"]} == {course_b.id, course_legacy.id}

    as_admin(ctx(ADMIN_A, super_admin=True))
    body = (await client.get("/api/v1/admin/courses")).json()
    assert {item["id"] for item in body["items"]} == {course_a.id, course_b.id, course_legacy.id}


@pytest.mark.asyncio
async def test_course_detail_scope(client: AsyncClient, seed_content):
    course_a = seed_content["courses"][0]
    as_admin(ctx(ADMIN_B))
    assert (await client.get(f"/api/v1/admin/courses/{course_a.id}")).status_code == 404
    as_admin(ctx(ADMIN_A))
    assert (await client.get(f"/api/v1/admin/courses/{course_a.id}")).status_code == 200


@pytest.mark.asyncio
async def test_room_list_and_detail_scope(client: AsyncClient, seed_content):
    room_a, room_b, room_legacy = seed_content["rooms"]

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/rooms")).json()
    assert {item["id"] for item in body["items"]} == {room_a.id, room_legacy.id}
    assert (await client.get(f"/api/v1/admin/rooms/{room_b.id}")).status_code == 404
    assert (await client.get(f"/api/v1/admin/rooms/{room_a.id}")).status_code == 200


@pytest.mark.asyncio
async def test_coupon_and_teacher_list_scope(client: AsyncClient, db_session):
    from datetime import datetime

    from app.models.coupon import Coupon
    from app.models.teacher import Teacher

    coupon_a = Coupon(
        name="券A", type="amount_off", discount_amount=5, created_by=ADMIN_A,
        valid_from=datetime(2026, 1, 1), expires_at=datetime(2027, 1, 1),
    )
    coupon_b = Coupon(
        name="券B", type="amount_off", discount_amount=5, created_by=ADMIN_B,
        valid_from=datetime(2026, 1, 1), expires_at=datetime(2027, 1, 1),
    )
    teacher_a = Teacher(name="师A", created_by=ADMIN_A)
    teacher_b = Teacher(name="师B", created_by=ADMIN_B)
    db_session.add_all([coupon_a, coupon_b, teacher_a, teacher_b])
    await db_session.commit()

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/coupons")).json()
    assert {item["id"] for item in body["items"]} == {coupon_a.id}
    body = (await client.get("/api/v1/admin/teachers")).json()
    assert {item["id"] for item in body["items"]} == {teacher_a.id}
    assert (await client.get(f"/api/v1/admin/coupons/{coupon_b.id}")).status_code == 404
    assert (await client.get(f"/api/v1/admin/teachers/{teacher_b.id}")).status_code == 404


# ---------------------------------------------------------------------------
# 座位随教室归属
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_seat_follows_room(client: AsyncClient, seed_content):
    room_a, room_b, _ = seed_content["rooms"]
    seat_a, seat_b = seed_content["seats"]

    as_admin(ctx(ADMIN_A))
    resp = await client.get(f"/api/v1/admin/rooms/{room_a.id}/seats")
    assert resp.status_code == 200
    assert [s["id"] for s in resp.json()] == [seat_a.id]
    assert (await client.get(f"/api/v1/admin/rooms/{room_b.id}/seats")).status_code == 404
    assert (await client.get(f"/api/v1/admin/seats/{seat_b.id}")).status_code == 404
    assert (await client.get(f"/api/v1/admin/seats/{seat_a.id}")).status_code == 200


# ---------------------------------------------------------------------------
# 预约/评价随关联内容归属
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_booking_follows_associated_content(client: AsyncClient, seed_content):
    booking_course, booking_seat, booking_legacy = seed_content["bookings"]

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/bookings")).json()
    assert {item["id"] for item in body["items"]} == {booking_course.id, booking_legacy.id}
    assert (await client.get(f"/api/v1/admin/bookings/{booking_seat.id}")).status_code == 404

    as_admin(ctx(ADMIN_B))
    body = (await client.get("/api/v1/admin/bookings")).json()
    assert {item["id"] for item in body["items"]} == {booking_seat.id, booking_legacy.id}

    as_admin(ctx(ADMIN_A, super_admin=True))
    body = (await client.get("/api/v1/admin/bookings")).json()
    assert body["total"] == 3


@pytest.mark.asyncio
async def test_review_follows_associated_content(client: AsyncClient, seed_content):
    review_course, review_seat = seed_content["reviews"]

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/reviews")).json()
    assert {item["id"] for item in body["items"]} == {review_course.id}

    as_admin(ctx(ADMIN_B))
    body = (await client.get("/api/v1/admin/reviews")).json()
    assert {item["id"] for item in body["items"]} == {review_seat.id}

    as_admin(ctx(ADMIN_B, super_admin=True))
    body = (await client.get("/api/v1/admin/reviews")).json()
    assert body["total"] == 2


# ---------------------------------------------------------------------------
# 超管创建的数据对有权限用户公开可见
# ---------------------------------------------------------------------------


@pytest.fixture
async def seed_super_content(db_session, seed_content):
    """超管创建的教室/课程/座位/预约/评价。"""
    super_user = User(
        id=SUPER_ADMIN, user_source="admin", user_type="super-admin",
        phone="13900000001", username="superadmin", nickname="超管", password_hash="x",
    )
    db_session.add(super_user)
    room_s = make_room("超管教室", SUPER_ADMIN)
    db_session.add(room_s)
    await db_session.flush()

    course_s = make_course("超管课程", room_s.id, SUPER_ADMIN)
    db_session.add(course_s)
    await db_session.flush()

    seat_s = Seat(room_id=room_s.id, seat_number="S-01", zone="S", price_per_hour=10, row=1, col=1)
    db_session.add(seat_s)
    await db_session.flush()

    user = seed_content["user"]
    booking_course_s = make_booking(room_s.id, str(user.id), course_id=course_s.id, booking_type="course")
    booking_seat_s = make_booking(room_s.id, str(user.id))
    db_session.add_all([booking_course_s, booking_seat_s])
    await db_session.flush()

    review_course_s = Review(booking_id=booking_course_s.id, user_id=user.id, course_id=course_s.id, rating=5, content="超管课程评价")
    review_seat_s = Review(booking_id=booking_seat_s.id, user_id=user.id, rating=4, content="超管座位评价")
    db_session.add_all([review_course_s, review_seat_s])

    from datetime import datetime

    from app.models.activity import Activity
    from app.models.coupon import Coupon
    from app.models.teacher import Teacher

    activity_s = Activity(title="超管活动", is_active=False, created_by=SUPER_ADMIN)
    coupon_s = Coupon(
        name="超管券", type="amount_off", discount_amount=5, created_by=SUPER_ADMIN,
        valid_from=datetime(2026, 1, 1), expires_at=datetime(2027, 1, 1),
    )
    teacher_s = Teacher(name="超管师", created_by=SUPER_ADMIN)
    db_session.add_all([activity_s, coupon_s, teacher_s])
    await db_session.commit()

    return {
        "super_user": super_user,
        "room": room_s,
        "course": course_s,
        "seat": seat_s,
        "bookings": (booking_course_s, booking_seat_s),
        "reviews": (review_course_s, review_seat_s),
        "activity": activity_s,
        "coupon": coupon_s,
        "teacher": teacher_s,
    }


@pytest.mark.asyncio
async def test_super_admin_content_public_to_normal_admin(client: AsyncClient, seed_content, seed_super_content):
    room_s = seed_super_content["room"]
    course_s = seed_super_content["course"]
    room_b = seed_content["rooms"][1]

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/rooms")).json()
    assert room_s.id in {item["id"] for item in body["items"]}
    body = (await client.get("/api/v1/admin/courses")).json()
    assert course_s.id in {item["id"] for item in body["items"]}
    assert (await client.get(f"/api/v1/admin/rooms/{room_s.id}")).status_code == 200
    assert (await client.get(f"/api/v1/admin/courses/{course_s.id}")).status_code == 200
    # 其他普通管理员创建的数据仍被过滤
    assert (await client.get(f"/api/v1/admin/rooms/{room_b.id}")).status_code == 404


@pytest.mark.asyncio
async def test_super_admin_seats_bookings_reviews_public(client: AsyncClient, seed_content, seed_super_content):
    room_s = seed_super_content["room"]
    seat_s = seed_super_content["seat"]
    booking_course_s, booking_seat_s = seed_super_content["bookings"]
    review_course_s, review_seat_s = seed_super_content["reviews"]

    as_admin(ctx(ADMIN_A))
    resp = await client.get(f"/api/v1/admin/rooms/{room_s.id}/seats")
    assert resp.status_code == 200
    assert [s["id"] for s in resp.json()] == [seat_s.id]

    body = (await client.get("/api/v1/admin/bookings")).json()
    ids = {item["id"] for item in body["items"]}
    assert {booking_course_s.id, booking_seat_s.id} <= ids

    body = (await client.get("/api/v1/admin/reviews")).json()
    ids = {item["id"] for item in body["items"]}
    assert {review_course_s.id, review_seat_s.id} <= ids


@pytest.mark.asyncio
async def test_demoted_super_admin_content_not_public(client: AsyncClient, db_session, seed_content, seed_super_content):
    room_s = seed_super_content["room"]
    course_s = seed_super_content["course"]

    super_user = await db_session.get(User, SUPER_ADMIN)
    super_user.user_type = "normal-user"
    await db_session.commit()

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/rooms")).json()
    assert room_s.id not in {item["id"] for item in body["items"]}
    assert (await client.get(f"/api/v1/admin/courses/{course_s.id}")).status_code == 404


# ---------------------------------------------------------------------------
# 写保护助手：超管创建的数据对非超管只读
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_readonly_creators(db_session, seed_content, seed_super_content):
    from app.services.data_scope import readonly_creators

    ids = [SUPER_ADMIN, ADMIN_B, None]
    assert await readonly_creators(db_session, ids, ctx(ADMIN_A)) == {SUPER_ADMIN}
    assert await readonly_creators(db_session, ids, ctx(ADMIN_A, super_admin=True)) == set()
    assert await readonly_creators(db_session, [], ctx(ADMIN_A)) == set()


@pytest.mark.asyncio
async def test_ensure_writable_helper(db_session, seed_content, seed_super_content):
    from fastapi import HTTPException

    from app.services.data_scope import ensure_writable

    room_s = seed_super_content["room"]
    room_a, _, room_legacy = seed_content["rooms"]

    with pytest.raises(HTTPException) as exc:
        await ensure_writable(db_session, StudyRoom, room_s.id, ctx(ADMIN_A))
    assert exc.value.status_code == 403

    # 自己创建、存量、超管查看、目标不存在均不拦截
    await ensure_writable(db_session, StudyRoom, room_a.id, ctx(ADMIN_A))
    await ensure_writable(db_session, StudyRoom, room_legacy.id, ctx(ADMIN_A))
    await ensure_writable(db_session, StudyRoom, room_s.id, ctx(ADMIN_A, super_admin=True))
    await ensure_writable(db_session, StudyRoom, 999999, ctx(ADMIN_A))


@pytest.mark.asyncio
async def test_ensure_writable_after_demotion(db_session, seed_content, seed_super_content):
    from app.services.data_scope import ensure_writable

    room_s = seed_super_content["room"]
    super_user = await db_session.get(User, SUPER_ADMIN)
    super_user.user_type = "normal-user"
    await db_session.flush()
    await ensure_writable(db_session, StudyRoom, room_s.id, ctx(ADMIN_A))


@pytest.mark.asyncio
async def test_ensure_record_writable_helpers(db_session, seed_content, seed_super_content):
    from fastapi import HTTPException

    from app.services.data_scope import (
        ensure_booking_writable,
        ensure_review_writable,
        ensure_seat_writable,
    )

    seat_s = seed_super_content["seat"]
    seat_a = seed_content["seats"][0]
    booking_course_s, booking_seat_s = seed_super_content["bookings"]
    review_course_s, review_seat_s = seed_super_content["reviews"]
    viewer = ctx(ADMIN_A)

    for helper, obj_id in (
        (ensure_seat_writable, seat_s.id),
        (ensure_booking_writable, booking_course_s.id),
        (ensure_booking_writable, booking_seat_s.id),
        (ensure_review_writable, review_course_s.id),
        (ensure_review_writable, review_seat_s.id),
    ):
        with pytest.raises(HTTPException) as exc:
            await helper(db_session, obj_id, viewer)
        assert exc.value.status_code == 403

    await ensure_seat_writable(db_session, seat_a.id, viewer)
    await ensure_seat_writable(db_session, seat_s.id, ctx(SUPER_ADMIN, super_admin=True))


# ---------------------------------------------------------------------------
# 写端点 403 与 readonly 标志（内容型五类）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_super_content_write_endpoints_rejected(client: AsyncClient, db_session, seed_content, seed_super_content):
    room_s = seed_super_content["room"]
    course_s = seed_super_content["course"]
    activity_s = seed_super_content["activity"]
    coupon_s = seed_super_content["coupon"]
    teacher_s = seed_super_content["teacher"]

    as_admin(ctx(ADMIN_A))
    requests = [
        ("put", f"/api/v1/admin/rooms/{room_s.id}", {"name": "改名"}),
        ("delete", f"/api/v1/admin/rooms/{room_s.id}", None),
        ("patch", f"/api/v1/admin/rooms/{room_s.id}/status", {"status": "closed"}),
        ("put", f"/api/v1/admin/courses/{course_s.id}", {"name": "改名"}),
        ("delete", f"/api/v1/admin/courses/{course_s.id}", None),
        ("patch", f"/api/v1/admin/courses/{course_s.id}/status?status=closed", None),
        ("post", f"/api/v1/admin/courses/{course_s.id}/lessons", {"title": "课时", "sort_order": 1}),
        ("delete", f"/api/v1/admin/courses/{course_s.id}/lessons/1", None),
        ("delete", f"/api/v1/admin/courses/{course_s.id}/schedules/1", None),
        ("put", f"/api/v1/admin/activities/{activity_s.id}", {"title": "改名"}),
        ("delete", f"/api/v1/admin/activities/{activity_s.id}", None),
        ("patch", f"/api/v1/admin/activities/{activity_s.id}/status", {"is_active": False}),
        ("put", f"/api/v1/admin/coupons/{coupon_s.id}", {"name": "改名"}),
        ("patch", f"/api/v1/admin/coupons/{coupon_s.id}/status", {"is_active": False}),
        ("delete", f"/api/v1/admin/coupons/{coupon_s.id}", None),
        ("put", f"/api/v1/admin/teachers/{teacher_s.id}", {"name": "改名"}),
        ("patch", f"/api/v1/admin/teachers/{teacher_s.id}/status", {"status": "inactive"}),
        ("delete", f"/api/v1/admin/teachers/{teacher_s.id}", None),
        ("put", f"/api/v1/admin/teachers/{teacher_s.id}/available-time-slots", {"available_time_slots": []}),
    ]
    for method, url, body in requests:
        resp = await getattr(client, method)(url, **({"json": body} if body is not None else {}))
        assert resp.status_code == 403, f"{method.upper()} {url} -> {resp.status_code}"

    # 数据未被修改
    await db_session.refresh(room_s)
    assert room_s.name == "超管教室"


@pytest.mark.asyncio
async def test_readonly_flags_in_content_lists(client: AsyncClient, seed_content, seed_super_content):
    room_s = seed_super_content["room"]
    course_s = seed_super_content["course"]
    room_a, _, room_legacy = seed_content["rooms"]
    course_a, _, course_legacy = seed_content["courses"]

    as_admin(ctx(ADMIN_A))
    body = (await client.get("/api/v1/admin/rooms")).json()
    flags = {item["id"]: item["readonly"] for item in body["items"]}
    assert flags == {room_s.id: True, room_a.id: False, room_legacy.id: False}
    assert (await client.get(f"/api/v1/admin/rooms/{room_s.id}")).json()["readonly"] is True
    assert (await client.get(f"/api/v1/admin/rooms/{room_a.id}")).json()["readonly"] is False

    body = (await client.get("/api/v1/admin/courses")).json()
    flags = {item["id"]: item["readonly"] for item in body["items"]}
    assert flags == {course_s.id: True, course_a.id: False, course_legacy.id: False}
    assert (await client.get(f"/api/v1/admin/courses/{course_s.id}")).json()["readonly"] is True

    for path, obj_key in (("activities", "activity"), ("coupons", "coupon"), ("teachers", "teacher")):
        body = (await client.get(f"/api/v1/admin/{path}")).json()
        item = next(i for i in body["items"] if i["id"] == seed_super_content[obj_key].id)
        assert item["readonly"] is True

    as_admin(ctx(SUPER_ADMIN, super_admin=True))
    body = (await client.get("/api/v1/admin/rooms")).json()
    assert all(item["readonly"] is False for item in body["items"])


@pytest.mark.asyncio
async def test_own_and_legacy_content_writable(client: AsyncClient, seed_content, seed_super_content):
    room_a, _, room_legacy = seed_content["rooms"]

    as_admin(ctx(ADMIN_A))
    resp = await client.put(f"/api/v1/admin/rooms/{room_a.id}", json={"name": "教室A改"})
    assert resp.status_code == 200
    assert resp.json()["readonly"] is False
    resp = await client.patch(f"/api/v1/admin/rooms/{room_legacy.id}/status", json={"status": "closed"})
    assert resp.status_code == 200

    # 超管本人可写自己的数据
    as_admin(ctx(SUPER_ADMIN, super_admin=True))
    room_s = seed_super_content["room"]
    resp = await client.put(f"/api/v1/admin/rooms/{room_s.id}", json={"name": "超管教室改"})
    assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 写端点 403 与 readonly 标志（座位/预约/评价）
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_super_record_write_endpoints_rejected(client: AsyncClient, db_session, seed_content, seed_super_content):
    room_s = seed_super_content["room"]
    seat_s = seed_super_content["seat"]
    booking_course_s, booking_seat_s = seed_super_content["bookings"]
    review_course_s, review_seat_s = seed_super_content["reviews"]

    as_admin(ctx(ADMIN_A))
    requests = [
        ("post", f"/api/v1/admin/rooms/{room_s.id}/seats",
         {"seat_number": "S-02", "zone": "quiet", "price_per_hour": 10, "row": 1, "col": 2}),
        ("post", f"/api/v1/admin/rooms/{room_s.id}/seats/bulk",
         {"seats": [{"zone": "quiet", "rows": 1, "cols": 1, "prefix": "S", "price_per_hour": 10}]}),
        ("put", f"/api/v1/admin/seats/{seat_s.id}", {"seat_number": "S-99"}),
        ("delete", f"/api/v1/admin/seats/{seat_s.id}", None),
        ("patch", f"/api/v1/admin/seats/{seat_s.id}/status", {"status": "maintenance"}),
        ("post", f"/api/v1/admin/bookings/{booking_course_s.id}/cancel", None),
        ("post", f"/api/v1/admin/bookings/{booking_seat_s.id}/confirm", None),
        ("patch", f"/api/v1/admin/reviews/{review_course_s.id}/status", {"status": "approved"}),
        ("patch", f"/api/v1/admin/reviews/{review_seat_s.id}/reply", {"reply_content": "回复"}),
    ]
    for method, url, body in requests:
        resp = await getattr(client, method)(url, **({"json": body} if body is not None else {}))
        assert resp.status_code == 403, f"{method.upper()} {url} -> {resp.status_code}"

    # 数据未被修改
    await db_session.refresh(seat_s)
    assert seat_s.seat_number == "S-01"
    await db_session.refresh(review_seat_s)
    assert review_seat_s.reply_content is None


@pytest.mark.asyncio
async def test_readonly_flags_in_record_lists(client: AsyncClient, seed_content, seed_super_content):
    room_s = seed_super_content["room"]
    seat_s = seed_super_content["seat"]
    room_a = seed_content["rooms"][0]
    booking_course_s, booking_seat_s = seed_super_content["bookings"]
    booking_course, _, booking_legacy = seed_content["bookings"]
    review_course_s, review_seat_s = seed_super_content["reviews"]
    review_course, _ = seed_content["reviews"]

    as_admin(ctx(ADMIN_A))
    seats = (await client.get(f"/api/v1/admin/rooms/{room_s.id}/seats")).json()
    assert seats and all(s["readonly"] is True for s in seats)
    assert (await client.get(f"/api/v1/admin/seats/{seat_s.id}")).json()["readonly"] is True
    seats = (await client.get(f"/api/v1/admin/rooms/{room_a.id}/seats")).json()
    assert seats and all(s["readonly"] is False for s in seats)

    body = (await client.get("/api/v1/admin/bookings")).json()
    flags = {i["id"]: i["readonly"] for i in body["items"]}
    assert flags == {
        booking_course_s.id: True, booking_seat_s.id: True,
        booking_course.id: False, booking_legacy.id: False,
    }
    assert (await client.get(f"/api/v1/admin/bookings/{booking_course_s.id}")).json()["readonly"] is True
    assert (await client.get(f"/api/v1/admin/bookings/{booking_course.id}")).json()["readonly"] is False

    body = (await client.get("/api/v1/admin/reviews")).json()
    flags = {i["id"]: i["readonly"] for i in body["items"]}
    assert flags == {review_course_s.id: True, review_seat_s.id: True, review_course.id: False}

    as_admin(ctx(SUPER_ADMIN, super_admin=True))
    body = (await client.get("/api/v1/admin/bookings")).json()
    assert all(i["readonly"] is False for i in body["items"])
    body = (await client.get("/api/v1/admin/reviews")).json()
    assert all(i["readonly"] is False for i in body["items"])


@pytest.mark.asyncio
async def test_own_records_writable(client: AsyncClient, seed_content, seed_super_content):
    seat_a = seed_content["seats"][0]
    review_course = seed_content["reviews"][0]

    as_admin(ctx(ADMIN_A))
    resp = await client.put(f"/api/v1/admin/seats/{seat_a.id}", json={"seat_number": "A-02"})
    assert resp.status_code == 200
    assert resp.json()["readonly"] is False
    resp = await client.patch(f"/api/v1/admin/reviews/{review_course.id}/reply", json={"reply_content": "感谢反馈"})
    assert resp.status_code == 200
    assert resp.json()["readonly"] is False