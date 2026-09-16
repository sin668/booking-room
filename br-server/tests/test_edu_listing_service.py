"""教培供需 service 层单元测试：排序口径 / 认证状态批量映射 / 组装空输入。"""

import uuid
from decimal import Decimal

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.edu_listing_status import EduListingStatus
from app.models.edu_listing import EduListing
from app.models.user import User
from app.models.user_identity_verification import UserIdentityVerification
from app.services import edu_listing_service as svc

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
OTHER_USER_ID = uuid.UUID("22222222-2222-2222-2222-222222222222")


async def _seed_users(db_session: AsyncSession) -> None:
    db_session.add_all(
        [
            User(id=USER_ID, phone="13800138001", nickname="小明", password_hash="h", username="u1"),
            User(id=OTHER_USER_ID, phone="13800138002", nickname="小红", password_hash="h", username="u2"),
        ]
    )
    await db_session.flush()


@pytest.mark.asyncio
async def test_assemble_items_empty_returns_empty(db_session: AsyncSession) -> None:
    assert await svc.assemble_items(db_session, []) == []


@pytest.mark.asyncio
async def test_certification_map_marks_passed_types(db_session: AsyncSession) -> None:
    await _seed_users(db_session)
    db_session.add_all(
        [
            UserIdentityVerification(user_id=USER_ID, verification_type="education", status="approved"),
            UserIdentityVerification(user_id=USER_ID, verification_type="teacher", status="verified"),
            UserIdentityVerification(user_id=OTHER_USER_ID, verification_type="education", status="pending"),
        ]
    )
    await db_session.flush()

    cert_map = await svc._load_certification_map(db_session, {USER_ID, OTHER_USER_ID})

    assert cert_map[USER_ID] == {"education": True, "teacher": True}
    assert cert_map[OTHER_USER_ID] == {"education": False, "teacher": False}


@pytest.mark.asyncio
async def test_list_orders_price_ascending_with_nulls_last(db_session: AsyncSession) -> None:
    await _seed_users(db_session)
    db_session.add_all(
        [
            EduListing(user_id=USER_ID, listing_type="tutor", title="贵", price=Decimal("300"),
                       status=EduListingStatus.APPROVED.value, view_count=0),
            EduListing(user_id=USER_ID, listing_type="tutor", title="便宜", price=Decimal("100"),
                       status=EduListingStatus.APPROVED.value, view_count=0),
            EduListing(user_id=USER_ID, listing_type="demand", title="无价", price=None,
                       status=EduListingStatus.APPROVED.value, view_count=0),
        ]
    )
    await db_session.flush()

    result = await svc.list_edu_listings(db_session, sort="price_asc")

    titles = [item.title for item in result.items]
    assert titles == ["便宜", "贵", "无价"]


@pytest.mark.asyncio
async def test_list_excludes_non_approved(db_session: AsyncSession) -> None:
    await _seed_users(db_session)
    db_session.add_all(
        [
            EduListing(user_id=USER_ID, listing_type="tutor", title="过",
                       status=EduListingStatus.APPROVED.value, view_count=0),
            EduListing(user_id=USER_ID, listing_type="tutor", title="待",
                       status=EduListingStatus.PENDING.value, view_count=0),
        ]
    )
    await db_session.flush()

    result = await svc.list_edu_listings(db_session)

    assert result.total == 1
    assert result.items[0].title == "过"
