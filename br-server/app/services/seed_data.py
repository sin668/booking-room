"""Seed data for homepage display features.

Run with: python -m app.services.seed_data
Requires DATABASE_URL env var to be set.
"""

import asyncio

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.activity import Activity
from app.models.banner import Banner
from app.models.study_room import StudyRoom

SEED_BANNERS = [
    Banner(
        image_url="https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=800&h=400&fit=crop",
        title="新用户首单立减20元",
        subtitle="限时优惠，先到先得",
        cta_text="立即领取",
        link_type="page",
        link_value="/pages/coupon/index",
        sort_order=1,
        is_active=True,
    ),
    Banner(
        image_url="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=800&h=400&fit=crop",
        title="充值100送30",
        subtitle="更多充值优惠等你来",
        cta_text="了解详情",
        link_type="page",
        link_value="/pages/recharge/index",
        sort_order=2,
        is_active=True,
    ),
]

SEED_ACTIVITIES = [
    Activity(
        title="沉浸式学习挑战赛",
        description="累计学习24小时赢好礼",
        cover_image="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=200&fit=crop",
        participant_count=326,
        sort_order=1,
        is_active=True,
    ),
    Activity(
        title="学霸训练营",
        description="每日打卡赢取学习基金",
        cover_image="https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400&h=200&fit=crop",
        participant_count=189,
        sort_order=2,
        is_active=True,
    ),
    Activity(
        title="周末冲刺班",
        description="周六日8小时高效学习",
        cover_image="https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=400&h=200&fit=crop",
        participant_count=512,
        sort_order=3,
        is_active=True,
    ),
    Activity(
        title="早起鸟计划",
        description="早8点前签到享折扣",
        cover_image="https://images.unsplash.com/photo-1497032628192-86f99bcd76bc?w=400&h=200&fit=crop",
        participant_count=278,
        sort_order=4,
        is_active=True,
    ),
]

SEED_STUDY_ROOMS = [
    StudyRoom(
        name="安静自习室·油城店",
        description="宽敞明亮的沉浸式自习空间，配备独立隔间和护眼灯",
        cover_image="https://images.unsplash.com/photo-1524995997946-a1c2e315a42f?w=400&h=300&fit=crop",
        address="茂名市茂南区油城三路88号",
        business_hours="07:00-23:00",
        status="open",
        min_price=8.00,
    ),
    StudyRoom(
        name="静谧书屋·电白店",
        description="安静舒适的阅读与学习空间，提供咖啡茶饮服务",
        cover_image="https://images.unsplash.com/photo-1481627834876-b7833e8f5570?w=400&h=300&fit=crop",
        address="茂名市电白区水东镇人民路166号",
        business_hours="08:00-22:00",
        status="open",
        min_price=10.00,
    ),
    StudyRoom(
        name="学霸空间·高州店",
        description="高端自习空间，独座位+空调+WiFi+充电，适合考研考公",
        cover_image="https://images.unsplash.com/photo-1503676260728-1c00da094a0b?w=400&h=300&fit=crop",
        address="茂名市高州市中山路56号",
        business_hours="06:30-23:30",
        status="open",
        min_price=12.00,
    ),
]


async def seed_all() -> None:
    async with async_session() as session:
        for banner in SEED_BANNERS:
            existing = await session.execute(
                select(Banner).where(Banner.title == banner.title)
            )
            if existing.scalar_one_or_none() is None:
                session.add(banner)
                print(f"  + Banner: {banner.title}")

        for activity in SEED_ACTIVITIES:
            existing = await session.execute(
                select(Activity).where(Activity.title == activity.title)
            )
            if existing.scalar_one_or_none() is None:
                session.add(activity)
                print(f"  + Activity: {activity.title}")

        for room in SEED_STUDY_ROOMS:
            existing = await session.execute(
                select(StudyRoom).where(StudyRoom.name == room.name)
            )
            if existing.scalar_one_or_none() is None:
                session.add(room)
                print(f"  + StudyRoom: {room.name}")

        await session.commit()
        print("Seed data complete.")


if __name__ == "__main__":
    asyncio.run(seed_all())
