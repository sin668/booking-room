import uuid

from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile

from app.api.dependencies import get_current_user_id, require_admin_permission
from app.schemas.upload import UploadResponse
from app.services.upload_service import ImageUploadService, UploadError

router = APIRouter(tags=["upload"])


async def _upload_image(file: UploadFile, scope: str) -> UploadResponse:
    try:
        return await ImageUploadService().upload_image(
            filename=file.filename,
            content_type=file.content_type,
            content=await file.read(),
            scope=scope,
        )
    except UploadError as exc:
        raise HTTPException(status_code=exc.status_code, detail=exc.message) from exc


@router.post(
    "/api/v1/admin/upload",
    response_model=UploadResponse,
    dependencies=[Depends(require_admin_permission("upload:create"))],
)
async def upload_admin_image(
    file: UploadFile,
    scope: str = Form("common"),
) -> UploadResponse:
    return await _upload_image(file, scope)


@router.post("/api/v1/upload/image", response_model=UploadResponse)
async def upload_user_image(
    file: UploadFile,
    scope: str = Form("avatar"),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> UploadResponse:
    _ = user_id
    if scope != "avatar":
        raise HTTPException(status_code=422, detail="上传场景不支持")
    return await _upload_image(file, scope)
