"""后台评价审核与评分聚合回写测试。"""

import uuid
from datetime import date, time

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    AdminContext,
    get_current_admin,
    get_current_user_id,
    get_optional_current_user_id,
)
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
ADMIN_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")

AUDIT_PERMISSIONS = {
    "training:reviews:view",
    "training:reviews:audit",
    "training:reviews:reply",
}


def _admin_context(codes: set[str]) -> AdminContext:
    return AdminContext(
        admin_id=ADMIN_ID,
        username="moderator",
        is_super_admin=False,
        permission_codes=codes,
        menu_ids=set(),
    )


@pytest.fixture
async def auth_client(client: AsyncClient):
    """conftest 已把 get_current_admin 覆盖为 None（放行全部后台权限）。"""
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    app.dependency_overrides[get_optional_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)
    app.dependency_overrides.pop(get_optional_current_user_id, None)


@pytest.fixture
async def audit_client(auth_client: AsyncClient):
    """持有全部评价权限的真实管理员上下文，用于断言 reviewed_by。"""
    app = auth_client._transport.app
    app.dependency_overrides[get_current_admin] = lambda: _admin_context(AUDIT_PERMISSIONS)
    yield auth_client
    app.dependency_overrides[get_current_admin] = lambda: None


@pytest.fixture
async def view_only_client(auth_client: AsyncClient):
    """只有查看权限的非超管，用于断言审核/回复被 403 拦截。"""
    app = auth_client._transport.app
    app.dependency_overrides[get_current_admin] = lambda: _admin_context(
        {"training:reviews:view"}
    )
    yield auth_client
    app.dependency_overrides[get_current_admin] = lambda: None


@pytest.fixture
async def seed(db_session: AsyncSession) -> dict:
    """课程与老师带种子评分（模拟 seed 数据），下挂若干已完成订单。"""
    db_session.add_all(
        [
            User(id=USER_ID, phone="13800138001", nickname="小明", password_hash="h", username="u1"),
            User(id=OTHER_USER_ID, phone="13800138002", nickname="小红", password_hash="h", username="u2", avatar="https://e.com/b.jpg"),
        ]
    )
    room = StudyRoom(name="南门自习室", address="南门街 1 号", status="open", min_price=12)
    db_session.add(room)
    await db_session.flush()

    course = Course(room_id=room.id, name="考研数学冲刺", category="考研", rating=4.8)
    teacher = Teacher(name="张老师", rating=4.6)
    db_session.add_all([course, teacher])
    await db_session.flush()

    bookings = [
        Booking(
            user_id=str(user_id),
            room_id=room.id,
            date=date(2026, 8, i + 1),
            start_time=time(9, 0),
            end_time=time(11, 0),
            total_price=100,
            status=BookingStatus.COMPLETED.value,
            course_id=course.id,
            teacher_id=teacher.id,
        )
        for i, user_id in enumerate([USER_ID, OTHER_USER_ID, OTHER_USER_ID, OTHER_USER_ID])
    ]
    db_session.add_all(bookings)
    await db_session.flush()

    return {"room": room, "course": course, "teacher": teacher, "bookings": bookings}


async def _add_review(db_session: AsyncSession, seed: dict, index: int, **overrides) -> Review:
    """在 seed['bookings'][index] 上挂一条评价。"""
    booking = seed["bookings"][index]
    defaults = dict(
        booking_id=booking.id,
        user_id=uuid.UUID(booking.user_id),
        course_id=seed["course"].id,
        teacher_id=seed["teacher"].id,
        rating=5,
        content="老师讲得很清楚",
        is_anonymous=False,
        status=ReviewStatus.PENDING.value,
    )
    defaults.update(overrides)
    review = Review(**defaults)
    db_session.add(review)
    await db_session.flush()
    return review


