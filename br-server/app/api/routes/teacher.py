"""教师详情路由"""

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.teacher import TeacherDetailResponse
from app.services import teacher_service

router = APIRouter(prefix="/api/v1/teachers", tags=["teachers"])


@router.get("/{teacher_id}", response_model=TeacherDetailResponse)
async def get_teacher_detail(
    teacher_id: int,
    db: AsyncSession = Depends(get_db),
) -> TeacherDetailResponse:
    result = await teacher_service.get_teacher_detail(db, teacher_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Teacher not found")
    return result
