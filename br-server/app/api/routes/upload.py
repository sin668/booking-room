import uuid
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, Depends, HTTPException, UploadFile, status

from app.api.dependencies import get_current_admin
from app.schemas.activity import UploadResponse

router = APIRouter(prefix="/api/v1/admin", tags=["admin-upload"], dependencies=[Depends(get_current_admin)])

UPLOAD_DIR = Path("uploads")
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".webp"}
MAX_FILE_SIZE = 5 * 1024 * 1024  # 5MB


@router.post("/upload", response_model=UploadResponse)
async def upload_file(file: UploadFile) -> UploadResponse:
    if not file.filename:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="缺少文件")

    ext = Path(file.filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="仅支持图片文件")

    content = await file.read()
    if len(content) > MAX_FILE_SIZE:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="文件大小不能超过5MB")

    today = datetime.now().strftime("%Y/%m/%d")
    dir_path = UPLOAD_DIR / today
    dir_path.mkdir(parents=True, exist_ok=True)

    filename = f"{uuid.uuid4().hex}{ext}"
    file_path = dir_path / filename

    with open(file_path, "wb") as f:
        f.write(content)

    return UploadResponse(url=f"/uploads/{today}/{filename}")
