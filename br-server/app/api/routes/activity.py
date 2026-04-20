from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.activity import ActivityResponse
from app.services import activity_service

router = APIRouter(prefix="/api/v1/activities", tags=["activities"])


@router.get("", response_model=list[ActivityResponse])
async def list_activities(db: AsyncSession = Depends(get_db)) -> list[ActivityResponse]:
    return await activity_service.list_active_activities(db)
