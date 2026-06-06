"""活动卡券后端能力测试。"""

import uuid
from datetime import datetime, timedelta, timezone
from decimal import Decimal

import pytest
from httpx import AsyncClient
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_optional_current_user_id
from app.models.activity import Activity, ActivityCoupon
from app.models.coupon import Coupon, UserCoupon
from app.services import activity_service

USER_ID = uuid.UUID("11111111-1111-1111-1111-111111111111")
NOW = datetime(2026, 6, 6, 10, 0, 0)


def _coupon(**overrides) -> Coupon:
    data = {
        "name": "活动满减券",
        "description": "活动专享",
        "type": "threshold_amount_off",
        "discount_amount": Decimal("8.00"),
        "discount_percent": None,
        "min_order_amount": Decimal("30.00"),
        "scope": "all",
        "seat_zone": None,
        "valid_from": NOW - timedelta(days=1),
        "expires_at": NOW + timedelta(days=7),
        "is_active": True,
    }
    data.update(overrides)
    return Coupon(**data)


async def _seed_activity_coupon(db_session: AsyncSession, **overrides):
    activity = Activity(
        title="周末活动",
        description="活动摘要",
        content_html="<p>周末规则</p>",
        cover_image="https://example.com/a.png",
        participant_count=12,
        sort_order=1,
        is_active=True,
    )
    coupon = _coupon()
    db_session.add_all([activity, coupon])
    await db_session.flush()
    activity_coupon_data = {
        "activity_id": activity.id,
        "coupon_id": coupon.id,
        "total_quantity": 10,
        "claimed_quantity": 0,
        "per_user_limit": 1,
        "claim_starts_at": NOW - timedelta(hours=1),
        "claim_ends_at": NOW + timedelta(days=1),
        "is_active": True,
        "sort_order": 1,
        "display_title": "周末专享券",
        "display_description": "满 30 减 8",
    }
    activity_coupon_data.update(overrides)
    activity_coupon = ActivityCoupon(**activity_coupon_data)
    db_session.add(activity_coupon)
    await db_session.flush()
    return activity, coupon, activity_coupon


class TestRichTextSanitizer:
    def test_clean_rich_text_removes_unsafe_content(self):
        html = (
            '<section><p onclick="alert(1)">规则</p>'
            '<a href="javascript:alert(1)">危险链接</a>'
            '<img src="https://example.com/a.png" onerror="alert(1)">'
            "<script>alert(1)</script></section>"
        )

        cleaned = activity_service.sanitize_activity_content(html)

        assert "<script" not in cleaned
        assert "onclick" not in cleaned
        assert "onerror" not in cleaned
        assert "javascript:" not in cleaned
        assert "<p>规则</p>" in cleaned
        assert 'src="https://example.com/a.png"' in cleaned

    def test_clean_rich_text_allows_empty_content(self):
        assert activity_service.sanitize_activity_content(None) == ""
        assert activity_service.sanitize_activity_content("   ") == ""


