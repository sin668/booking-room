"""Unit tests for image upload validation and storage adapters."""

from datetime import datetime
from uuid import UUID

import pytest

from app.core.config import Settings
from app.services.upload_service import (
    ImageUploadService,
    LocalStorageAdapter,
    OssStorageAdapter,
    UploadConfigError,
    UploadObject,
    UploadStorageError,
    UploadValidationError,
    generate_object_key,
    normalize_extension,
    validate_image_content,
)


PNG_BYTES = b"\x89PNG\r\n\x1a\nfake-png-content"
JPG_BYTES = b"\xff\xd8\xfffake-jpg-content"
WEBP_BYTES = b"RIFF\x10\x00\x00\x00WEBPfake-webp-content"


def test_validate_image_accepts_supported_signatures():
    cases = [
        (JPG_BYTES, "image/jpeg", ".jpg"),
        (PNG_BYTES, "image/png", ".png"),
        (WEBP_BYTES, "image/webp", ".webp"),
    ]

    for content, content_type, ext in cases:
        validate_image_content(
            content=content,
            content_type=content_type,
            ext=ext,
            size=len(content),
            scope="common",
        )


def test_invalid_extension_is_rejected():
    with pytest.raises(UploadValidationError, match="仅支持图片文件"):
        normalize_extension("script.exe")


def test_fake_extension_is_rejected():
    with pytest.raises(UploadValidationError, match="仅支持图片文件"):
        validate_image_content(
            content=b"not-a-real-png",
            content_type="image/png",
            ext=".png",
            size=len(b"not-a-real-png"),
            scope="common",
        )


def test_mismatched_content_type_and_extension_is_rejected():
    with pytest.raises(UploadValidationError, match="仅支持图片文件"):
        validate_image_content(
            content=PNG_BYTES,
            content_type="image/jpeg",
            ext=".png",
            size=len(PNG_BYTES),
            scope="common",
        )


def test_empty_file_is_rejected():
    with pytest.raises(UploadValidationError, match="缺少文件"):
        validate_image_content(
            content=b"",
            content_type="image/png",
            ext=".png",
            size=0,
            scope="common",
        )


def test_avatar_size_limit_is_two_mb():
    content = b"\x89PNG\r\n\x1a\n" + (b"x" * (2 * 1024 * 1024))

    with pytest.raises(UploadValidationError, match="文件大小不能超过2MB"):
        validate_image_content(
            content=content,
            content_type="image/png",
            ext=".png",
            size=len(content),
            scope="avatar",
        )


def test_cover_scope_allows_under_five_mb():
    content = b"\x89PNG\r\n\x1a\n" + (b"x" * (5 * 1024 * 1024 - 100))

    validate_image_content(
        content=content,
        content_type="image/png",
        ext=".png",
        size=len(content),
        scope="activity-cover",
    )


def test_generate_object_key_uses_scope_date_uuid_and_strips_filename_path():
    ext = normalize_extension("../../avatar.png")
    object_key = generate_object_key(
        "avatar",
        ext,
        now=datetime(2026, 5, 29),
        uuid_value=UUID("12345678-1234-5678-1234-567812345678"),
    )

    assert object_key == (
        "images/avatar/2026/05/29/12345678123456781234567812345678.png"
    )
    assert ".." not in object_key


def test_local_storage_adapter_writes_file_and_returns_uploads_url(tmp_path):
    adapter = LocalStorageAdapter(upload_dir=str(tmp_path))
    upload = UploadObject(
        content=PNG_BYTES,
        object_key="images/common/2026/05/29/file.png",
        content_type="image/png",
        size=len(PNG_BYTES),
    )

    result = adapter.upload(upload)

    assert (tmp_path / upload.object_key).read_bytes() == PNG_BYTES
    assert result.url == "/uploads/images/common/2026/05/29/file.png"
    assert result.object_key == upload.object_key
    assert result.size == len(PNG_BYTES)
    assert result.content_type == "image/png"


