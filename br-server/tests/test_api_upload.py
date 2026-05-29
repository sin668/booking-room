"""Integration tests for file upload API endpoints."""

import io
import uuid

import pytest
from httpx import AsyncClient

from app.api.dependencies import AdminContext, get_current_admin, get_current_user_id
from app.core.config import settings
from app.main import app

ADMIN_TOKEN = "test-admin-token"
PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-png-content"


@pytest.fixture
def admin_headers():
    return {"X-Admin-Token": ADMIN_TOKEN}


class TestUploadAPI:
    @pytest.mark.asyncio
    async def test_admin_upload_image(self, client: AsyncClient, admin_headers, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "UPLOAD_STORAGE_DRIVER", "local")
        fake_file = io.BytesIO(PNG_BYTES)
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("photo.png", fake_file, "image/png")},
            data={"scope": "activity-cover"},
            headers=admin_headers,
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["url"].startswith("/uploads/images/activity-cover/")
        assert data["url"].endswith(".png")
        assert data["object_key"].startswith("images/activity-cover/")
        assert data["size"] == len(PNG_BYTES)
        assert data["content_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_admin_upload_defaults_to_common_scope(
        self,
        client: AsyncClient,
        admin_headers,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "UPLOAD_STORAGE_DRIVER", "local")

        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("photo.png", io.BytesIO(PNG_BYTES), "image/png")},
            headers=admin_headers,
        )

        assert resp.status_code == 200
        assert resp.json()["object_key"].startswith("images/common/")

    @pytest.mark.asyncio
    async def test_upload_non_image_returns_422(self, client: AsyncClient, admin_headers):
        fake_file = io.BytesIO(b"not-an-image")
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("script.exe", fake_file, "application/octet-stream")},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        assert "仅支持图片文件" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_oversized_avatar_returns_422(self, client: AsyncClient, admin_headers):
        large_content = b"\x89PNG\r\n\x1a\n" + (b"x" * (2 * 1024 * 1024))
        fake_file = io.BytesIO(large_content)
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("big.png", fake_file, "image/png")},
            data={"scope": "avatar"},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        assert "文件大小不能超过2MB" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_admin_upload_no_permission_returns_403(
        self,
        client: AsyncClient,
        admin_headers,
    ):
        app.dependency_overrides[get_current_admin] = lambda: AdminContext(
            admin_id=uuid.UUID(int=1),
            username="limited-admin",
            is_super_admin=False,
            permission_codes=set(),
            menu_ids=set(),
        )

        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("photo.png", io.BytesIO(PNG_BYTES), "image/png")},
            headers=admin_headers,
        )

        assert resp.status_code == 403

    @pytest.mark.asyncio
    async def test_admin_upload_missing_file_returns_422(self, client: AsyncClient, admin_headers):
        resp = await client.post("/api/v1/admin/upload", headers=admin_headers)
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_oss_config_missing_returns_503(self, client: AsyncClient, admin_headers, monkeypatch):
        monkeypatch.setattr(settings, "UPLOAD_STORAGE_DRIVER", "oss")
        monkeypatch.setattr(settings, "OSS_ENDPOINT", "")
        monkeypatch.setattr(settings, "OSS_BUCKET_NAME", "")
        monkeypatch.setattr(settings, "OSS_ACCESS_KEY_ID", "")
        monkeypatch.setattr(settings, "OSS_ACCESS_KEY_SECRET", "")
        monkeypatch.setattr(settings, "OSS_PUBLIC_BASE_URL", "")

        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("photo.png", io.BytesIO(PNG_BYTES), "image/png")},
            headers=admin_headers,
        )

        assert resp.status_code == 503
        assert resp.json()["detail"] == "图片上传服务暂不可用"
        assert "OSS_ACCESS_KEY_SECRET" not in resp.text

    @pytest.mark.asyncio
    async def test_admin_upload_no_token_returns_401(self, client: AsyncClient):
        # Temporarily remove the override so the real dependency runs.
        del app.dependency_overrides[get_current_admin]
        try:
            resp = await client.post(
                "/api/v1/admin/upload",
                files={"file": ("photo.png", io.BytesIO(PNG_BYTES), "image/png")},
            )
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None

    @pytest.mark.asyncio
    async def test_app_upload_requires_login(self, client: AsyncClient):
        resp = await client.post(
            "/api/v1/upload/image",
            files={"file": ("photo.png", io.BytesIO(PNG_BYTES), "image/png")},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_app_upload_image_without_admin_permission(
        self,
        client: AsyncClient,
        tmp_path,
        monkeypatch,
    ):
        monkeypatch.chdir(tmp_path)
        monkeypatch.setattr(settings, "UPLOAD_STORAGE_DRIVER", "local")
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID(int=2)

        resp = await client.post(
            "/api/v1/upload/image",
            files={"file": ("avatar.png", io.BytesIO(PNG_BYTES), "image/png")},
            data={"scope": "avatar"},
        )

        assert resp.status_code == 200
        data = resp.json()
        assert data["object_key"].startswith("images/avatar/")
        assert data["url"].startswith("/uploads/images/avatar/")
        assert data["content_type"] == "image/png"

    @pytest.mark.asyncio
    async def test_app_upload_rejects_non_avatar_scope(
        self,
        client: AsyncClient,
        monkeypatch,
    ):
        monkeypatch.setattr(settings, "UPLOAD_STORAGE_DRIVER", "local")
        app.dependency_overrides[get_current_user_id] = lambda: uuid.UUID(int=2)

        resp = await client.post(
            "/api/v1/upload/image",
            files={"file": ("room.png", io.BytesIO(PNG_BYTES), "image/png")},
            data={"scope": "room-cover"},
        )

        assert resp.status_code == 422
        assert resp.json()["detail"] == "上传场景不支持"
