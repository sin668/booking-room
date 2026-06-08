from datetime import datetime, timedelta
from decimal import Decimal

import pytest
from pydantic import ValidationError
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.activity import Activity, ActivityCoupon
from app.models.coupon import Coupon, UserCoupon
from app.schemas.coupon_admin import AdminCouponCreate
from app.services import admin_coupon_service


def _coupon_data(**overrides):
    now = datetime.now()
    data = {
        "name": "满100减20",
        "description": "测试卡券",
        "type": "threshold_amount_off",
        "discount_amount": Decimal("20.00"),
        "discount_percent": None,
        "min_order_amount": Decimal("100.00"),
        "scope": "all",
        "seat_zone": None,
        "valid_from": now - timedelta(days=1),
        "expires_at": now + timedelta(days=30),
        "is_active": True,
    }
    data.update(overrides)
    return data


async def _create_coupon(db: AsyncSession, **overrides) -> Coupon:
    coupon = Coupon(**_coupon_data(**overrides))
    db.add(coupon)
    await db.flush()
    await db.refresh(coupon)
    return coupon


class TestAdminCouponService:
    @pytest.mark.asyncio
    async def test_create_threshold_coupon_success(self, db_session: AsyncSession):
        result = await admin_coupon_service.create_coupon(db_session, _coupon_data())

        assert result.id
        assert result.type == "threshold_amount_off"
        assert result.discount_amount == Decimal("20.00")

    @pytest.mark.asyncio
    async def test_create_threshold_coupon_requires_discount_amount(self, db_session: AsyncSession):
        with pytest.raises(admin_coupon_service.AdminCouponError, match="优惠金额"):
            await admin_coupon_service.create_coupon(
                db_session,
                _coupon_data(discount_amount=None),
            )

    @pytest.mark.asyncio
    async def test_create_percentage_coupon_success(self, db_session: AsyncSession):
        result = await admin_coupon_service.create_coupon(
            db_session,
            _coupon_data(
                type="percentage_off",
                discount_amount=None,
                discount_percent=80,
                min_order_amount=Decimal("0.00"),
            ),
        )

        assert result.type == "percentage_off"
        assert result.discount_percent == 80

    def test_percentage_coupon_rejects_out_of_range_percent(self):
        with pytest.raises(ValidationError):
            AdminCouponCreate(
                **_coupon_data(
                    type="percentage_off",
                    discount_amount=None,
                    discount_percent=100,
                    min_order_amount=Decimal("0.00"),
                )
            )

    @pytest.mark.asyncio
    async def test_update_linked_coupon_type_rejected(self, db_session: AsyncSession):
        coupon = await _create_coupon(db_session)
        activity = Activity(title="活动")
        db_session.add(activity)
        await db_session.flush()
        db_session.add(
            ActivityCoupon(
                activity_id=activity.id,
                coupon_id=coupon.id,
                total_quantity=10,
                claimed_quantity=0,
                per_user_limit=1,
            )
        )
        await db_session.flush()

        with pytest.raises(admin_coupon_service.AdminCouponError, match="禁止修改类型"):
            await admin_coupon_service.update_coupon(
                db_session,
                coupon.id,
                {"type": "amount_off", "discount_amount": Decimal("10.00")},
            )

    @pytest.mark.asyncio
    async def test_enable_expired_coupon_rejected(self, db_session: AsyncSession):
        coupon = await _create_coupon(
            db_session,
            is_active=False,
            valid_from=datetime.now() - timedelta(days=30),
            expires_at=datetime.now() - timedelta(days=1),
        )

        with pytest.raises(admin_coupon_service.AdminCouponError, match="已过期"):
            await admin_coupon_service.toggle_status(db_session, coupon.id, True)

    @pytest.mark.asyncio
    async def test_delete_linked_coupon_rejected(self, db_session: AsyncSession):
        coupon = await _create_coupon(db_session)
        db_session.add(UserCoupon(user_id="user-001", coupon_id=coupon.id, status="available"))
        await db_session.flush()

        with pytest.raises(admin_coupon_service.AdminCouponError, match="禁止删除"):
            await admin_coupon_service.delete_coupon(db_session, coupon.id)