# ── 5.4 后台列表与审核 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_admin_list_filters_by_status(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_review(db_session, seed, 0, status=ReviewStatus.PENDING.value)
    await _add_review(db_session, seed, 1, status=ReviewStatus.APPROVED.value)
    await _add_review(db_session, seed, 2, status=ReviewStatus.REJECTED.value, reject_reason="广告")

    all_response = await auth_client.get("/api/v1/admin/reviews")
    pending = await auth_client.get("/api/v1/admin/reviews?status=pending")
    rejected = await auth_client.get("/api/v1/admin/reviews?status=rejected")

    assert all_response.status_code == 200
    assert all_response.json()["total"] == 3
    assert pending.json()["total"] == 1
    assert rejected.json()["total"] == 1
    assert rejected.json()["items"][0]["reject_reason"] == "广告"


@pytest.mark.asyncio
async def test_admin_list_invalid_status_is_rejected(auth_client: AsyncClient) -> None:
    response = await auth_client.get("/api/v1/admin/reviews?status=unknown")

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_admin_keyword_matches_content_and_nickname(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_review(db_session, seed, 0, content="讲解清晰易懂")
    await _add_review(db_session, seed, 1, content="节奏偏快", rating=3)

    by_content = await auth_client.get("/api/v1/admin/reviews?keyword=讲解")
    by_nickname = await auth_client.get("/api/v1/admin/reviews?keyword=小红")
    no_hit = await auth_client.get("/api/v1/admin/reviews?keyword=不存在的关键字")

    assert by_content.json()["total"] == 1
    assert by_content.json()["items"][0]["content"] == "讲解清晰易懂"
    assert by_nickname.json()["total"] == 1
    assert by_nickname.json()["items"][0]["user_nickname"] == "小红"
    assert no_hit.json()["total"] == 0


@pytest.mark.asyncio
async def test_admin_sees_real_identity_of_anonymous_review(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_review(db_session, seed, 0, is_anonymous=True)

    admin = await auth_client.get("/api/v1/admin/reviews")
    public = await auth_client.get(f"/api/v1/reviews?course_id={seed['course'].id}")

    item = admin.json()["items"][0]
    assert item["user_nickname"] == "小明"
    assert item["is_anonymous"] is True
    # 同一条评价在 C 端未通过审核前不出现，脱敏行为由 test_api_review 覆盖
    assert public.json()["total"] == 0


@pytest.mark.asyncio
async def test_approve_records_operator_and_naive_datetime(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0)

    response = await audit_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
    )

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == ReviewStatus.APPROVED.value
    assert body["reviewed_at"] is not None

    await db_session.refresh(review)
    assert review.reviewed_by == ADMIN_ID
    # BUG-15 / BUG-29 防线：写库时间必须是 naive 的业务本地时间
    assert review.reviewed_at.tzinfo is None


@pytest.mark.asyncio
async def test_reject_without_reason_is_rejected(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0)

    empty = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "rejected"}
    )
    blank = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status",
        json={"status": "rejected", "reject_reason": "   "},
    )

    assert empty.status_code == 422
    assert blank.status_code == 422
    await db_session.refresh(review)
    assert review.status == ReviewStatus.PENDING.value


@pytest.mark.asyncio
async def test_invalid_target_status_is_rejected(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0)

    pending = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "pending"}
    )
    unknown = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "deleted"}
    )

    assert pending.status_code == 422
    assert unknown.status_code == 422
    await db_session.refresh(review)
    assert review.status == ReviewStatus.PENDING.value


@pytest.mark.asyncio
async def test_rejected_review_hidden_from_public_but_kept_in_mine(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(
        db_session, seed, 0, status=ReviewStatus.APPROVED.value
    )
    assert (await auth_client.get(f"/api/v1/reviews?course_id={seed['course'].id}")).json()["total"] == 1

    rejected = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status",
        json={"status": "rejected", "reject_reason": "包含广告信息"},
    )
    assert rejected.status_code == 200

    public = await auth_client.get(f"/api/v1/reviews?course_id={seed['course'].id}")
    mine = await auth_client.get("/api/v1/reviews?mine=true")

    assert public.json()["total"] == 0
    assert mine.json()["total"] == 1
    assert mine.json()["items"][0]["reject_reason"] == "包含广告信息"