def test_oss_storage_adapter_puts_object_and_returns_public_url():
    class FakeBucket:
        def __init__(self):
            self.calls = []

        def put_object(self, object_key, content, headers=None):
            self.calls.append((object_key, content, headers))

    bucket = FakeBucket()
    config = Settings(
        UPLOAD_STORAGE_DRIVER="oss",
        OSS_ENDPOINT="https://oss-cn.example.aliyuncs.com",
        OSS_BUCKET_NAME="booking-room",
        OSS_ACCESS_KEY_ID="access-key-id",
        OSS_ACCESS_KEY_SECRET="access-key-secret",
        OSS_PUBLIC_BASE_URL="https://cdn.example.com/assets/",
    )
    adapter = OssStorageAdapter(config, bucket=bucket)
    upload = UploadObject(
        content=PNG_BYTES,
        object_key="images/common/2026/05/29/file.png",
        content_type="image/png",
        size=len(PNG_BYTES),
    )

    result = adapter.upload(upload)

    assert bucket.calls == [
        (
            "images/common/2026/05/29/file.png",
            PNG_BYTES,
            {"Content-Type": "image/png"},
        )
    ]
    assert result.url == "https://cdn.example.com/assets/images/common/2026/05/29/file.png"
    assert result.object_key == upload.object_key
    assert result.content_type == "image/png"


def test_oss_storage_adapter_adds_https_scheme_to_public_url():
    class FakeBucket:
        def put_object(self, object_key, content, headers=None):
            return None

    config = Settings(
        UPLOAD_STORAGE_DRIVER="oss",
        OSS_ENDPOINT="https://oss-cn.example.aliyuncs.com",
        OSS_BUCKET_NAME="booking-room",
        OSS_ACCESS_KEY_ID="access-key-id",
        OSS_ACCESS_KEY_SECRET="access-key-secret",
        OSS_PUBLIC_BASE_URL="cdn.example.com",
    )
    adapter = OssStorageAdapter(config, bucket=FakeBucket())
    upload = UploadObject(
        content=PNG_BYTES,
        object_key="images/avatar/2026/05/29/file.png",
        content_type="image/png",
        size=len(PNG_BYTES),
    )

    result = adapter.upload(upload)

    assert result.url == "https://cdn.example.com/images/avatar/2026/05/29/file.png"


def test_oss_storage_error_is_sanitized():
    class FailingBucket:
        def put_object(self, object_key, content, headers=None):
            raise RuntimeError("AccessKeySecret=super-secret traceback")

    config = Settings(
        UPLOAD_STORAGE_DRIVER="oss",
        OSS_ENDPOINT="https://oss-cn.example.aliyuncs.com",
        OSS_BUCKET_NAME="booking-room",
        OSS_ACCESS_KEY_ID="access-key-id",
        OSS_ACCESS_KEY_SECRET="access-key-secret",
        OSS_PUBLIC_BASE_URL="https://cdn.example.com",
    )
    adapter = OssStorageAdapter(config, bucket=FailingBucket())

    with pytest.raises(UploadStorageError) as exc:
        adapter.upload(
            UploadObject(
                content=PNG_BYTES,
                object_key="images/common/2026/05/29/file.png",
                content_type="image/png",
                size=len(PNG_BYTES),
            )
        )

    assert str(exc.value) == "图片上传服务暂不可用"
    assert "super-secret" not in str(exc.value)


@pytest.mark.asyncio
async def test_service_returns_503_error_for_missing_oss_config():
    service = ImageUploadService(
        config=Settings(
            UPLOAD_STORAGE_DRIVER="oss",
            OSS_ENDPOINT="",
            OSS_BUCKET_NAME="",
            OSS_ACCESS_KEY_ID="",
            OSS_ACCESS_KEY_SECRET="",
            OSS_PUBLIC_BASE_URL="",
        )
    )

    with pytest.raises(UploadConfigError, match="图片上传服务暂不可用"):
        await service.upload_image(
            filename="photo.png",
            content_type="image/png",
            content=PNG_BYTES,
            scope="common",
        )