class TestActivityCouponService:
    @pytest.mark.asyncio
    async def test_create_activity_sanitizes_content_and_creates_coupons(self, db_session: AsyncSession):
        coupon = _coupon()
        db_session.add(coupon)
        await db_session.flush()

        activity = await activity_service.create_activity(
            db_session,
            {
                "title": "新活动",
                "content_html": '<p onclick="bad()">正文</p><script>bad()</script>',
                "activity_coupons": [
                    {
                        "coupon_id": coupon.id,
                        "total_quantity": 5,
                        "per_user_limit": 1,
                        "claim_starts_at": NOW,
                        "claim_ends_at": NOW + timedelta(days=1),
                        "display_title": "领取券",
                    }
                ],
            },
        )

        assert activity.content_html == "<p>正文</p>"
        rows = (await db_session.execute(select(ActivityCoupon))).scalars().all()
        assert len(rows) == 1
        assert rows[0].activity_id == activity.id
        assert rows[0].claimed_quantity == 0

    @pytest.mark.asyncio
    async def test_create_activity_normalizes_claim_time_to_shanghai_naive(self, db_session: AsyncSession):
        coupon = _coupon()
        db_session.add(coupon)
        await db_session.flush()

        activity = await activity_service.create_activity(
            db_session,
            {
                "title": "时区活动",
                "activity_coupons": [
                    {
                        "coupon_id": coupon.id,
                        "total_quantity": 5,
                        "per_user_limit": 1,
                        "claim_starts_at": datetime(2026, 6, 6, 2, 0, tzinfo=timezone.utc),
                        "claim_ends_at": datetime(2026, 6, 7, 2, 0, tzinfo=timezone.utc),
                    }
                ],
            },
        )

        row = (
            await db_session.execute(select(ActivityCoupon).where(ActivityCoupon.activity_id == activity.id))
        ).scalar_one()
        assert row.claim_starts_at == datetime(2026, 6, 6, 10, 0)
        assert row.claim_ends_at == datetime(2026, 6, 7, 10, 0)
        assert row.claim_starts_at.tzinfo is None
        assert row.claim_ends_at.tzinfo is None

    @pytest.mark.asyncio
    async def test_create_activity_rejects_missing_coupon_id_with_chinese_error(self, db_session: AsyncSession):
        with pytest.raises(activity_service.ActivityCouponError, match="卡券模板不存在"):
            await activity_service.create_activity(
                db_session,
                {
                    "title": "无效卡券活动",
                    "activity_coupons": [
                        {
                            "coupon_id": 999999,
                            "total_quantity": 5,
                            "per_user_limit": 1,
                        }
                    ],
                },
            )

    @pytest.mark.asyncio
    async def test_publish_rejects_disabled_coupon_template_with_chinese_error(self, db_session: AsyncSession):
        disabled_coupon = _coupon(is_active=False)
        db_session.add(disabled_coupon)
        await db_session.flush()

        with pytest.raises(activity_service.ActivityCouponError, match="启用的活动卡券必须关联启用的卡券模板"):
            await activity_service.create_activity(
                db_session,
                {
                    "title": "禁用模板活动",
                    "is_active": True,
                    "activity_coupons": [
                        {
                            "coupon_id": disabled_coupon.id,
                            "total_quantity": 5,
                            "per_user_limit": 1,
                        }
                    ],
                },
            )

    @pytest.mark.asyncio
    async def test_claim_activity_coupon_creates_user_coupon_and_records_source(self, db_session: AsyncSession):
        activity, coupon, activity_coupon = await _seed_activity_coupon(db_session)

        result = await activity_service.claim_activity_coupon(
            db_session,
            activity_id=activity.id,
            activity_coupon_id=activity_coupon.id,
            user_id=USER_ID,
            now=NOW,
        )

        assert result.user_coupon.coupon_id == coupon.id
        assert result.user_coupon.source_type == "activity"
        assert result.user_coupon.source_activity_id == activity.id
        assert result.user_coupon.source_activity_coupon_id == activity_coupon.id
        assert result.activity_coupon.claimed_quantity == 1

    @pytest.mark.asyncio
    async def test_claim_activity_coupon_rejects_per_user_limit(self, db_session: AsyncSession):
        activity, coupon, activity_coupon = await _seed_activity_coupon(db_session)
        db_session.add(
            UserCoupon(
                user_id=str(USER_ID),
                coupon_id=coupon.id,
                source_type="activity",
                source_activity_id=activity.id,
                source_activity_coupon_id=activity_coupon.id,
            )
        )
        await db_session.flush()

        with pytest.raises(activity_service.ActivityCouponClaimError, match="已达到领取上限"):
            await activity_service.claim_activity_coupon(
                db_session,
                activity_id=activity.id,
                activity_coupon_id=activity_coupon.id,
                user_id=USER_ID,
                now=NOW,
            )