@pytest.mark.asyncio
async def test_approve_is_idempotent(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0, rating=4)
    url = f"/api/v1/admin/reviews/{review.id}/status"

    first = await auth_client.patch(url, json={"status": "approved"})
    second = await auth_client.patch(url, json={"status": "approved"})

    assert first.status_code == 200
    assert second.status_code == 200
    await db_session.refresh(seed["course"])
    assert float(seed["course"].rating) == 4.0
    assert seed["course"].review_count == 1


@pytest.mark.asyncio
async def test_approve_clears_previous_reject_reason(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(
        db_session, seed, 0,
        status=ReviewStatus.REJECTED.value, reject_reason="旧理由",
    )

    response = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
    )

    assert response.status_code == 200
    assert response.json()["reject_reason"] is None


@pytest.mark.asyncio
async def test_audit_missing_review_is_404(auth_client: AsyncClient, seed: dict) -> None:
    response = await auth_client.patch(
        "/api/v1/admin/reviews/999999/status", json={"status": "approved"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_audit_and_reply_without_permission_are_forbidden(
    view_only_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0)

    audit = await view_only_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
    )
    reply = await view_only_client.patch(
        f"/api/v1/admin/reviews/{review.id}/reply", json={"reply_content": "感谢"}
    )
    listing = await view_only_client.get("/api/v1/admin/reviews")

    assert audit.status_code == 403
    assert reply.status_code == 403
    assert listing.status_code == 200
    await db_session.refresh(review)
    assert review.status == ReviewStatus.PENDING.value


@pytest.mark.asyncio
async def test_reply_write_update_and_clear(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0)
    url = f"/api/v1/admin/reviews/{review.id}/reply"

    created = await auth_client.patch(url, json={"reply_content": "感谢您的反馈"})
    assert created.status_code == 200
    assert created.json()["reply_content"] == "感谢您的反馈"
    await db_session.refresh(review)
    assert review.reply_at is not None and review.reply_at.tzinfo is None

    updated = await auth_client.patch(url, json={"reply_content": "已更新回复"})
    assert updated.json()["reply_content"] == "已更新回复"

    cleared = await auth_client.patch(url, json={"reply_content": "   "})
    assert cleared.json()["reply_content"] is None
    assert cleared.json()["reply_at"] is None
    await db_session.refresh(review)
    assert review.reply_content is None and review.reply_at is None


@pytest.mark.asyncio
async def test_reply_visible_in_public_list(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0, status=ReviewStatus.APPROVED.value)

    await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/reply", json={"reply_content": "感谢反馈"}
    )
    public = await auth_client.get(f"/api/v1/reviews?course_id={seed['course'].id}")

    assert public.json()["items"][0]["reply_content"] == "感谢反馈"


@pytest.mark.asyncio
async def test_overlong_reply_is_rejected(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0)

    response = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/reply", json={"reply_content": "感" * 501}
    )

    assert response.status_code == 422


# ── 5.5 评分聚合回写 ────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_first_approval_overwrites_seeded_rating(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    """种子评分 4.8 必须被真实聚合覆盖，而不是与之平均。"""
    review = await _add_review(db_session, seed, 0, rating=5)
    assert float(seed["course"].rating) == 4.8

    await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
    )

    await db_session.refresh(seed["course"])
    await db_session.refresh(seed["teacher"])
    assert float(seed["course"].rating) == 5.0
    assert seed["course"].review_count == 1
    assert float(seed["teacher"].rating) == 5.0
    assert seed["teacher"].review_count == 1


