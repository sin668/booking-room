"""VIP 会员升级逻辑单元测试"""
import pytest
from datetime import datetime
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

from app.models.coupon import Coupon, UserCoupon
from app.services.coupon_service import _check_scope
from app.services.wallet_service import WalletService


def _make_user(membership_level="none", balance=Decimal("0"), nickname="测试用户"):
    user = MagicMock()
    user.membership_level = membership_level
    user.balance = balance
    user.id = "user-uuid-001"
    user.nickname = nickname
    return user


class TestProcessVipUpgrade:
    """VIP 升级条件判断测试"""

    @pytest.mark.asyncio
    async def test_recharge_100_none_user_upgrades(self):
        """充值100元 + membership_level=none → 升级"""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        result = await WalletService._process_vip_upgrade(
            db, _make_user(), Decimal("100")
        )

        assert result.upgraded is True
        assert result.user.membership_level == "vip"
        assert result.vip_coupon is not None

    @pytest.mark.asyncio
    async def test_recharge_50_none_user_no_upgrade(self):
        """充值50元 + membership_level=none → 不升级"""
        db = MagicMock()
        result = await WalletService._process_vip_upgrade(
            db, _make_user(), Decimal("50")
        )
        assert result.upgraded is False
        assert result.user.membership_level == "none"

    @pytest.mark.asyncio
    async def test_already_vip_no_upgrade(self):
        """已是VIP → 不升级"""
        db = MagicMock()
        result = await WalletService._process_vip_upgrade(
            db, _make_user(membership_level="vip"), Decimal("100")
        )
        assert result.upgraded is False
        assert result.user.membership_level == "vip"

    @pytest.mark.asyncio
    async def test_svip_user_no_downgrade(self):
        """SVIP用户充值 → 不降级"""
        db = MagicMock()
        result = await WalletService._process_vip_upgrade(
            db, _make_user(membership_level="svip"), Decimal("100")
        )
        assert result.upgraded is False
        assert result.user.membership_level == "svip"

    @pytest.mark.asyncio
    async def test_recharge_150_upgrades(self):
        """充值150元也触发升级"""
        db = MagicMock()
        db.flush = AsyncMock()
        result = await WalletService._process_vip_upgrade(
            db, _make_user(), Decimal("150")
        )
        assert result.upgraded is True
        assert result.user.membership_level == "vip"

    @pytest.mark.asyncio
    async def test_welcome_coupon_created_with_correct_fields(self):
        """赠券字段正确：scope=vip_only, type=percentage_off, discount_percent=80"""
        db = MagicMock()
        db.add = MagicMock()
        db.flush = AsyncMock()

        result = await WalletService._process_vip_upgrade(
            db, _make_user(nickname="小明"), Decimal("100")
        )

        assert result.upgraded is True
        assert db.add.call_count == 2  # Coupon + UserCoupon
        coupon = db.add.call_args_list[0][0][0]
        assert coupon.scope == "vip_only"
        assert coupon.type == "percentage_off"
        assert coupon.discount_percent == 80
        assert coupon.min_order_amount == Decimal("0")
        assert coupon.is_active is True
        assert "小明" in coupon.name


class TestVIPScopeFilter:
    def test_vip_only_coupon_for_vip_user(self):
        coupon = MagicMock(spec=Coupon)
        coupon.scope = "vip_only"
        user = MagicMock()
        user.membership_level = "vip"
        assert _check_scope(user, coupon) is True

    def test_vip_only_coupon_for_none_user(self):
        coupon = MagicMock(spec=Coupon)
        coupon.scope = "vip_only"
        user = MagicMock()
        user.membership_level = "none"
        assert _check_scope(user, coupon) is False

    def test_all_scope_for_any_user(self):
        coupon = MagicMock(spec=Coupon)
        coupon.scope = "all"
        user = MagicMock()
        user.membership_level = "none"
        assert _check_scope(user, coupon) is True
