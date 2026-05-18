import pytest
from httpx import AsyncClient

from app.models.admin_setting import SystemSetting


def legacy_headers():
    return {"X-Admin-Token": "test-admin-token"}


@pytest.mark.asyncio
async def test_settings_read_masks_smtp_password(client: AsyncClient, monkeypatch, db_session):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    db_session.add(SystemSetting(key="smtp_password", value="secret", group="email", is_secret=True))
    await db_session.commit()

    resp = await client.get("/api/v1/admin/settings", headers=legacy_headers())

    assert resp.status_code == 200
    assert "smtp_password" not in resp.json()["email"]
    assert resp.json()["email"]["smtp_password_set"] is True


@pytest.mark.asyncio
async def test_update_email_without_password_preserves_existing_secret(client: AsyncClient, monkeypatch, db_session):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")
    db_session.add(SystemSetting(key="smtp_password", value="secret", group="email", is_secret=True))
    await db_session.commit()

    resp = await client.put(
        "/api/v1/admin/settings/email",
        headers=legacy_headers(),
        json={
            "smtp_host": "smtp.example.com",
            "smtp_port": 587,
            "smtp_username": "user",
            "smtp_sender": "noreply@example.com",
            "smtp_tls": True,
        },
    )

    assert resp.status_code == 200
    secret = await db_session.get(SystemSetting, "smtp_password")
    assert secret.value == "secret"
    assert resp.json()["smtp_password_set"] is True


@pytest.mark.asyncio
async def test_email_test_requires_complete_config(client: AsyncClient, monkeypatch):
    monkeypatch.setattr("app.core.config.settings.ADMIN_TOKEN", "test-admin-token")

    resp = await client.post(
        "/api/v1/admin/settings/email/test",
        headers=legacy_headers(),
        json={"to_email": "admin@example.com"},
    )

    assert resp.status_code == 400
