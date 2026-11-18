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
    await db_session.commit()

    return {
        "super_user": super_user,
        "room": room_s,
        "course": course_s,
        "seat": seat_s,
        "bookings": (booking_course_s, booking_seat_s),
        "reviews": (review_course_s, review_seat_s),
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