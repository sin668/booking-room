"""Seed data for homepage display features.

Run with: python -m app.services.seed_data
Requires DATABASE_URL env var to be set.
"""

import asyncio
from datetime import datetime, timedelta, timezone
from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import async_session
from app.models.activity import Activity
from app.models.banner import Banner
from app.models.coupon import Coupon, UserCoupon
from app.models.notification import Notification, NotificationPreference
from app.models.study_room import StudyRoom
from app.models.user import User

CHINA_TIMEZONE = timezone(timedelta(hours=8))


def _china_now_naive() -> datetime:
    """Return China local time for timezone-naive database DateTime columns."""
    return datetime.now(CHINA_TIMEZONE).replace(tzinfo=None)


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

SEED_COUPONS = [
    {
        "name": "满20减3",
        "description": "全场通用",
        "type": "threshold_amount_off",
        "discount_amount": Decimal("3.00"),
        "discount_percent": None,
        "min_order_amount": Decimal("20.00"),
        "scope": "all",
        "seat_zone": None,
    },
    {
        "name": "新用户首单立减20",
        "description": "限首次预约",
        "type": "amount_off",
        "discount_amount": Decimal("20.00"),
        "discount_percent": None,
        "min_order_amount": Decimal("0.00"),
        "scope": "first_booking",
        "seat_zone": None,
    },
    {
        "name": "VIP专享8折",
        "description": "限VIP座位",
        "type": "percentage_off",
        "discount_amount": None,
        "discount_percent": 80,
        "min_order_amount": Decimal("0.00"),
        "scope": "seat_zone",
        "seat_zone": "vip",
    },
]

DEMO_APP_USER = {
    "phone": "13900000001",
    "nickname": "消息演示用户",
    "username": "notify_demo_user",
    "password_hash": "seed-demo-user-not-for-login",
    "user_type": "app",
    "status": "active",
}

SEED_NOTIFICATIONS = [
    {
        "type": "booking",
        "title": "预约成功通知",
        "content": "您已成功预约安静自习室·油城店 A区 08 号座位，请按时到店学习。",
        "target_url": "/pages/orders/index",
        "target_type": "booking",
        "target_id": "seed-booking-success",
        "minutes_ago": 8,
        "is_read": False,
    },
    {
        "type": "booking",
        "title": "预约开始提醒",
        "content": "您的预约将在 15 分钟后开始，请提前准备学习用品并到店签到。",
        "target_url": "/pages/qrcode/index",
        "target_type": "arrival",
        "target_id": "seed-booking-arrival",
        "minutes_ago": 36,
        "is_read": False,
    },
    {
        "type": "booking",
        "title": "预约变更提醒",
        "content": "您预约的座位已完成变更，新的座位信息可在订单列表中查看。",
        "target_url": "/pages/orders/index",
        "target_type": "booking",
        "target_id": "seed-booking-change",
        "minutes_ago": 160,
        "is_read": True,
    },
    {
        "type": "activity",
        "title": "早起鸟计划上线",
        "content": "早 8 点前到店签到可获得额外学习积分，本周活动名额有限。",
        "target_url": "/pages/index/index",
        "target_type": "activity",
        "target_id": "seed-activity-early-bird",
        "minutes_ago": 18,
        "is_read": False,
    },
    {
        "type": "activity",
        "title": "周末冲刺班报名中",
        "content": "周末 8 小时沉浸学习挑战开启，连续打卡可领取优惠券。",
        "target_url": "/pages/index/index",
        "target_type": "activity",
        "target_id": "seed-activity-weekend",
        "minutes_ago": 240,
        "is_read": False,
    },
    {
        "type": "activity",
        "title": "充值福利到账",
        "content": "充值满 100 送 30 活动进行中，优惠可用于后续预约订单。",
        "target_url": "/pages/recharge/index",
        "target_type": "activity",
        "target_id": "seed-activity-recharge",
        "minutes_ago": 720,
        "is_read": True,
    },
    {
        "type": "report",
        "title": "本周学习报告已生成",
        "content": "您本周累计学习 18.5 小时，专注力超过 82% 的同城用户。",
        "target_url": "/pages/study-record/index",
        "target_type": "report",
        "target_id": "seed-report-weekly",
        "minutes_ago": 52,
        "is_read": False,
    },
    {
        "type": "report",
        "title": "连续学习成就达成",
        "content": "您已连续 5 天完成学习打卡，继续保持稳定节奏。",
        "target_url": "/pages/study-record/index",
        "target_type": "report",
        "target_id": "seed-report-streak",
        "minutes_ago": 300,
        "is_read": False,
    },
    {
        "type": "report",
        "title": "月度学习趋势提醒",
        "content": "本月晚间学习时长占比提升，建议继续固定高效时间段。",
        "target_url": "/pages/study-record/index",
        "target_type": "report",
        "target_id": "seed-report-monthly",
        "minutes_ago": 1080,
        "is_read": True,
    },
    {
        "type": "arrival",
        "title": "到店签到提醒",
        "content": "检测到您已接近门店，请打开我的学习码完成到店核销。",
        "target_url": "/pages/qrcode/index",
        "target_type": "arrival",
        "target_id": "seed-arrival-checkin",
        "minutes_ago": 5,
        "is_read": False,
    },
    {
        "type": "arrival",
        "title": "学习码即将过期",
        "content": "当前学习码即将刷新，如需核销请在页面展示最新二维码。",
        "target_url": "/pages/qrcode/index",
        "target_type": "arrival",
        "target_id": "seed-arrival-qrcode",
        "minutes_ago": 84,
        "is_read": False,
    },
    {
        "type": "arrival",
        "title": "离店核销完成",
        "content": "本次学习已完成离店核销，学习时长已计入记录。",
        "target_url": "/pages/study-record/index",
        "target_type": "arrival",
        "target_id": "seed-arrival-finished",
        "minutes_ago": 420,
        "is_read": True,
    },
]


