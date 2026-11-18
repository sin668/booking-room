"""app-cs-edu-follow：C 端详情 creator_username 与供需关注（follow_type=listing）。"""

import uuid

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.course import Course
from app.models.edu_listing import EduListing
from app.models.room_follow import RoomFollow
from app.models.study_room import StudyRoom
from app.models.user import User
from app.services import room_follow_service, study_room_service, training_service

USER_ID = uuid.UUID("33333333-3333-3333-3333-333333333333")
CREATOR_ID = uuid.UUID("44444444-4444-4444-4444-444444444444")


@pytest.fixture
async def seed_user(db_session: AsyncSession) -> User:
    user = User(
        id=USER_ID,
        phone="13900139033",
        nickname="客服关注测试用户",
        password_hash="hashed",
        username="cs_edu_follow_user",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def seed_creator(db_session: AsyncSession) -> User:
    user = User(
        id=CREATOR_ID,
        phone="13900139044",
        nickname="创建人管理员",
        password_hash="hashed",
        username="cs_edu_follow_creator",
    )
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.fixture
async def seed_room(db_session: AsyncSession, seed_creator: User) -> StudyRoom:
    room = StudyRoom(
        name="客服测试自习室",
        address="测试街 1 号",
        status="open",
        min_price=10,
        created_by=CREATOR_ID,
    )
    db_session.add(room)
    await db_session.flush()
    return room


@pytest.fixture
async def seed_legacy_room(db_session: AsyncSession) -> StudyRoom:
    room = StudyRoom(
        name="存量自习室",
        address="测试街 2 号",
        status="open",
        min_price=10,
    )
    db_session.add(room)
    await db_session.flush()
    return room


@pytest.fixture
async def seed_course(db_session: AsyncSession, seed_room: StudyRoom) -> Course:
    course = Course(
        name="客服测试课程",
        room_id=seed_room.id,
        category="math",
        status="active",
    )
    db_session.add(course)
    await db_session.flush()
    return course


@pytest.fixture
async def seed_listing(db_session: AsyncSession, seed_user: User) -> EduListing:
    listing = EduListing(
        user_id=USER_ID,
        listing_type="tutor",
        title="数学家教",
        subject="math",
        price=100,
        price_unit="元/小时",
        area="天河区",
        description="一对一辅导",
        images=["https://example.com/a.jpg"],
        status="approved",
        city_id=1,
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


@pytest.fixture
async def seed_offline_listing(db_session: AsyncSession, seed_user: User) -> EduListing:
    listing = EduListing(
        user_id=USER_ID,
        listing_type="demand",
        title="已下架求教",
        status="offline",
    )
    db_session.add(listing)
    await db_session.flush()
    return listing


# ── creator_username ─────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_room_detail_creator_username(
    db_session: AsyncSession, seed_room: StudyRoom
) -> None:
    item = await study_room_service.get_study_room(db_session, seed_room.id)
    assert item.creator_username == CREATOR_ID.hex


@pytest.mark.asyncio
async def test_room_detail_creator_username_null_for_legacy(
    db_session: AsyncSession, seed_legacy_room: StudyRoom
) -> None:
    item = await study_room_service.get_study_room(db_session, seed_legacy_room.id)
    assert item.creator_username is None


@pytest.mark.asyncio
async def test_course_detail_creator_username_from_room(
    db_session: AsyncSession, seed_course: Course
) -> None:
    detail = await training_service.get_course_detail(db_session, seed_course.id)
    assert detail is not None
    assert detail.creator_username == CREATOR_ID.hex


@pytest.mark.asyncio
async def test_course_detail_creator_username_null_for_legacy_room(
    db_session: AsyncSession, seed_legacy_room: StudyRoom
) -> None:
    course = Course(
        name="存量室课程",
        room_id=seed_legacy_room.id,
        category="math",
        status="active",
    )
    db_session.add(course)
    await db_session.flush()
    detail = await training_service.get_course_detail(db_session, course.id)
    assert detail is not None
    assert detail.creator_username is None


# ── listing 关注 ─────────────────────────────────────────────────────


@pytest.mark.asyncio
async def test_follow_listing_created(
    db_session: AsyncSession, seed_user: User, seed_listing: EduListing
) -> None:
    item, created = await room_follow_service.follow_room(
        db_session, USER_ID, seed_listing.id, follow_type="listing"
    )
    assert created is True
    assert item.id == seed_listing.id
    assert item.room_type == "listing"
    assert item.name == "数学家教"
    assert item.cover_image == "https://example.com/a.jpg"
    assert item.address == "天河区"
    assert float(item.min_price) == 100.0


@pytest.mark.asyncio
async def test_follow_listing_idempotent(
    db_session: AsyncSession, seed_user: User, seed_listing: EduListing
) -> None:
    await room_follow_service.follow_room(
        db_session, USER_ID, seed_listing.id, follow_type="listing"
    )
    _, created = await room_follow_service.follow_room(
        db_session, USER_ID, seed_listing.id, follow_type="listing"
    )
    assert created is False


@pytest.mark.asyncio
async def test_follow_listing_not_approved_raises(
    db_session: AsyncSession, seed_user: User, seed_offline_listing: EduListing
) -> None:
    with pytest.raises(ValueError):
        await room_follow_service.follow_room(
            db_session, USER_ID, seed_offline_listing.id, follow_type="listing"
        )


@pytest.mark.asyncio
async def test_follow_listing_missing_raises(
    db_session: AsyncSession, seed_user: User
) -> None:
    with pytest.raises(ValueError):
        await room_follow_service.follow_room(
            db_session, USER_ID, 999999, follow_type="listing"
        )


@pytest.mark.asyncio
async def test_unfollow_listing(
    db_session: AsyncSession, seed_user: User, seed_listing: EduListing
) -> None:
    await room_follow_service.follow_room(
        db_session, USER_ID, seed_listing.id, follow_type="listing"
    )
    await room_follow_service.unfollow_room(
        db_session, USER_ID, seed_listing.id, follow_type="listing"
    )
    result = await room_follow_service.list_followed_rooms(
        db_session, USER_ID, follow_type="listing"
    )
    assert result.total == 0


@pytest.mark.asyncio
async def test_list_listing_only_approved(
    db_session: AsyncSession,
    seed_user: User,
    seed_listing: EduListing,
    seed_offline_listing: EduListing,
) -> None:
    db_session.add(
        RoomFollow(user_id=USER_ID, room_id=seed_listing.id, follow_type="listing")
    )
    db_session.add(
        RoomFollow(user_id=USER_ID, room_id=seed_offline_listing.id, follow_type="listing")
    )
    await db_session.flush()
    result = await room_follow_service.list_followed_rooms(
        db_session, USER_ID, follow_type="listing"
    )
    assert result.total == 1
    assert result.items[0].id == seed_listing.id
    assert result.items[0].room_type == "listing"


@pytest.mark.asyncio
async def test_list_listing_city_filter(
    db_session: AsyncSession, seed_user: User, seed_listing: EduListing
) -> None:
    no_city = EduListing(
        user_id=USER_ID,
        listing_type="training",
        title="无城市培训班",
        status="approved",
    )
    other_city = EduListing(
        user_id=USER_ID,
        listing_type="training",
        title="其他城市培训班",
        status="approved",
        city_id=2,
    )
    db_session.add_all([no_city, other_city])
    await db_session.flush()
    for listing in (seed_listing, no_city, other_city):
        db_session.add(
            RoomFollow(user_id=USER_ID, room_id=listing.id, follow_type="listing")
        )
    await db_session.flush()

    result = await room_follow_service.list_followed_rooms(
        db_session, USER_ID, follow_type="listing", city_id=1
    )
    assert {item.id for item in result.items} == {seed_listing.id, no_city.id}