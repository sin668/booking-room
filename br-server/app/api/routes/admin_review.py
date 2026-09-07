from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, require_admin_permission
from app.core.database import get_db
from app.schemas.admin_review import (
    AdminReviewItem,
    AdminReviewListResponse,
    ReviewReplyUpdate,
    ReviewStatusUpdate,
)
from app.services import admin_review_service
from app.services.review_service import DEFAULT_PAGE_SIZE

router = APIRouter(prefix="/api/v1/admin/reviews", tags=["admin-reviews"])

# 后台分页上限沿用 AdminUserListParams 的口径（100），比 C 端的 50 宽
ADMIN_MAX_PAGE_SIZE = 100


@router.get(
    "",
    response_model=AdminReviewListResponse,
    dependencies=[Depends(require_admin_permission("training:reviews:view"))],
)
async def list_reviews(
    review_status: str | None = Query(
        None, alias="status", pattern="^(pending|approved|rejected)$"
    ),
    rating_band: str = Query("all", pattern="^(all|good|mid|bad)$"),
    keyword: str | None = Query(None, max_length=100),
    sort: str = Query("new", pattern="^(new|score)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=ADMIN_MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
) -> AdminReviewListResponse:
    return await admin_review_service.list_reviews(
        db,
        review_status=review_status,
        rating_band=rating_band,
        keyword=keyword,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.patch(
    "/{review_id}/status",
    response_model=AdminReviewItem,
)
async def update_review_status(
    review_id: int,
    data: ReviewStatusUpdate,
    # 作为参数依赖而非 dependencies=[...]，以便取得 AdminContext 写入 reviewed_by
    context: AdminContext | None = Depends(
        require_admin_permission("training:reviews:audit")
    ),
    db: AsyncSession = Depends(get_db),
) -> AdminReviewItem:
    return await admin_review_service.update_status(
        db,
        review_id,
        data,
        admin_id=context.admin_id if context else None,
    )


@router.patch(
    "/{review_id}/reply",
    response_model=AdminReviewItem,
    dependencies=[Depends(require_admin_permission("training:reviews:reply"))],
)
async def update_review_reply(
    review_id: int,
    data: ReviewReplyUpdate,
    db: AsyncSession = Depends(get_db),
) -> AdminReviewItem:
    return await admin_review_service.update_reply(db, review_id, data)