@pytest.mark.asyncio
async def test_aggregate_counts_only_approved(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    approved = await _add_review(db_session, seed, 0, rating=5, status=ReviewStatus.APPROVED.value)
    await _add_review(db_session, seed, 1, rating=1, status=ReviewStatus.PENDING.value)

    await auth_client.patch(
        f"/api/v1/admin/reviews/{approved.id}/status", json={"status": "approved"}
    )

    await db_session.refresh(seed["course"])
    assert float(seed["course"].rating) == 5.0
    assert seed["course"].review_count == 1


@pytest.mark.asyncio
async def test_rejecting_only_approved_review_resets_aggregate(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0, rating=5, status=ReviewStatus.APPROVED.value)
    await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
    )
    await db_session.refresh(seed["course"])
    assert seed["course"].review_count == 1

    await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status",
        json={"status": "rejected", "reject_reason": "违规"},
    )

    await db_session.refresh(seed["course"])
    await db_session.refresh(seed["teacher"])
    assert float(seed["course"].rating) == 0.0
    assert seed["course"].review_count == 0
    assert float(seed["teacher"].rating) == 0.0
    assert seed["teacher"].review_count == 0


@pytest.mark.asyncio
async def test_aggregate_uses_half_up_rounding(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    """5/5/4/3 → 4.25，须回写 4.3（非银行家舍入的 4.2）。"""
    reviews = [
        await _add_review(db_session, seed, i, rating=rating)
        for i, rating in enumerate([5, 5, 4, 3])
    ]

    for review in reviews:
        await auth_client.patch(
            f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
        )

    await db_session.refresh(seed["course"])
    assert float(seed["course"].rating) == 4.3
    assert seed["course"].review_count == 4


@pytest.mark.asyncio
async def test_teacher_aggregate_is_independent_from_course(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    other_course = Course(room_id=seed["room"].id, name="英语四级", category="语言", rating=0.0)
    db_session.add(other_course)
    await db_session.flush()

    extra_booking = Booking(
        user_id=str(OTHER_USER_ID),
        room_id=seed["room"].id,
        date=date(2026, 9, 1),
        start_time=time(9, 0),
        end_time=time(11, 0),
        total_price=100,
        status=BookingStatus.COMPLETED.value,
        course_id=other_course.id,
        teacher_id=seed["teacher"].id,
    )
    db_session.add(extra_booking)
    await db_session.flush()

    first = await _add_review(db_session, seed, 0, rating=5)
    second = Review(
        booking_id=extra_booking.id,
        user_id=OTHER_USER_ID,
        course_id=other_course.id,
        teacher_id=seed["teacher"].id,
        rating=4,
        content="另一位老师的课",
        is_anonymous=False,
        status=ReviewStatus.PENDING.value,
    )
    db_session.add(second)
    await db_session.flush()

    for review in (first, second):
        await auth_client.patch(
            f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
        )

    await db_session.refresh(seed["teacher"])
    await db_session.refresh(seed["course"])
    await db_session.refresh(other_course)
    # 老师维度合并两门课：(5 + 4) / 2 = 4.5
    assert float(seed["teacher"].rating) == 4.5
    assert seed["teacher"].review_count == 2
    # 两门课各自独立
    assert float(seed["course"].rating) == 5.0
    assert seed["course"].review_count == 1
    assert float(other_course.rating) == 4.0
    assert other_course.review_count == 1


@pytest.mark.asyncio
async def test_review_without_teacher_does_not_break_aggregate(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    review = await _add_review(db_session, seed, 0, rating=5, teacher_id=None)

    response = await auth_client.patch(
        f"/api/v1/admin/reviews/{review.id}/status", json={"status": "approved"}
    )

    assert response.status_code == 200
    await db_session.refresh(seed["course"])
    await db_session.refresh(seed["teacher"])
    assert float(seed["course"].rating) == 5.0
    assert seed["course"].review_count == 1
    # 老师维度无该评价参与，保留种子值不被误改
    assert float(seed["teacher"].rating) == 4.6
    assert seed["teacher"].review_count == 0
