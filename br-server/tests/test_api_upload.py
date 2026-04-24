"""Integration tests for file upload API endpoint."""

import io

import pytest
from httpx import AsyncClient

from app.api.dependencies import get_current_admin

ADMIN_TOKEN = "test-admin-token"


@pytest.fixture
def admin_headers():
    return {"X-Admin-Token": ADMIN_TOKEN}


class TestUploadAPI:
    @pytest.mark.asyncio
    async def test_upload_image(self, client: AsyncClient, admin_headers, tmp_path, monkeypatch):
        monkeypatch.chdir(tmp_path)
        fake_file = io.BytesIO(b"\x89PNG\r\n\x1a\nfake-png-content")
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("photo.png", fake_file, "image/png")},
            headers=admin_headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["url"].startswith("/uploads/")
        assert data["url"].endswith(".png")

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
    async def test_upload_oversized_file_returns_422(self, client: AsyncClient, admin_headers):
        large_content = b"x" * (5 * 1024 * 1024 + 1)
        fake_file = io.BytesIO(b"\x89PNG\r\n\x1a\n" + large_content)
        resp = await client.post(
            "/api/v1/admin/upload",
            files={"file": ("big.png", fake_file, "image/png")},
            headers=admin_headers,
        )
        assert resp.status_code == 422
        assert "文件大小不能超过5MB" in resp.json()["detail"]

    @pytest.mark.asyncio
    async def test_upload_no_token_returns_401(self, client: AsyncClient):
        from app.main import app

        # Temporarily remove the override so the real dependency runs
        del app.dependency_overrides[get_current_admin]
        try:
            fake_file = io.BytesIO(b"\x89PNG\r\n\x1a\n")
            resp = await client.post(
                "/api/v1/admin/upload",
                files={"file": ("photo.png", fake_file, "image/png")},
            )
            assert resp.status_code == 401
        finally:
            app.dependency_overrides[get_current_admin] = lambda: None
