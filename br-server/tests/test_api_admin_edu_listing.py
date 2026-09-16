"""后台教培供需审核测试：筛选 / 关键词 / 通过 / 拒绝必填理由 / 下架 / 权限 403 /
审核时间 naive。"""

import uuid
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, get_current_admin
from app.domain.edu_listing_status import EduListingStatus
from app.models.edu_listing import EduListing
from app.models.user import User
from app.models.user_identity_verification import UserIdentityVerification

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
ADMIN_ID = uuid.UUID("99999999-9999-9999-9999-999999999999")

AUDIT_PERMISSIONS = {"edu:listing:view", "edu:listing:audit"}


def _admin_context(codes: set[str]) -> AdminContext:
    return AdminContext(
        admin_id=ADMIN_ID,
        username="moderator",
        is_super_admin=False,
        permission_codes=codes,
        menu_ids=set(),
    )


@pytest.fixture
async def audit_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_admin] = lambda: _admin_context(AUDIT_PERMISSIONS)
    yield client
    app.dependency_overrides[get_current_admin] = lambda: None


@pytest.fixture
async def view_only_client(client: AsyncClient):
    app = client._transport.app
    app.dependency_overrides[get_current_admin] = lambda: _admin_context({"edu:listing:view"})
    yield client
    app.dependency_overrides[get_current_admin] = lambda: None


@pytest.fixture
async def seed(db_session: AsyncSession) -> dict:
    db_session.add(
        User(id=USER_ID, phone="13800138001", nickname="小明", password_hash="h", username="u1")
    )
    db_session.add(
        UserIdentityVerification(user_id=USER_ID, verification_type="education", status="approved")
    )
    await db_session.flush()
    return {"user_id": USER_ID}


async def _add_listing(db_session: AsyncSession, **overrides) -> EduListing:
    defaults = dict(
        user_id=USER_ID,
        listing_type="tutor",
        title="初中数学家教",
        status=EduListingStatus.PENDING.value,
        view_count=0,
    )
    defaults.update(overrides)
    listing = EduListing(**defaults)
    db_session.add(listing)
    await db_session.flush()
    return listing


@pytest.mark.asyncio
async def test_admin_list_filters_by_status(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session, title="待审", status=EduListingStatus.PENDING.value)
    await _add_listing(db_session, title="已过", status=EduListingStatus.APPROVED.value)

    response = await audit_client.get("/api/v1/admin/edu-listings?status=pending")

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "待审"


@pytest.mark.asyncio
async def test_admin_list_keyword_matches_title(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session, title="高中数学冲刺")
    await _add_listing(db_session, title="少儿英语陪练")

    response = await audit_client.get("/api/v1/admin/edu-listings?keyword=数学")

    data = response.json()
    assert data["total"] == 1
    assert data["items"][0]["title"] == "高中数学冲刺"


@pytest.mark.asyncio
async def test_admin_list_carries_publisher_and_cert_summary(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    await _add_listing(db_session)

    response = await audit_client.get("/api/v1/admin/edu-listings")

    item = response.json()["items"][0]
    assert item["publisher_nickname"] == "小明"
    assert item["publisher_education_verified"] is True


@pytest.mark.asyncio
async def test_approve_makes_listing_visible_in_plaza(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session, status=EduListingStatus.PENDING.value)

    audit = await audit_client.patch(
        f"/api/v1/admin/edu-listings/{listing.id}/status", json={"status": "approved"}
    )
    assert audit.status_code == 200
    assert audit.json()["status"] == EduListingStatus.APPROVED.value
    assert audit.json()["reviewed_by"] == str(ADMIN_ID)

    plaza = await audit_client.get("/api/v1/edu-listings")
    assert plaza.json()["total"] == 1


@pytest.mark.asyncio
async def test_reject_requires_reason(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session)

    response = await audit_client.patch(
        f"/api/v1/admin/edu-listings/{listing.id}/status", json={"status": "rejected"}
    )

    assert response.status_code == 422
    refreshed = (
        await db_session.execute(select(EduListing).where(EduListing.id == listing.id))
    ).scalar_one()
    assert refreshed.status == EduListingStatus.PENDING.value


@pytest.mark.asyncio
async def test_reject_with_reason_persists(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session)

    response = await audit_client.patch(
        f"/api/v1/admin/edu-listings/{listing.id}/status",
        json={"status": "rejected", "reject_reason": "信息不实"},
    )

    assert response.status_code == 200
    assert response.json()["reject_reason"] == "信息不实"


@pytest.mark.asyncio
async def test_offline_hides_approved_listing(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session, status=EduListingStatus.APPROVED.value)

    response = await audit_client.patch(
        f"/api/v1/admin/edu-listings/{listing.id}/status", json={"status": "offline"}
    )
    assert response.json()["status"] == EduListingStatus.OFFLINE.value

    plaza = await audit_client.get("/api/v1/edu-listings")
    assert plaza.json()["total"] == 0


@pytest.mark.asyncio
async def test_reviewed_at_is_naive(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session)

    await audit_client.patch(
        f"/api/v1/admin/edu-listings/{listing.id}/status", json={"status": "approved"}
    )

    refreshed = (
        await db_session.execute(select(EduListing).where(EduListing.id == listing.id))
    ).scalar_one()
    assert refreshed.reviewed_at is not None
    assert refreshed.reviewed_at.tzinfo is None


@pytest.mark.asyncio
async def test_audit_without_permission_is_forbidden(
    view_only_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session)

    response = await view_only_client.patch(
        f"/api/v1/admin/edu-listings/{listing.id}/status", json={"status": "approved"}
    )

    assert response.status_code == 403


@pytest.mark.asyncio
async def test_update_status_not_found(audit_client: AsyncClient, seed: dict) -> None:
    response = await audit_client.patch(
        "/api/v1/admin/edu-listings/999999/status", json={"status": "approved"}
    )

    assert response.status_code == 404


@pytest.mark.asyncio
async def test_invalid_status_is_rejected(
    audit_client: AsyncClient, db_session: AsyncSession, seed: dict
) -> None:
    listing = await _add_listing(db_session)

    response = await audit_client.patch(
        f"/api/v1/admin/edu-listings/{listing.id}/status", json={"status": "pending"}
    )

    assert response.status_code == 422
