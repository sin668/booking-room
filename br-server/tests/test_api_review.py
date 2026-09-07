"""C 端学员评价接口测试（发表 / 查询 / 可见性 / 筛选排序分页 / 概览）。"""

import uuid
from datetime import date, time

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_optional_current_user_id
from app.domain.booking_status import BookingStatus
from app.domain.review_status import ReviewStatus
from app.models.booking import Booking
from app.models.course import Course
from app.models.review import Review
from app.models.study_room import StudyRoom
from app.models.teacher import Teacher
from app.models.user import User

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    app.dependency_overrides[get_optional_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_optional_current_user_id, None)


@pytest.fixture
async def seed(db_session: AsyncSession) -> dict:
    """两个用户 + 一个自习室 + 一门课 + 一位老师 + 两个已完成订单。"""
    db_session.add_all(
        [
            User(id=USER_ID, phone="13800138001", nickname="小明", password_hash="h", username="u1"),
            User(id=OTHER_USER_ID, phone="13800138002", nickname="小红", password_hash="h", username="u2", avatar="https://example.com/b.jpg"),
        ]
    )
    room = StudyRoom(name="南门自习室", address="南门街 1 号", status="open", min_price=12)
    db_session.add(room)
    await db_session.flush()

    course = Course(room_id=room.id, name="考研数学冲刺", category="考研")
    teacher = Teacher(name="张老师")
    db_session.add_all([course, teacher])
    await db_session.flush()

    def _booking(user_id: uuid.UUID) -> Booking:
        return Booking(
            user_id=str(user_id),
            room_id=room.id,
            date=date(2026, 8, 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            total_price=100,
            status=BookingStatus.COMPLETED.value,
            course_id=course.id,
            teacher_id=teacher.id,
        )

    mine = _booking(USER_ID)
    others = _booking(OTHER_USER_ID)
    db_session.add_all([mine, others])
    await db_session.flush()

    return {
        "room": room,
        "course": course,
        "teacher": teacher,
        "my_booking": mine,
        "other_booking": others,
    }


async def _add_review(db_session: AsyncSession, seed: dict, **overrides) -> Review:
    defaults = dict(
        booking_id=seed["my_booking"].id,
        user_id=USER_ID,
        course_id=seed["course"].id,
        teacher_id=seed["teacher"].id,
        rating=5,
        content="老师讲得很清楚",
        is_anonymous=False,
        status=ReviewStatus.APPROVED.value,
    )
    defaults.update(overrides)
    review = Review(**defaults)
    db_session.add(review)
    await db_session.flush()
    return review


# ── 5.1 发表 ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_create_review_persists_pending_with_booking_context(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    response = await auth_client.post(
        "/api/v1/reviews",
        json={
            "booking_id": seed["my_booking"].id,
            "rating": 5,
            "content": "老师讲得很清楚",
            "images": ["https://example.com/a.jpg"],
            "tags": ["讲解清晰"],
            "is_anonymous": True,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert data["status"] == ReviewStatus.PENDING.value
    assert data["reject_reason"] is None
    assert data["course_id"] == seed["course"].id
    assert data["teacher_id"] == seed["teacher"].id
    assert data["course_name"] == "考研数学冲刺"
    assert data["teacher_name"] == "张老师"
    assert data["images"] == ["https://example.com/a.jpg"]

    review = (await db_session.execute(select(Review))).scalar_one()
    assert review.status == ReviewStatus.PENDING.value
    assert review.reviewed_by is None and review.reviewed_at is None


@pytest.mark.asyncio
async def test_create_review_normalises_empty_images_and_tags_to_empty_list(
    auth_client: AsyncClient, seed: dict
) -> None:
    response = await auth_client.post(
        "/api/v1/reviews",
        json={"booking_id": seed["my_booking"].id, "rating": 4, "content": "还行"},
    )

    assert response.status_code == 200
    assert response.json()["images"] == []
    assert response.json()["tags"] == []


@pytest.mark.asyncio
async def test_review_uncompleted_booking_is_rejected(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    seed["my_booking"].status = BookingStatus.PENDING_START.value
    await db_session.flush()

    response = await auth_client.post(
        "/api/v1/reviews",
        json={"booking_id": seed["my_booking"].id, "rating": 5, "content": "好"},
    )

    assert response.status_code == 400
    assert "已完成" in response.json()["detail"]


@pytest.mark.asyncio
async def test_review_other_users_booking_is_not_found(
    auth_client: AsyncClient, seed: dict
) -> None:
    response = await auth_client.post(
        "/api/v1/reviews",
        json={"booking_id": seed["other_booking"].id, "rating": 5, "content": "好"},
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_duplicate_review_for_same_booking_is_rejected(
    auth_client: AsyncClient, seed: dict
) -> None:
    payload = {"booking_id": seed["my_booking"].id, "rating": 5, "content": "第一次"}

    first = await auth_client.post("/api/v1/reviews", json=payload)
    second = await auth_client.post("/api/v1/reviews", json={**payload, "content": "第二次"})

    assert first.status_code == 200
    assert second.status_code == 400
    assert "已评价" in second.json()["detail"]
    # 一单一评由 reviews.booking_id 的 UNIQUE 约束强制，
    # 第二次请求触发 IntegrityError 后 session 回滚（测试 fixture 不 commit），
    # 故此处不断言回滚后的行数，唯一性已由迁移的 DDL 保证


@pytest.mark.parametrize(
    "payload",
    [
        {"rating": 0, "content": "好"},
        {"rating": 6, "content": "好"},
        {"rating": 5, "content": ""},
        {"rating": 5, "content": "   "},
        {"rating": 5, "content": "好" * 501},
        {"rating": 5, "content": "好", "images": ["https://e.com/%d.jpg" % i for i in range(10)]},
        {"rating": 5, "content": "好", "tags": ["t%d" % i for i in range(6)]},
    ],
)
@pytest.mark.asyncio
async def test_invalid_review_payload_is_rejected(
    auth_client: AsyncClient, seed: dict, payload: dict
) -> None:
    response = await auth_client.post(
        "/api/v1/reviews", json={"booking_id": seed["my_booking"].id, **payload}
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_create_review_without_login_is_rejected(client: AsyncClient, seed: dict) -> None:
    response = await client.post(
        "/api/v1/reviews",
        json={"booking_id": seed["my_booking"].id, "rating": 5, "content": "好"},
    )

    assert response.status_code == 401


# ── 5.2 查询与可见性 ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_public_list_filters_by_course_and_teacher(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    other_course = Course(room_id=seed["room"].id, name="英语四级", category="语言")
    db_session.add(other_course)
    await db_session.flush()

    await _add_review(db_session, seed, content="数学课评价")
    await _add_review(
        db_session,
        seed,
        booking_id=seed["other_booking"].id,
        user_id=OTHER_USER_ID,
        course_id=other_course.id,
        content="英语课评价",
    )

    by_course = await auth_client.get(f"/api/v1/reviews?course_id={seed['course'].id}")
    by_teacher = await auth_client.get(f"/api/v1/reviews?teacher_id={seed['teacher'].id}")

    assert by_course.status_code == 200
    assert by_course.json()["total"] == 1
    assert by_course.json()["items"][0]["content"] == "数学课评价"
    # 两条评价同属一位老师，故老师维度返回 2 条
    assert by_teacher.json()["total"] == 2


@pytest.mark.asyncio
async def test_public_list_only_returns_approved(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    other_bookings = [
        Booking(
            user_id=str(OTHER_USER_ID),
            room_id=seed["room"].id,
            date=date(2026, 8, i + 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            total_price=100,
            status=BookingStatus.COMPLETED.value,
            course_id=seed["course"].id,
            teacher_id=seed["teacher"].id,
        )
        for i in range(2)
    ]
    db_session.add_all(other_bookings)
    await db_session.flush()

    await _add_review(db_session, seed, status=ReviewStatus.APPROVED.value)
    await _add_review(
        db_session, seed, booking_id=other_bookings[0].id, user_id=OTHER_USER_ID,
        status=ReviewStatus.PENDING.value,
    )
    await _add_review(
        db_session, seed, booking_id=other_bookings[1].id, user_id=OTHER_USER_ID,
        status=ReviewStatus.REJECTED.value,
    )

    response = await auth_client.get(f"/api/v1/reviews?course_id={seed['course'].id}")

    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_unauthenticated_user_can_read_public_list(
    client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_review(db_session, seed)

    response = await client.get(f"/api/v1/reviews?course_id={seed['course'].id}")

    assert response.status_code == 200
    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_my_reviews_include_all_own_statuses_with_reject_reason(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    extra_bookings = [
        Booking(
            user_id=str(USER_ID),
            room_id=seed["room"].id,
            date=date(2026, 7, i + 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            total_price=100,
            status=BookingStatus.COMPLETED.value,
            course_id=seed["course"].id,
            teacher_id=seed["teacher"].id,
        )
        for i in range(2)
    ]
    db_session.add_all(extra_bookings)
    await db_session.flush()

    await _add_review(db_session, seed, status=ReviewStatus.APPROVED.value)
    await _add_review(db_session, seed, booking_id=extra_bookings[0].id, status=ReviewStatus.PENDING.value)
    await _add_review(
        db_session, seed, booking_id=extra_bookings[1].id,
        status=ReviewStatus.REJECTED.value, reject_reason="包含广告信息",
    )

    response = await auth_client.get("/api/v1/reviews?mine=true")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    reasons = {item["status"]: item["reject_reason"] for item in data["items"]}
    assert reasons[ReviewStatus.REJECTED.value] == "包含广告信息"
    # 本人查询不脱敏
    assert all(item["user_nickname"] == "小明" for item in data["items"])


@pytest.mark.asyncio
async def test_my_reviews_never_expose_other_users(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_review(
        db_session, seed, booking_id=seed["other_booking"].id, user_id=OTHER_USER_ID
    )

    response = await auth_client.get("/api/v1/reviews?mine=true")

    assert response.status_code == 200
    assert response.json()["total"] == 0


@pytest.mark.asyncio
async def test_my_reviews_without_login_is_rejected(client: AsyncClient) -> None:
    response = await client.get("/api/v1/reviews?mine=true")

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_anonymous_review_masks_author_in_public_list(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_review(db_session, seed, is_anonymous=True)

    public = await auth_client.get(f"/api/v1/reviews?course_id={seed['course'].id}")
    mine = await auth_client.get("/api/v1/reviews?mine=true")

    public_item = public.json()["items"][0]
    assert public_item["user_nickname"] == "匿名用户"
    assert public_item["user_avatar"] is None
    # 后台/本人视角不脱敏
    assert mine.json()["items"][0]["user_nickname"] == "小明"


@pytest.mark.asyncio
async def test_query_own_review_by_booking_id(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_review(db_session, seed)

    hit = await auth_client.get(f"/api/v1/reviews?mine=true&booking_id={seed['my_booking'].id}")
    miss = await auth_client.get(f"/api/v1/reviews?mine=true&booking_id={seed['other_booking'].id}")

    assert hit.json()["total"] == 1
    assert miss.status_code == 200
    assert miss.json()["total"] == 0


# ── 5.3 筛选 / 排序 / 分页 / 概览 ───────────────────────────────────


@pytest.fixture
async def seed_many_reviews(db_session: AsyncSession, seed: dict) -> dict:
    """同一课程/老师下 4 条已通过评价（5/5/4/3 星）+ 1 条 1 星带图。"""
    bookings = [
        Booking(
            user_id=str(OTHER_USER_ID),
            room_id=seed["room"].id,
            date=date(2026, 6, i + 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            total_price=100,
            status=BookingStatus.COMPLETED.value,
            course_id=seed["course"].id,
            teacher_id=seed["teacher"].id,
        )
        for i in range(4)
    ]
    db_session.add_all(bookings)
    await db_session.flush()

    for booking, rating in zip(bookings, [5, 5, 4, 3]):
        await _add_review(
            db_session, seed, booking_id=booking.id, user_id=OTHER_USER_ID, rating=rating
        )
    await _add_review(
        db_session, seed, rating=1, images=["https://example.com/x.jpg"], content="体验不好"
    )
    return seed


@pytest.mark.asyncio
async def test_rating_band_filters(auth_client: AsyncClient, seed_many_reviews: dict) -> None:
    course_id = seed_many_reviews["course"].id

    good = await auth_client.get(f"/api/v1/reviews?course_id={course_id}&rating_band=good")
    mid = await auth_client.get(f"/api/v1/reviews?course_id={course_id}&rating_band=mid")
    bad = await auth_client.get(f"/api/v1/reviews?course_id={course_id}&rating_band=bad")

    # 课程下共 5 条已通过评价（5/5/4/3/1），好评档含 5、5、4
    assert good.json()["total"] == 3
    assert mid.json()["total"] == 1
    assert bad.json()["total"] == 1


@pytest.mark.asyncio
async def test_has_images_filter(auth_client: AsyncClient, seed_many_reviews: dict) -> None:
    course_id = seed_many_reviews["course"].id

    response = await auth_client.get(f"/api/v1/reviews?course_id={course_id}&has_images=true")

    assert response.json()["total"] == 1
    assert response.json()["items"][0]["images"]


@pytest.mark.asyncio
async def test_has_images_filter_excludes_json_null(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    """回归：create_review 把空图片写成 JSON 字面量 null（非 SQL NULL）。

    images 是 JSON 列且 none_as_null=False，显式传 images=None 会被序列化成
    JSON 'null'，此时 `images IS NOT NULL` 为真，无图评价会漏进「仅看有图」。
    过滤须同时排除 SQL NULL、JSON null 与空数组 []。
    """
    course_id = seed["course"].id
    # 无图评价：显式 images=None → JSON 列序列化为字面量 null（复现线上数据）
    await _add_review(db_session, seed, booking_id=seed["my_booking"].id, images=None)
    # 有图评价
    await _add_review(
        db_session,
        seed,
        booking_id=seed["other_booking"].id,
        user_id=OTHER_USER_ID,
        images=["https://example.com/a.jpg"],
    )

    response = await auth_client.get(f"/api/v1/reviews?course_id={course_id}&has_images=true")

    assert response.json()["total"] == 1
    assert response.json()["items"][0]["images"] == ["https://example.com/a.jpg"]


@pytest.mark.asyncio
async def test_sort_by_score(auth_client: AsyncClient, seed_many_reviews: dict) -> None:
    course_id = seed_many_reviews["course"].id

    response = await auth_client.get(f"/api/v1/reviews?course_id={course_id}&sort=score")

    ratings = [item["rating"] for item in response.json()["items"]]
    assert ratings == sorted(ratings, reverse=True)


@pytest.mark.asyncio
async def test_page_size_over_limit_is_rejected(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/reviews?page_size=100")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_pagination_total_is_consistent(
    auth_client: AsyncClient, seed_many_reviews: dict
) -> None:
    course_id = seed_many_reviews["course"].id

    page2 = await auth_client.get(f"/api/v1/reviews?course_id={course_id}&page=2&page_size=2")

    data = page2.json()
    assert data["total"] == 5
    assert len(data["items"]) == 2
    assert data["page"] == 2 and data["page_size"] == 2


@pytest.mark.asyncio
async def test_summary_computes_average_rate_and_distribution(
    auth_client: AsyncClient, seed_many_reviews: dict
) -> None:
    course_id = seed_many_reviews["course"].id

    response = await auth_client.get(f"/api/v1/reviews/summary?course_id={course_id}")

    assert response.status_code == 200
    data = response.json()
    # 5/5/4/3/1 → 均分 3.6，4 星及以上 3 条 / 5 条 = 60%
    assert data["average"] == 3.6
    assert data["count"] == 5
    assert data["positive_rate"] == 60
    assert data["distribution"] == {"5": 2, "4": 1, "3": 1, "2": 0, "1": 1}


@pytest.mark.asyncio
async def test_summary_average_uses_half_up_rounding(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    """5/5/4/3 → 4.25，契约要求四舍五入为 4.3（非银行家舍入的 4.2）。"""
    bookings = [
        Booking(
            user_id=str(OTHER_USER_ID),
            room_id=seed["room"].id,
            date=date(2026, 5, i + 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            total_price=100,
            status=BookingStatus.COMPLETED.value,
            course_id=seed["course"].id,
            teacher_id=seed["teacher"].id,
        )
        for i in range(3)
    ]
    db_session.add_all(bookings)
    await db_session.flush()

    for booking, rating in zip(bookings, [5, 5, 4]):
        await _add_review(
            db_session, seed, booking_id=booking.id, user_id=OTHER_USER_ID, rating=rating
        )
    await _add_review(db_session, seed, rating=3)

    response = await auth_client.get(f"/api/v1/reviews/summary?course_id={seed['course'].id}")

    assert response.json()["average"] == 4.3
    assert response.json()["positive_rate"] == 75


@pytest.mark.asyncio
async def test_summary_excludes_unaudited_reviews(
    auth_client: AsyncClient, db_session: AsyncSession, seed_many_reviews: dict
) -> None:
    extra = Booking(
        user_id=str(OTHER_USER_ID),
        room_id=seed_many_reviews["room"].id,
        date=date(2026, 4, 1),
        start_time=time(9, 0),
        end_time=time(11, 0),
        total_price=100,
        status=BookingStatus.COMPLETED.value,
        course_id=seed_many_reviews["course"].id,
        teacher_id=seed_many_reviews["teacher"].id,
    )
    db_session.add(extra)
    await db_session.flush()
    await _add_review(
        db_session, seed_many_reviews, booking_id=extra.id, user_id=OTHER_USER_ID,
        rating=1, status=ReviewStatus.PENDING.value,
    )

    response = await auth_client.get(
        f"/api/v1/reviews/summary?course_id={seed_many_reviews['course'].id}"
    )

    assert response.json()["count"] == 5


@pytest.mark.asyncio
async def test_summary_without_reviews_returns_zeros(auth_client: AsyncClient, seed: dict) -> None:
    response = await auth_client.get(f"/api/v1/reviews/summary?teacher_id={seed['teacher'].id}")

    assert response.status_code == 200
    assert response.json() == {
        "average": 0.0,
        "count": 0,
        "positive_rate": 0,
        "distribution": {"5": 0, "4": 0, "3": 0, "2": 0, "1": 0},
    }


@pytest.mark.asyncio
async def test_summary_requires_a_dimension(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/reviews/summary")

    assert response.status_code == 422


# ── room_id 维度（自习室评价）──────────────────────────


@pytest.mark.asyncio
async def test_list_filters_by_room_id(
    auth_client: AsyncClient, seed_many_reviews: dict
) -> None:
    """自习室维度：seed 订单均为该室的 seat 订单，5 条评价全部命中。"""
    room_id = seed_many_reviews["room"].id

    response = await auth_client.get(f"/api/v1/reviews?room_id={room_id}")

    assert response.status_code == 200
    assert response.json()["total"] == 5


@pytest.mark.asyncio
async def test_room_id_filter_excludes_course_bookings(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    """综合室既出租座位又上课：课程订单（booking_type='course'）也带 room_id，
    但其评价属课程/老师维度，不应混进自习室评价区。"""
    room_id = seed["room"].id
    # 自习座位订单评价（应命中）
    await _add_review(
        db_session, seed, booking_id=seed["my_booking"].id, content="自习室很安静"
    )
    # 同室课程订单评价（应排除）
    course_booking = Booking(
        user_id=str(OTHER_USER_ID),
        room_id=room_id,
        date=date(2026, 9, 1),
        start_time=time(9, 0),
        end_time=time(11, 0),
        total_price=100,
        status=BookingStatus.COMPLETED.value,
        booking_type="course",
        course_id=seed["course"].id,
        teacher_id=seed["teacher"].id,
    )
    db_session.add(course_booking)
    await db_session.flush()
    await _add_review(
        db_session, seed, booking_id=course_booking.id, user_id=OTHER_USER_ID,
        content="老师讲得很好",
    )

    response = await auth_client.get(f"/api/v1/reviews?room_id={room_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["content"] == "自习室很安静"


@pytest.mark.asyncio
async def test_summary_by_room_id(
    auth_client: AsyncClient, seed_many_reviews: dict
) -> None:
    """自习室概览：与课程维度同口径（seed 订单同属该室），均分 3.6、5 条。"""
    room_id = seed_many_reviews["room"].id

    response = await auth_client.get(f"/api/v1/reviews/summary?room_id={room_id}")

    assert response.status_code == 200
    data = response.json()
    assert data["average"] == 3.6
    assert data["count"] == 5
