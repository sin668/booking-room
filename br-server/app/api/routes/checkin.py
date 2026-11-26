import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.checkin import (
    CheckinActionResponse,
    CheckinSummaryResponse,
    MakeupRequest,
)
from app.services import checkin_service

router = APIRouter(prefix="/api/v1/checkin", tags=["checkin"])


@router.get("/summary", response_model=CheckinSummaryResponse)
async def get_summary(
    month: str = Query(
        ...,
        pattern=r"^\d{4}-(0[1-9]|1[0-2])$",
        description="月份，格式 YYYY-MM",
    ),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CheckinSummaryResponse:
    year, month_num = map(int, month.split("-"))
    return await checkin_service.get_summary(db, user_id, date(year, month_num, 1))


@router.post("", response_model=CheckinActionResponse)
async def check_in(
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CheckinActionResponse:
    return await checkin_service.check_in(db, user_id)


@router.post("/makeup", response_model=CheckinActionResponse)
async def make_up(
    payload: MakeupRequest,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> CheckinActionResponse:
    return await checkin_service.make_up(db, user_id, payload.dates)
