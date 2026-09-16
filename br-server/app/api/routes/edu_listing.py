import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.edu_listing import (
    EduListingCreate,
    EduListingItem,
    EduListingListResponse,
)
from app.services import edu_listing_service
from app.services.edu_listing_service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/v1/edu-listings", tags=["edu-listings"])


@router.get("", response_model=EduListingListResponse)
async def list_edu_listings(
    listing_type: str | None = Query(None, pattern="^(tutor|training|demand)$"),
    subject: str | None = Query(None, max_length=50, description="按科目过滤"),
    city: str | None = Query(None, max_length=100, description="按服务区域模糊过滤"),
    sort: str = Query("new", pattern="^(new|price_asc|price_desc)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
) -> EduListingListResponse:
    """综合广场列表：教与学混排，仅返回已通过信息，游客可访问。"""
    return await edu_listing_service.list_edu_listings(
        db,
        listing_type=listing_type,
        subject=subject,
        city=city,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/mine", response_model=EduListingListResponse)
async def list_my_edu_listings(
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> EduListingListResponse:
    """我发布的供需信息：全部状态，需登录。"""
    return await edu_listing_service.list_mine(db, user_id, page=page, page_size=page_size)


@router.get("/{listing_id}", response_model=EduListingItem)
async def get_edu_listing_detail(
    listing_id: int,
    db: AsyncSession = Depends(get_db),
) -> EduListingItem:
    """供需信息详情：浏览数 +1，附带发布者认证状态。"""
    return await edu_listing_service.get_detail(db, listing_id)


@router.post("", response_model=EduListingItem, status_code=status.HTTP_201_CREATED)
async def create_edu_listing(
    data: EduListingCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> EduListingItem:
    """发布供需信息：后端强制认证前置校验。"""
    return await edu_listing_service.create_edu_listing(db, user_id, data)
