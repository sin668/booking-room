"""Image upload validation and storage adapters."""

from __future__ import annotations

import posixpath
import uuid
import logging
from asyncio import to_thread
from dataclasses import dataclass
from datetime import datetime
from pathlib import PurePath
from typing import Protocol

from app.core.config import Settings, settings
from app.schemas.upload import UploadResponse


logger = logging.getLogger(__name__)
MB = 1024 * 1024
UPLOAD_SCOPES = {"avatar", "activity-cover", "room-cover", "common"}
SCOPE_SIZE_LIMITS = {
    "avatar": 2 * MB,
    "activity-cover": 5 * MB,
    "room-cover": 5 * MB,
    "common": 5 * MB,
}
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
ALLOWED_CONTENT_TYPES = {
    "image/jpeg",
    "image/png",
    "image/gif",
    "image/webp",
}


class UploadError(Exception):
    """Base upload error with a user-safe message."""

    status_code = 422

    def __init__(self, message: str) -> None:
        self.message = message
        super().__init__(message)


class UploadValidationError(UploadError):
    """Raised when an uploaded file is invalid."""


class UploadConfigError(UploadError):
    """Raised when upload storage is not usable."""

    status_code = 503


class UploadStorageError(UploadError):
    """Raised when storage fails."""

    status_code = 503


@dataclass(frozen=True)
class UploadObject:
    content: bytes
    object_key: str
    content_type: str
    size: int


class StorageAdapter(Protocol):
    def upload(self, upload: UploadObject) -> UploadResponse:
        """Persist an upload object and return the public result."""


class LocalStorageAdapter:
    def __init__(self, upload_dir: str = "uploads") -> None:
        from pathlib import Path

        self._upload_dir = Path(upload_dir)

    def upload(self, upload: UploadObject) -> UploadResponse:
        path = self._upload_dir / upload.object_key
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_bytes(upload.content)
        return UploadResponse(
            url=f"/uploads/{upload.object_key}",
            object_key=upload.object_key,
            size=upload.size,
            content_type=upload.content_type,
        )


class OssStorageAdapter:
    def __init__(
        self,
        config: Settings,
        *,
        bucket=None,
    ) -> None:
        self._config = config
        self._bucket = bucket

    def upload(self, upload: UploadObject) -> UploadResponse:
        try:
            self._get_bucket().put_object(
                upload.object_key,
                upload.content,
                headers={"Content-Type": upload.content_type},
            )
        except Exception as exc:
            logger.warning(
                "OSS image upload failed: bucket=%s endpoint=%s object_key=%s error=%s",
                self._config.OSS_BUCKET_NAME,
                self._config.OSS_ENDPOINT,
                upload.object_key,
                type(exc).__name__,
            )
            raise UploadStorageError("图片上传服务暂不可用") from exc

        return UploadResponse(
            url=_join_public_url(self._config.OSS_PUBLIC_BASE_URL, upload.object_key),
            object_key=upload.object_key,
            size=upload.size,
            content_type=upload.content_type,
        )

    def _get_bucket(self):
        if self._bucket is not None:
            return self._bucket

        try:
            import oss2
        except ImportError as exc:
            raise UploadConfigError("图片上传服务暂不可用") from exc

        auth = oss2.Auth(
            self._config.OSS_ACCESS_KEY_ID,
            self._config.OSS_ACCESS_KEY_SECRET,
        )
        self._bucket = oss2.Bucket(
            auth,
            self._config.OSS_ENDPOINT,
            self._config.OSS_BUCKET_NAME,
        )
        return self._bucket


def get_storage_adapter(config: Settings = settings) -> StorageAdapter:
    try:
        config.require_upload_storage_usable()
    except ValueError as exc:
        raise UploadConfigError("图片上传服务暂不可用") from exc

    if config.upload_storage_driver == "local":
        return LocalStorageAdapter()
    return OssStorageAdapter(config)


class ImageUploadService:
    def __init__(
        self,
        storage: StorageAdapter | None = None,
        *,
        config: Settings = settings,
    ) -> None:
        self._storage = storage
        self._config = config

    async def upload_image(
        self,
        *,
        filename: str | None,
        content_type: str | None,
        content: bytes,
        scope: str = "common",
    ) -> UploadResponse:
        normalized_scope = validate_scope(scope)
        ext = normalize_extension(filename)
        size = len(content)
        validate_image_content(
            content=content,
            content_type=content_type,
            ext=ext,
            size=size,
            scope=normalized_scope,
        )
        object_key = generate_object_key(normalized_scope, ext)
        upload_object = UploadObject(
            content=content,
            object_key=object_key,
            content_type=_content_type_for_extension(ext),
            size=size,
        )
        storage = self._storage or get_storage_adapter(self._config)
        return await to_thread(
            storage.upload,
            upload_object,
        )


def validate_scope(scope: str | None) -> str:
    normalized = (scope or "common").strip()
    if normalized not in UPLOAD_SCOPES:
        raise UploadValidationError("上传场景不支持")
    return normalized


def normalize_extension(filename: str | None) -> str:
    if not filename:
        raise UploadValidationError("缺少文件")
    ext = PurePath(filename.replace("\\", "/")).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError("仅支持图片文件")
    return ext


def validate_image_content(
    *,
    content: bytes,
    content_type: str | None,
    ext: str,
    size: int,
    scope: str,
) -> None:
    if size <= 0:
        raise UploadValidationError("缺少文件")

    max_size = SCOPE_SIZE_LIMITS[scope]
    if size > max_size:
        limit_mb = max_size // MB
        raise UploadValidationError(f"文件大小不能超过{limit_mb}MB")

    if content_type not in ALLOWED_CONTENT_TYPES:
        raise UploadValidationError("仅支持图片文件")

    expected_content_type = _content_type_for_extension(ext)
    if content_type != expected_content_type:
        raise UploadValidationError("仅支持图片文件")

    if not _has_valid_signature(content, ext):
        raise UploadValidationError("仅支持图片文件")


def generate_object_key(
    scope: str,
    ext: str,
    *,
    now: datetime | None = None,
    uuid_value: uuid.UUID | None = None,
) -> str:
    normalized_scope = validate_scope(scope)
    if ext not in ALLOWED_EXTENSIONS:
        raise UploadValidationError("仅支持图片文件")

    current = now or datetime.now()
    file_id = (uuid_value or uuid.uuid4()).hex
    return f"images/{normalized_scope}/{current:%Y/%m/%d}/{file_id}{ext}"


def _has_valid_signature(content: bytes, ext: str) -> bool:
    if ext in {".jpg", ".jpeg"}:
        return content.startswith(b"\xff\xd8\xff")
    if ext == ".png":
        return content.startswith(b"\x89PNG\r\n\x1a\n")
    if ext == ".gif":
        return content.startswith((b"GIF87a", b"GIF89a"))
    if ext == ".webp":
        return len(content) >= 12 and content.startswith(b"RIFF") and content[8:12] == b"WEBP"
    return False


def _content_type_for_extension(ext: str) -> str:
    if ext in {".jpg", ".jpeg"}:
        return "image/jpeg"
    if ext == ".png":
        return "image/png"
    if ext == ".gif":
        return "image/gif"
    if ext == ".webp":
        return "image/webp"
    return "application/octet-stream"


def _join_public_url(base_url: str, object_key: str) -> str:
    normalized_base_url = base_url.strip()
    if "://" not in normalized_base_url:
        normalized_base_url = f"https://{normalized_base_url}"
    return f"{normalized_base_url.rstrip('/')}/{posixpath.normpath(object_key).lstrip('/')}"
