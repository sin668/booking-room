from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.banner import BannerResponse
from app.services import banner_service

router = APIRouter(prefix="/api/v1/banners", tags=["banners"])


@router.get("", response_model=list[BannerResponse])
async def list_banners(db: AsyncSession = Depends(get_db)) -> list[BannerResponse]:
    return await banner_service.list_active_banners(db)
