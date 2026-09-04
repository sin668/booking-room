import uuid
from datetime import datetime, timedelta
from decimal import Decimal
from unittest.mock import AsyncMock

import bcrypt
import pytest
from httpx import ASGITransport, AsyncClient

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.core.redis import get_redis
from app.main import app
from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.user import User
from app.models.user_identity_verification import UserIdentityVerification
from app.models.wallet import WalletTransaction


USER_ID = uuid.UUID("11111111-2222-3333-4444-555555555555")


@pytest.fixture
async def security_client(db_session):
    async def override_get_db():
        yield db_session

    redis = AsyncMock()
    redis.keys.return_value = [f"refresh:{USER_ID}:old"]
    redis.delete = AsyncMock()

    app.dependency_overrides[get_db] = override_get_db
    app.dependency_overrides[get_redis] = lambda: redis
    app.dependency_overrides[get_current_user_id] = lambda: USER_ID

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        ac.redis = redis
        yield ac

    app.dependency_overrides.clear()


async def _create_user(db_session, **overrides) -> User:
    values = {
        "id": USER_ID,
        "phone": "13800138000",
        "username": "Luna48392",
        "nickname": "学习达人",
        "password_hash": bcrypt.hashpw(b"oldpass123", bcrypt.gensalt()).decode("utf-8"),
        "status": "active",
        "balance": Decimal("0.00"),
    }
    values.update(overrides)
    user = User(**values)
    db_session.add(user)
    await db_session.flush()
    return user


@pytest.mark.asyncio
async def test_security_summary_masks_sensitive_fields(security_client, db_session):
    await _create_user(db_session, wechat_openid="openid-secret")
    db_session.add(
        UserIdentityVerification(
            user_id=USER_ID,
            real_name="张三",
            id_card_hash="hash-secret",
            id_card_masked="440101********1234",
            status="verified",
            submitted_at=datetime.now(),
            reviewed_at=datetime.now(),
        )
    )
    await db_session.flush()

    resp = await security_client.get("/api/v1/users/me/security")

    assert resp.status_code == 200
    data = resp.json()
    assert data["phone_bound"] is True
    assert data["phone_masked"] == "138****8000"
    assert data["wechat_bound"] is True
    assert data["identity_status"] == "verified"
    assert data["identity_masked"] == "440101********1234"
    assert "openid-secret" not in resp.text
    assert "hash-secret" not in resp.text


@pytest.mark.asyncio
async def test_security_summary_requires_auth(client):
    resp = await client.get("/api/v1/users/me/security")

    assert resp.status_code == 401


@pytest.mark.asyncio
async def test_security_summary_returns_deleted_unbound_unverified_state(security_client, db_session):
    await _create_user(
        db_session,
        phone=None,
        wechat_openid=None,
        status="deleted",
    )

    resp = await security_client.get("/api/v1/users/me/security")

    assert resp.status_code == 200
    data = resp.json()
    assert data["phone_bound"] is False
    assert data["phone_masked"] is None
    assert data["wechat_bound"] is False
    assert data["identity_status"] == "unverified"
    assert data["account_status"] == "deleted"


@pytest.mark.asyncio
async def test_change_password_updates_hash_and_revokes_refresh_tokens(security_client, db_session):
    user = await _create_user(db_session)
    old_hash = user.password_hash

    resp = await security_client.post(
        "/api/v1/users/me/password",
        json={
            "old_password": "oldpass123",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        },
    )

    assert resp.status_code == 200
    assert resp.json()["message"] == "密码已更新"
    assert user.password_hash != old_hash
    assert bcrypt.checkpw(b"newpass123", user.password_hash.encode("utf-8"))
    security_client.redis.delete.assert_awaited()


@pytest.mark.asyncio
async def test_change_password_rejects_bad_old_password_or_mismatch(security_client, db_session):
    user = await _create_user(db_session)
    old_hash = user.password_hash

    bad_old = await security_client.post(
        "/api/v1/users/me/password",
        json={
            "old_password": "wrongpass",
            "new_password": "newpass123",
            "confirm_password": "newpass123",
        },
    )
    mismatch = await security_client.post(
        "/api/v1/users/me/password",
        json={
            "old_password": "oldpass123",
            "new_password": "newpass123",
            "confirm_password": "newpass124",
        },
    )

    assert bad_old.status_code == 400
    assert mismatch.status_code == 422
    assert user.password_hash == old_hash


@pytest.mark.asyncio
async def test_submit_identity_verification_masks_and_verifies(security_client, db_session):
    await _create_user(db_session)

    resp = await security_client.post(
        "/api/v1/users/me/identity-verification",
        json={"real_name": "张三", "id_card_number": "11010519491231002X"},
    )

    assert resp.status_code == 200
    data = resp.json()
    assert data["status"] == "verified"
    assert data["id_card_masked"] == "110105********002X"
    assert "11010519491231002X" not in resp.text


@pytest.mark.asyncio
async def test_submit_identity_rejects_invalid_or_different_verified(security_client, db_session):
    await _create_user(db_session)
    db_session.add(
        UserIdentityVerification(
            user_id=USER_ID,
            real_name="张三",
            id_card_hash="2b01b0db9cdd68657a420d31bd4efcdf51c6c86b07639075fcd91f8c299a1d21",
            id_card_masked="110105********002X",
            status="verified",
            submitted_at=datetime.now(),
            reviewed_at=datetime.now(),
        )
    )
    await db_session.flush()

    invalid = await security_client.post(
        "/api/v1/users/me/identity-verification",
        json={"real_name": "", "id_card_number": "bad"},
    )
    different = await security_client.post(
        "/api/v1/users/me/identity-verification",
        json={"real_name": "李四", "id_card_number": "11010519491231002X"},
    )

    assert invalid.status_code == 422
    assert different.status_code == 409


@pytest.mark.asyncio
async def test_deactivate_account_sets_deleted_without_removing_user(security_client, db_session):
    user = await _create_user(db_session)

    resp = await security_client.post("/api/v1/users/me/deactivation")

    assert resp.status_code == 200
    assert resp.json()["status"] == "deleted"
    assert user.status == "deleted"
    assert user in db_session
    security_client.redis.delete.assert_awaited()


@pytest.mark.asyncio
async def test_deactivate_account_blocks_risks(security_client, db_session):
    await _create_user(db_session, balance=Decimal("8.00"))
    db_session.add(
        Booking(
            user_id=str(USER_ID),
            seat_id=1,
            room_id=1,
            date=datetime.now().date(),
            start_time=datetime.now().time(),
            end_time=datetime.now().time(),
            status="in_progress",
            payment_status="paid",
            total_price=10,
        )
    )
    coupon = Coupon(
        name="券",
        type="cash",
        valid_from=datetime.now() - timedelta(days=1),
        expires_at=datetime.now() + timedelta(days=1),
        is_active=True,
    )
    db_session.add(coupon)
    await db_session.flush()
    db_session.add(UserCoupon(user_id=str(USER_ID), coupon_id=coupon.id, status="available"))
    db_session.add(
        WalletTransaction(
            user_id=str(USER_ID),
            type="recharge",
            amount=10,
            order_id="order-1",
            status="pending",
            payment_status="pending",
        )
    )
    await db_session.flush()

    resp = await security_client.post("/api/v1/users/me/deactivation")

    assert resp.status_code == 409
    detail = resp.json()["detail"]
    codes = {item["code"] for item in detail["risks"]}
    assert "wallet_balance" in codes
    assert "unfinished_booking" in codes
    assert "available_coupon" in codes
    assert "pending_wallet_transaction" in codes
