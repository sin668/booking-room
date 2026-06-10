from datetime import datetime, timedelta
from decimal import Decimal
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, get_current_admin
from app.models.coupon import Coupon


def _payload(**overrides):
    now = datetime.now()
    data = {
        "name": "VIP专享8折券",
        "description": "VIP 用户可用",
        "type": "percentage_off",
        "discount_amount": None,
        "discount_percent": 80,
        "min_order_amount": "0.00",
        "scope": "vip_only",
        "seat_zone": None,
        "valid_from": (now - timedelta(days=1)).isoformat(),
        "expires_at": (now + timedelta(days=30)).isoformat(),
        "is_active": True,
    }
    data.update(overrides)
    return data


@pytest.fixture
def admin_headers():
    return {"X-Admin-Token": "test-admin-token"}


@pytest.fixture
async def seed_coupon(db_session: AsyncSession):
    coupon = Coupon(
        name="满100减20",
        description="测试卡券",
        type="threshold_amount_off",
        discount_amount=Decimal("20.00"),
        discount_percent=None,
        min_order_amount=Decimal("100.00"),
        scope="all",
        seat_zone=None,
        valid_from=datetime.now() - timedelta(days=1),
        expires_at=datetime.now() + timedelta(days=30),
        is_active=True,
    )
    db_session.add(coupon)
    await db_session.flush()
    await db_session.refresh(coupon)
    return coupon


class TestAdminCouponApi:
    @pytest.mark.asyncio
    async def test_no_token_returns_401(self, client: AsyncClient):
        from app.main import app

        del app.dependency_overrides[get_current_admin]
        try:
            resp = await client.get("/api/v1/admin/coupons")
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None

    @pytest.mark.asyncio
    async def test_missing_permission_returns_403(self, client: AsyncClient):
        from app.main import app

        app.dependency_overrides[get_current_admin] = lambda: AdminContext(
            admin_id=uuid.UUID("00000000-0000-0000-0000-000000000000"),
            username="limited-admin",
            is_super_admin=False,
            permission_codes=set(),
            menu_ids=set(),
        )
        try:
            resp = await client.get("/api/v1/admin/coupons")
            assert resp.status_code == 403
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None

    @pytest.mark.asyncio
    async def test_crud_flow(self, client: AsyncClient, admin_headers):
        create_resp = await client.post("/api/v1/admin/coupons", json=_payload(), headers=admin_headers)
        assert create_resp.status_code == 201
        created = create_resp.json()
        coupon_id = created["id"]
        assert created["scope"] == "vip_only"

        list_resp = await client.get("/api/v1/admin/coupons?keyword=VIP", headers=admin_headers)
        assert list_resp.status_code == 200
        assert list_resp.json()["total"] == 1

        get_resp = await client.get(f"/api/v1/admin/coupons/{coupon_id}", headers=admin_headers)
        assert get_resp.status_code == 200
        assert get_resp.json()["name"] == "VIP专享8折券"

        update_resp = await client.put(
            f"/api/v1/admin/coupons/{coupon_id}",
            json={"name": "VIP专享7折券", "discount_percent": 70},
            headers=admin_headers,
        )
        assert update_resp.status_code == 200
        assert update_resp.json()["discount_percent"] == 70

        status_resp = await client.patch(
            f"/api/v1/admin/coupons/{coupon_id}/status",
            json={"is_active": False},
            headers=admin_headers,
        )
        assert status_resp.status_code == 200
        assert status_resp.json()["is_active"] is False

        delete_resp = await client.delete(f"/api/v1/admin/coupons/{coupon_id}", headers=admin_headers)
        assert delete_resp.status_code == 204

        missing_resp = await client.get(f"/api/v1/admin/coupons/{coupon_id}", headers=admin_headers)
        assert missing_resp.status_code == 404

    @pytest.mark.asyncio
    async def test_create_invalid_coupon_returns_422(self, client: AsyncClient, admin_headers):
        resp = await client.post(
            "/api/v1/admin/coupons",
            json=_payload(type="threshold_amount_off", discount_amount=None, discount_percent=None),
            headers=admin_headers,
        )

        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_list_filters(self, client: AsyncClient, admin_headers, seed_coupon):
        resp = await client.get(
            "/api/v1/admin/coupons?type=threshold_amount_off&scope=all&is_active=true",
            headers=admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["total"] == 1
        assert data["items"][0]["id"] == seed_coupon.id

    @pytest.mark.asyncio
    async def test_list_filters_active_not_expired_and_orders_by_created_desc(
        self, client: AsyncClient, admin_headers, db_session: AsyncSession
    ):
        now = datetime.now()
        older_valid = Coupon(
            name="有效旧券",
            description="有效启用",
            type="amount_off",
            discount_amount=Decimal("10.00"),
            discount_percent=None,
            min_order_amount=Decimal("0.00"),
            scope="all",
            seat_zone=None,
            valid_from=now - timedelta(days=2),
            expires_at=now + timedelta(days=2),
            is_active=True,
            created_at=now - timedelta(hours=2),
        )
        future_valid = Coupon(
            name="未来开始券",
            description="未过期",
            type="amount_off",
            discount_amount=Decimal("12.00"),
            discount_percent=None,
            min_order_amount=Decimal("0.00"),
            scope="all",
            seat_zone=None,
            valid_from=now + timedelta(days=1),
            expires_at=now + timedelta(days=3),
            is_active=True,
            created_at=now - timedelta(minutes=90),
        )
        newer_valid = Coupon(
            name="有效新券",
            description="有效启用",
            type="amount_off",
            discount_amount=Decimal("15.00"),
            discount_percent=None,
            min_order_amount=Decimal("0.00"),
            scope="all",
            seat_zone=None,
            valid_from=now - timedelta(days=1),
            expires_at=now + timedelta(days=1),
            is_active=True,
            created_at=now - timedelta(hours=1),
        )
        expired = Coupon(
            name="过期券",
            description="已过期",
            type="amount_off",
            discount_amount=Decimal("20.00"),
            discount_percent=None,
            min_order_amount=Decimal("0.00"),
            scope="all",
            seat_zone=None,
            valid_from=now - timedelta(days=4),
            expires_at=now - timedelta(days=1),
            is_active=True,
            created_at=now,
        )
        inactive = Coupon(
            name="停用券",
            description="未启用",
            type="amount_off",
            discount_amount=Decimal("25.00"),
            discount_percent=None,
            min_order_amount=Decimal("0.00"),
            scope="all",
            seat_zone=None,
            valid_from=now - timedelta(days=1),
            expires_at=now + timedelta(days=1),
            is_active=False,
            created_at=now,
        )
        db_session.add_all([older_valid, future_valid, newer_valid, expired, inactive])
        await db_session.flush()

        resp = await client.get(
            "/api/v1/admin/coupons?is_active=true&valid_now=true",
            headers=admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert [item["name"] for item in data["items"]] == ["有效新券", "未来开始券", "有效旧券"]