async def seed_coupons(session: AsyncSession) -> None:
    now = _china_now_naive()
    valid_from = now - timedelta(days=1)
    expires_at = now + timedelta(days=90)
    coupons_by_name: dict[str, Coupon] = {}

    for coupon_data in SEED_COUPONS:
        existing = await session.execute(
            select(Coupon).where(Coupon.name == coupon_data["name"])
        )
        coupon = existing.scalar_one_or_none()
        if coupon is None:
            coupon = Coupon(
                **coupon_data,
                valid_from=valid_from,
                expires_at=expires_at,
                is_active=True,
            )
            session.add(coupon)
            await session.flush()
            print(f"  + Coupon: {coupon.name}")
        coupons_by_name[coupon.name] = coupon

    users = (await session.execute(select(User).where(User.status == "active"))).scalars().all()
    for user in users:
        for coupon in coupons_by_name.values():
            existing_user_coupon = await session.execute(
                select(UserCoupon).where(
                    UserCoupon.user_id == str(user.id),
                    UserCoupon.coupon_id == coupon.id,
                )
            )
            if existing_user_coupon.scalar_one_or_none() is None:
                session.add(
                    UserCoupon(
                        user_id=str(user.id),
                        coupon_id=coupon.id,
                        status="available",
                    )
                )
                print(f"  + UserCoupon: {coupon.name} -> {user.phone}")


async def _get_or_create_demo_user(session: AsyncSession) -> User:
    existing = await session.execute(
        select(User).where(User.username == DEMO_APP_USER["username"])
    )
    user = existing.scalar_one_or_none()
    if user is not None:
        user.status = "active"
        return user

    user = User(**DEMO_APP_USER)
    session.add(user)
    await session.flush()
    print(f"  + DemoUser: {user.nickname} ({user.username})")
    return user


async def _seed_notification_preferences(session: AsyncSession, user: User) -> None:
    existing = await session.execute(
        select(NotificationPreference).where(NotificationPreference.user_id == user.id)
    )
    if existing.scalar_one_or_none() is None:
        session.add(NotificationPreference(user_id=user.id))
        print(f"  + NotificationPreference: {user.username}")


async def seed_notifications(session: AsyncSession) -> None:
    users = (
        await session.execute(
            select(User).where(
                User.user_type == "app",
                User.status == "active",
            )
        )
    ).scalars().all()
    if not users:
        users = [await _get_or_create_demo_user(session)]

    now = _china_now_naive()
    for user in users:
        await _seed_notification_preferences(session, user)
        for item in SEED_NOTIFICATIONS:
            existing = await session.execute(
                select(Notification).where(
                    Notification.user_id == user.id,
                    Notification.type == item["type"],
                    Notification.title == item["title"],
                )
            )
            if existing.scalar_one_or_none() is not None:
                continue

            created_at = now - timedelta(minutes=item["minutes_ago"])
            session.add(
                Notification(
                    user_id=user.id,
                    type=item["type"],
                    title=item["title"],
                    content=item["content"],
                    target_url=item["target_url"],
                    target_type=item["target_type"],
                    target_id=item["target_id"],
                    is_read=item["is_read"],
                    created_at=created_at,
                    read_at=created_at + timedelta(minutes=2) if item["is_read"] else None,
                )
            )
            print(f"  + Notification: {item['type']} / {item['title']} -> {user.username}")


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

        await seed_coupons(session)
        await seed_notifications(session)

        await session.commit()
        print("Seed data complete.")


if __name__ == "__main__":
    asyncio.run(seed_all())
