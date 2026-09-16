from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, require_admin_permission
from app.core.database import get_db
from app.schemas.admin_edu_listing import (
    AdminEduListingItem,
    AdminEduListingListResponse,
    EduListingStatusUpdate,
)
from app.services import admin_edu_listing_service
from app.services.admin_edu_listing_service import (
    ADMIN_DEFAULT_PAGE_SIZE,
    ADMIN_MAX_PAGE_SIZE,
)

router = APIRouter(prefix="/api/v1/admin/edu-listings", tags=["admin-edu-listings"])


@router.get(
    "",
    response_model=AdminEduListingListResponse,
    dependencies=[Depends(require_admin_permission("edu:listing:view"))],
)
async def list_edu_listings(
    keyword: str | None = Query(None, max_length=100, description="标题模糊匹配"),
    listing_type: str | None = Query(None, alias="type", pattern="^(tutor|training|demand)$"),
    listing_status: str | None = Query(
        None, alias="status", pattern="^(pending|approved|rejected|offline)$"
    ),
    page: int = Query(1, ge=1),
    page_size: int = Query(ADMIN_DEFAULT_PAGE_SIZE, ge=1, le=ADMIN_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
) -> AdminEduListingListResponse:
    return await admin_edu_listing_service.list_edu_listings(
        db,
        keyword=keyword,
        listing_type=listing_type,
        listing_status=listing_status,
        page=page,
        page_size=page_size,
    )


@router.patch("/{listing_id}/status", response_model=AdminEduListingItem)
async def update_edu_listing_status(
    listing_id: int,
    data: EduListingStatusUpdate,
    # 作为参数依赖而非 dependencies=[...]，以便取得 AdminContext 写入 reviewed_by
    context: AdminContext | None = Depends(require_admin_permission("edu:listing:audit")),
    db: AsyncSession = Depends(get_db),
) -> AdminEduListingItem:
    return await admin_edu_listing_service.update_status(
        db,
        listing_id,
        data,
        admin_id=context.admin_id if context else None,
    )
