"""Tests for upload no-filename edge case."""

import pytest
from httpx import AsyncClient


class TestUploadNoFilename:
    @pytest.mark.asyncio
    async def test_upload_no_filename_returns_422(self, client: AsyncClient):
        """Uploading with no file at all returns 422 (missing file)."""
        # Send request without any file field
        resp = await client.post("/api/v1/admin/upload")
        assert resp.status_code == 422
