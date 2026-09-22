import pytest
from httpx import AsyncClient

from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.models.user import User
from app.services.admin_auth_service import AdminAuthService


@pytest.fixture
async def admin_user(db_session):
    permission = AdminMenu(type="button", title="Role create", permission_code="system:role:create")
    role = AdminRole(name="Role manager", code="role_manager")
    role.menus.append(permission)
    user = User(user_type="admin", phone="",
        username="admin",
        password_hash=AdminAuthService.hash_password("secret123"),
        nickname="Admin",
        email="admin@example.com",
    )
    user.roles.append(role)
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.mark.asyncio
async def test_admin_login_and_me_return_permissions(client: AsyncClient, admin_user):
    login = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "admin", "password": "secret123"},
    )
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = await client.get(
        "/api/v1/admin/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me.status_code == 200
    assert me.json()["username"] == "admin"
    assert {"label": "Role create", "value": "system:role:create"} in me.json()["permissions"]


@pytest.mark.asyncio
async def test_admin_login_rejects_disabled_user(client: AsyncClient, db_session):
    db_session.add(
        User(user_type="admin", phone="",
            username="disabled",
            password_hash=AdminAuthService.hash_password("secret123"),
            nickname="Disabled",
            status="disabled",
        )
    )
    await db_session.commit()

    resp = await client.post(
        "/api/v1/admin/auth/login",
        json={"username": "disabled", "password": "secret123"},
    )

    assert resp.status_code == 403


@pytest.mark.asyncio
async def test_profile_update_does_not_accept_username(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "new-name", "nickname": "New"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_profile_update_does_not_accept_mobile(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"mobile": "13900139000"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_me_returns_phone(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    me = await client.get(
        "/api/v1/admin/auth/me",
        headers={"Authorization": f"Bearer {token}"},
    )

    assert me.status_code == 200
    body = me.json()
    assert "phone" in body
    assert body["username_updated_at"] is None
    assert body["phone_updated_at"] is None


@pytest.mark.asyncio
async def test_profile_update_rejects_phone_field(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"nickname": "New Nick", "email": "new@example.com", "phone": "13700137000"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_profile_update_unchanged_username_skips_cooldown(
    client: AsyncClient, admin_user, db_session
):
    from datetime import datetime

    admin_user.username_updated_at = datetime.now()
    await db_session.commit()
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "admin", "nickname": "Still me"},
    )

    assert resp.status_code == 200
    assert resp.json()["nickname"] == "Still me"


@pytest.mark.asyncio
async def test_profile_update_persists_username(client: AsyncClient, admin_user, db_session):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "new_admin_01"},
    )

    assert resp.status_code == 200
    assert resp.json()["username"] == "new_admin_01"
    assert resp.json()["username_updated_at"] is not None
    await db_session.refresh(admin_user)
    assert admin_user.username == "new_admin_01"


@pytest.mark.asyncio
async def test_profile_update_rejects_invalid_username_format(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "bad name!"},
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_profile_update_rejects_duplicate_username(client: AsyncClient, admin_user, db_session):
    db_session.add(
        User(user_type="app", username="taken_name", password_hash="x", nickname="Other")
    )
    await db_session.commit()
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "taken_name"},
    )

    assert resp.status_code == 409


@pytest.mark.asyncio
async def test_profile_update_username_cooldown_returns_429(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    first = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "first_change"},
    )
    assert first.status_code == 200

    second = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"username": "second_chang3"},
    )

    assert second.status_code == 429
    body = second.json()
    assert "30 天" in body["detail"]
    assert body["retry_after_seconds"] > 0


@pytest.mark.asyncio
async def test_profile_update_persists_gender_birthday_signature(
    client: AsyncClient, admin_user, db_session
):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"gender": "male", "birthday": "1995-06-01", "signature": "hello admin"},
    )

    assert resp.status_code == 200
    assert resp.json()["gender"] == "male"
    assert resp.json()["birthday"] == "1995-06-01"
    assert resp.json()["signature"] == "hello admin"
    await db_session.refresh(admin_user)
    assert admin_user.signature == "hello admin"


@pytest.mark.asyncio
async def test_profile_update_rejects_conflicting_phone(client: AsyncClient, admin_user, db_session):
    db_session.add(
        User(user_type="app", phone="13800138000", password_hash="x", nickname="Other")
    )
    await db_session.commit()
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/profile",
        headers={"Authorization": f"Bearer {token}"},
        json={"phone": "13800138000"},
    )

    assert resp.status_code == 422
    await db_session.refresh(admin_user)
    assert admin_user.phone == ""


