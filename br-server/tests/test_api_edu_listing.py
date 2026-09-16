"""教培供需 C 端接口测试：综合广场混排 / 仅 approved 可见 / 详情浏览数自增 /
认证前置校验 / 我的发布 / 校验边界。"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.domain.edu_listing_status import EduListingStatus
from app.models.edu_listing import EduListing
from app.models.user import User
from app.models.user_identity_verification import UserIdentityVerification

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


@pytest.fixture
async def auth_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID
    yield client
    app.dependency_overrides.pop(get_current_user_id, None)


@pytest.fixture
async def seed(db_session: AsyncSession) -> dict:
    db_session.add_all(
        [
            User(id=USER_ID, phone="13800138001", nickname="小明", password_hash="h", username="u1"),
            User(id=OTHER_USER_ID, phone="13800138002", nickname="小红", password_hash="h", username="u2", avatar="https://e.com/b.jpg"),
        ]
    )
    await db_session.flush()
    return {"user_id": USER_ID, "other_user_id": OTHER_USER_ID}


async def _add_listing(db_session: AsyncSession, **overrides) -> EduListing:
    defaults = dict(
        user_id=OTHER_USER_ID,
        listing_type="tutor",
        title="初中数学家教",
        subject="数学",
        price=Decimal("200.00"),
        area="广州市天河区",
        status=EduListingStatus.APPROVED.value,
        view_count=0,
    )
    defaults.update(overrides)
    listing = EduListing(**defaults)
    db_session.add(listing)
    await db_session.flush()
    return listing


async def _add_cert(db_session: AsyncSession, user_id, verification_type: str, status: str) -> None:
    db_session.add(
        UserIdentityVerification(
            user_id=user_id, verification_type=verification_type, status=status
        )
    )
    await db_session.flush()


# ── 综合广场列表 ────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_public_list_mixes_teach_and_demand(
    client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session, listing_type="tutor", title="家教")
    await _add_listing(db_session, listing_type="training", title="培训班")
    await _add_listing(db_session, listing_type="demand", title="求教")

    response = await client.get("/api/v1/edu-listings")

    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    types = {item["listing_type"] for item in data["items"]}
    assert types == {"tutor", "training", "demand"}


@pytest.mark.asyncio
async def test_public_list_only_returns_approved(
    client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session, status=EduListingStatus.APPROVED.value)
    await _add_listing(db_session, title="待审", status=EduListingStatus.PENDING.value)
    await _add_listing(db_session, title="驳回", status=EduListingStatus.REJECTED.value)
    await _add_listing(db_session, title="下架", status=EduListingStatus.OFFLINE.value)

    response = await client.get("/api/v1/edu-listings")

    assert response.json()["total"] == 1


@pytest.mark.asyncio
async def test_public_list_filters_by_type(
    client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session, listing_type="tutor", title="家教")
    await _add_listing(db_session, listing_type="demand", title="求教")

    response = await client.get("/api/v1/edu-listings?listing_type=demand")

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["listing_type"] == "demand"


@pytest.mark.asyncio
async def test_public_list_carries_publisher_nickname(
    client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session, user_id=OTHER_USER_ID)

    response = await client.get("/api/v1/edu-listings")

    item = response.json()["items"][0]
    assert item["publisher_nickname"] == "小红"
    assert item["publisher_avatar"] == "https://e.com/b.jpg"


# ── 详情 ────────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_detail_increments_view_count(
    client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session, view_count=5)

    response = await client.get(f"/api/v1/edu-listings/{listing.id}")

    assert response.status_code == 200
    assert response.json()["view_count"] == 6
    refreshed = (
        await db_session.execute(select(EduListing).where(EduListing.id == listing.id))
    ).scalar_one()
    assert refreshed.view_count == 6


@pytest.mark.asyncio
async def test_detail_includes_publisher_certification(
    client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_cert(db_session, OTHER_USER_ID, "education", "approved")
    listing = await _add_listing(db_session, user_id=OTHER_USER_ID, listing_type="tutor")

    response = await client.get(f"/api/v1/edu-listings/{listing.id}")

    data = response.json()
    assert data["publisher_education_verified"] is True
    assert data["publisher_teacher_verified"] is False


@pytest.mark.asyncio
async def test_detail_not_found(client: AsyncClient, seed: dict) -> None:
    response = await client.get("/api/v1/edu-listings/999999")

    assert response.status_code == 404


# ── 发布与认证前置校验 ──────────────────────────────────────────────


@pytest.mark.asyncio
async def test_publish_tutor_requires_education_cert(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    response = await auth_client.post(
        "/api/v1/edu-listings",
        json={"listing_type": "tutor", "title": "数学家教"},
    )

    assert response.status_code == 400
    assert "学历认证" in response.json()["detail"]
    assert (await db_session.execute(select(EduListing))).scalar_one_or_none() is None


@pytest.mark.asyncio
async def test_publish_training_succeeds_with_teacher_cert(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_cert(db_session, USER_ID, "teacher", "verified")

    response = await auth_client.post(
        "/api/v1/edu-listings",
        json={"listing_type": "training", "title": "物理冲刺班", "price": "3800.00"},
    )

    assert response.status_code == 201
    data = response.json()
    assert data["status"] == EduListingStatus.PENDING.value
    assert data["view_count"] == 0
    assert Decimal(str(data["price"])) == Decimal("3800.00")


@pytest.mark.asyncio
async def test_publish_demand_accepts_verified_real_name(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_cert(db_session, USER_ID, "real_name", "verified")

    response = await auth_client.post(
        "/api/v1/edu-listings",
        json={"listing_type": "demand", "title": "求化学家教"},
    )

    assert response.status_code == 201


@pytest.mark.asyncio
async def test_publish_pending_cert_is_rejected(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_cert(db_session, USER_ID, "education", "pending")

    response = await auth_client.post(
        "/api/v1/edu-listings",
        json={"listing_type": "tutor", "title": "数学家教"},
    )

    assert response.status_code == 400


@pytest.mark.asyncio
async def test_publish_without_login_is_rejected(client: AsyncClient, seed: dict) -> None:
    response = await client.post(
        "/api/v1/edu-listings",
        json={"listing_type": "demand", "title": "求教"},
    )

    assert response.status_code == 401


@pytest.mark.asyncio
async def test_publish_rejects_more_than_three_images(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_cert(db_session, USER_ID, "real_name", "approved")

    response = await auth_client.post(
        "/api/v1/edu-listings",
        json={
            "listing_type": "demand",
            "title": "求教",
            "images": ["https://e.com/%d.jpg" % i for i in range(4)],
        },
    )

    assert response.status_code == 422


@pytest.mark.asyncio
async def test_publish_rejects_invalid_listing_type(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    response = await auth_client.post(
        "/api/v1/edu-listings",
        json={"listing_type": "unknown", "title": "x"},
    )

    assert response.status_code == 422


# ── 我的发布 ────────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_mine_includes_all_own_statuses(
    auth_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session, user_id=USER_ID, title="A", status=EduListingStatus.APPROVED.value)
    await _add_listing(db_session, user_id=USER_ID, title="B", status=EduListingStatus.PENDING.value)
    await _add_listing(
        db_session, user_id=USER_ID, title="C",
        status=EduListingStatus.REJECTED.value, reject_reason="含广告",
    )
    await _add_listing(db_session, user_id=OTHER_USER_ID, title="别人的")

    response = await auth_client.get("/api/v1/edu-listings/mine")

    data = response.json()
    assert data["total"] == 3
    reasons = {item["title"]: item["reject_reason"] for item in data["items"]}
    assert reasons["C"] == "含广告"
    assert "别人的" not in reasons


@pytest.mark.asyncio
async def test_mine_without_login_is_rejected(client: AsyncClient, seed: dict) -> None:
    response = await client.get("/api/v1/edu-listings/mine")

    assert response.status_code == 401
