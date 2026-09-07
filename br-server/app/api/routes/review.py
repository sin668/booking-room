import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_optional_current_user_id
from app.core.database import get_db
from app.schemas.review import (
    ReviewCreate,
    ReviewItem,
    ReviewListResponse,
    ReviewSummary,
)
from app.services import review_service
from app.services.review_service import DEFAULT_PAGE_SIZE, MAX_PAGE_SIZE

router = APIRouter(prefix="/api/v1/reviews", tags=["reviews"])


@router.get("", response_model=ReviewListResponse)
async def list_reviews(
    course_id: int | None = Query(None, description="按课程过滤"),
    teacher_id: int | None = Query(None, description="按老师过滤"),
    booking_id: int | None = Query(None, description="按订单过滤"),
    room_id: int | None = Query(None, description="按学习室过滤（仅自习座位订单）"),
    mine: bool = Query(False, description="只看本人发表的评价（含待审核/已驳回）"),
    rating_band: str = Query("all", pattern="^(all|good|mid|bad)$"),
    has_images: bool = Query(False, description="仅看有图"),
    sort: str = Query("new", pattern="^(new|score)$"),
    page: int = Query(1, ge=1),
    page_size: int = Query(DEFAULT_PAGE_SIZE, ge=1, le=MAX_PAGE_SIZE),
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID | None = Depends(get_optional_current_user_id),
) -> ReviewListResponse:
    # 公开查询允许未登录访问，只有"我的评价"需要登录态
    if mine and user_id is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="未登录")
    return await review_service.list_reviews(
        db,
        user_id=user_id,
        course_id=course_id,
        teacher_id=teacher_id,
        booking_id=booking_id,
        room_id=room_id,
        mine=mine,
        rating_band=rating_band,
        has_images=has_images,
        sort=sort,
        page=page,
        page_size=page_size,
    )


@router.get("/summary", response_model=ReviewSummary)
async def get_review_summary(
    course_id: int | None = Query(None),
    teacher_id: int | None = Query(None),
    room_id: int | None = Query(None),
    db: AsyncSession = Depends(get_db),
) -> ReviewSummary:
    if course_id is None and teacher_id is None and room_id is None:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
            detail="course_id、teacher_id 与 room_id 至少传一个",
        )
    return await review_service.get_summary(
        db, course_id=course_id, teacher_id=teacher_id, room_id=room_id
    )


@router.post("", response_model=ReviewItem)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    user_id: uuid.UUID = Depends(get_current_user_id),
) -> ReviewItem:
    return await review_service.create_review(db, user_id, data)