class TestActivityCouponAPI:
    @pytest.fixture
    async def auth_client(self, client: AsyncClient):
        app = client._transport.app
        app.dependency_overrides[get_current_user_id] = lambda: USER_ID
        app.dependency_overrides[get_optional_current_user_id] = lambda: USER_ID
        yield client
        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_admin_create_activity_with_content_and_coupon(self, client: AsyncClient, db_session: AsyncSession):
        coupon = _coupon()
        db_session.add(coupon)
        await db_session.flush()

        resp = await client.post(
            "/api/v1/admin/activities",
            json={
                "title": "运营活动",
                "content_html": '<p onclick="bad()">活动正文</p><script>bad()</script>',
                "activity_coupons": [
                    {
                        "coupon_id": coupon.id,
                        "total_quantity": 6,
                        "per_user_limit": 1,
                        "claim_starts_at": NOW.isoformat(),
                        "claim_ends_at": (NOW + timedelta(days=1)).isoformat(),
                        "display_title": "运营券",
                        "display_description": "满 30 减 8",
                    }
                ],
            },
        )

        assert resp.status_code == 201
        data = resp.json()
        assert data["content_html"] == "<p>活动正文</p>"
        assert data["activity_coupons"][0]["coupon"]["name"] == "活动满减券"
        assert data["activity_coupons"][0]["remaining_quantity"] == 6

    @pytest.mark.asyncio
    async def test_admin_create_activity_missing_coupon_returns_422(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/admin/activities",
            json={
                "title": "无效卡券活动",
                "activity_coupons": [
                    {
                        "coupon_id": 999999,
                        "total_quantity": 5,
                        "per_user_limit": 1,
                    }
                ],
            },
        )

        assert resp.status_code == 422
        assert "卡券模板不存在" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_admin_publish_disabled_coupon_template_returns_422(
        self,
        client: AsyncClient,
        db_session: AsyncSession,
    ):
        disabled_coupon = _coupon(is_active=False)
        activity = Activity(title="待上架活动", is_active=False)
        db_session.add_all([disabled_coupon, activity])
        await db_session.flush()
        db_session.add(
            ActivityCoupon(
                activity_id=activity.id,
                coupon_id=disabled_coupon.id,
                total_quantity=5,
                per_user_limit=1,
                is_active=True,
            )
        )
        await db_session.flush()

        resp = await client.patch(f"/api/v1/admin/activities/{activity.id}/status", json={"is_active": True})

        assert resp.status_code == 422
        assert "启用的活动卡券必须关联启用的卡券模板" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_activity_detail_returns_coupon_status_for_logged_in_user(
        self,
        auth_client: AsyncClient,
        db_session: AsyncSession,
    ):
        activity, _, activity_coupon = await _seed_activity_coupon(db_session)

        resp = await auth_client.get(f"/api/v1/activities/{activity.id}/")

        assert resp.status_code == 200
        data = resp.json()
        assert data["content_html"] == "<p>周末规则</p>"
        assert data["activity_coupons"][0]["id"] == activity_coupon.id
        assert data["activity_coupons"][0]["claim_status"] == "available"
        assert data["activity_coupons"][0]["remaining_user_claims"] == 1

    @pytest.mark.asyncio
    async def test_claim_endpoint_creates_user_coupon(self, auth_client: AsyncClient, db_session: AsyncSession):
        activity, _, activity_coupon = await _seed_activity_coupon(db_session)

        resp = await auth_client.post(f"/api/v1/activities/{activity.id}/coupons/{activity_coupon.id}/claim")

        assert resp.status_code == 201
        data = resp.json()
        assert data["user_coupon"]["source_type"] == "activity"
        assert data["activity_coupon"]["claimed_quantity"] == 1
        assert data["activity_coupon"]["claim_status"] in {"claimed", "limit_reached"}

    @pytest.mark.asyncio
    async def test_claim_endpoint_requires_login(self, client: AsyncClient, db_session: AsyncSession):
        activity, _, activity_coupon = await _seed_activity_coupon(db_session)

        resp = await client.post(f"/api/v1/activities/{activity.id}/coupons/{activity_coupon.id}/claim")

        assert resp.status_code == 401
