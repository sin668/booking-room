"""全局搜索 API 路由。"""

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.search import SearchResponse
from app.services import search_service

router = APIRouter(prefix="/api/v1/search", tags=["search"])


@router.get("", response_model=SearchResponse)
async def search(
    q: str = Query(..., min_length=1, max_length=100),
    city_id: int | None = Query(None, ge=1),
    db: AsyncSession = Depends(get_db),
) -> SearchResponse:
    return await search_service.search_all(db, keyword=q, city_id=city_id)
