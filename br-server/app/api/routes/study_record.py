import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.study_record import StudyRecordListResponse, StudyRecordSummaryResponse
from app.services import study_record_service
from sqlalchemy.ext.asyncio import AsyncSession

router = APIRouter(prefix="/api/v1/study-records", tags=["study-records"])


@router.get("/summary", response_model=StudyRecordSummaryResponse)
async def get_summary(
    month: str = Query(..., pattern=r"^\d{4}-\d{2}$", description="月份，格式 YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> StudyRecordSummaryResponse:
    year, month_num = map(int, month.split("-"))
    month_date = date(year, month_num, 1)
    return await study_record_service.get_monthly_summary(db, user_id, month_date)


@router.get("", response_model=StudyRecordListResponse)
async def list_records(
    page: int = Query(1, ge=1),
    page_size: int = Query(10, ge=1, le=50),
    month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$", description="月份，格式 YYYY-MM"),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> StudyRecordListResponse:
    month_date = None
    if month is not None:
        year, month_num = map(int, month.split("-"))
        month_date = date(year, month_num, 1)
    return await study_record_service.list_study_records(
        db, user_id, page=page, page_size=page_size, month=month_date
    )