@pytest.mark.asyncio
class TestAdminPhoneChangeWithSms:
    async def _patch_sms(self, monkeypatch, verify_ok: bool):
        import app.api.routes.admin_auth as admin_auth_route

        class FakeSMS:
            def __init__(self, redis=None, config=None):
                pass

            async def verify_code(self, phone, code):
                return verify_ok

        monkeypatch.setattr(admin_auth_route, "SMSService", FakeSMS)

    async def test_change_phone_with_valid_code(
        self, client: AsyncClient, admin_user, db_session, monkeypatch
    ):
        await self._patch_sms(monkeypatch, verify_ok=True)
        token = AdminAuthService.create_access_token(admin_user.id)

        resp = await client.patch(
            "/api/v1/admin/auth/phone",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "13700137000", "sms_code": "123456"},
        )

        assert resp.status_code == 200
        assert resp.json() == {"message": "手机号已更新", "phone": "13700137000"}
        await db_session.refresh(admin_user)
        assert admin_user.phone == "13700137000"
        assert admin_user.phone_updated_at is not None

    async def test_change_phone_rejects_invalid_code(
        self, client: AsyncClient, admin_user, db_session, monkeypatch
    ):
        await self._patch_sms(monkeypatch, verify_ok=False)
        token = AdminAuthService.create_access_token(admin_user.id)

        resp = await client.patch(
            "/api/v1/admin/auth/phone",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "13700137000", "sms_code": "000000"},
        )

        assert resp.status_code == 400
        assert resp.json()["detail"] == "验证码无效或已过期"
        await db_session.refresh(admin_user)
        assert admin_user.phone == ""

    async def test_change_phone_rejects_malformed_payload(
        self, client: AsyncClient, admin_user
    ):
        token = AdminAuthService.create_access_token(admin_user.id)

        bad_phone = await client.patch(
            "/api/v1/admin/auth/phone",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "12345", "sms_code": "123456"},
        )
        bad_code = await client.patch(
            "/api/v1/admin/auth/phone",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "13700137000", "sms_code": "123"},
        )

        assert bad_phone.status_code == 422
        assert bad_code.status_code == 422

    async def test_change_phone_conflict_returns_409(
        self, client: AsyncClient, admin_user, db_session, monkeypatch
    ):
        db_session.add(
            User(user_type="app", phone="13800138000", password_hash="x", nickname="Other")
        )
        await db_session.commit()
        await self._patch_sms(monkeypatch, verify_ok=True)
        token = AdminAuthService.create_access_token(admin_user.id)

        resp = await client.patch(
            "/api/v1/admin/auth/phone",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "13800138000", "sms_code": "123456"},
        )

        assert resp.status_code == 409
        await db_session.refresh(admin_user)
        assert admin_user.phone == ""

    async def test_change_phone_cooldown_returns_429(
        self, client: AsyncClient, admin_user, db_session, monkeypatch
    ):
        from datetime import datetime

        admin_user.phone = "13700137000"
        admin_user.phone_updated_at = datetime.now()
        await db_session.commit()
        await self._patch_sms(monkeypatch, verify_ok=True)
        token = AdminAuthService.create_access_token(admin_user.id)

        resp = await client.patch(
            "/api/v1/admin/auth/phone",
            headers={"Authorization": f"Bearer {token}"},
            json={"phone": "13900139000", "sms_code": "123456"},
        )

        assert resp.status_code == 429
        body = resp.json()
        assert "30 天" in body["detail"]
        assert body["retry_after_seconds"] > 0


@pytest.mark.asyncio
async def test_password_update_validates_confirmation(client: AsyncClient, admin_user):
    token = AdminAuthService.create_access_token(admin_user.id)

    resp = await client.put(
        "/api/v1/admin/auth/password",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "old_password": "secret123",
            "new_password": "new-secret",
            "confirm_password": "different",
        },
    )

    assert resp.status_code == 422


@pytest.mark.asyncio
async def test_admin_login_with_phone(client: AsyncClient, db_session):
    """Admin login with phone (no username) returns 200."""
    user = User(
        phone="13800138000",
        password_hash=AdminAuthService.hash_password("secret123"),
        nickname="PhoneUser",
    )
    db_session.add(user)
    await db_session.commit()

    resp = await client.post(
        "/api/v1/admin/auth/login",
        json={"phone": "13800138000", "password": "secret123"},
    )
    assert resp.status_code == 200
    assert resp.json()["access_token"]


@pytest.mark.asyncio
async def test_admin_login_missing_both_fields(client: AsyncClient):
    """Admin login with neither phone nor username returns 422."""
    resp = await client.post(
        "/api/v1/admin/auth/login",
        json={"password": "secret123"},
    )
    assert resp.status_code == 422
