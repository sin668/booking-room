from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.city import CityResponse
from app.services import city_service

router = APIRouter(prefix="/api/v1/cities", tags=["cities"])


@router.get("/", response_model=list[CityResponse])
async def list_cities(db: AsyncSession = Depends(get_db)) -> list[CityResponse]:
    return await city_service.get_active_cities(db)
