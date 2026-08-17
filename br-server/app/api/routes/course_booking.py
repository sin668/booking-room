"""课程预约 API 路由。"""

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id
from app.core.database import get_db
from app.schemas.course_booking import CourseBookingCreate, CourseBookingResponse
from app.services.course_booking_service import (
    CourseBookingService,
    CourseBookingError,
    CourseNotFoundError,
    CouponUnavailableError,
    LessonValidationError,
    WalletBalanceInsufficientError,
)

router = APIRouter(tags=["course-booking"])


@router.get("/api/v1/courses/{course_id}/lessons")
async def get_course_lessons(
    course_id: int,
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """获取课程详情 + 课时列表 + 定价信息。"""
    service = CourseBookingService()
    result = await service.get_course_with_lessons(course_id, db)
    if result is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    return result


@router.post(
    "/api/v1/course-bookings",
    response_model=CourseBookingResponse,
    status_code=status.HTTP_201_CREATED,
)
async def create_course_booking(
    data: CourseBookingCreate,
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
) -> CourseBookingResponse:
    """创建课程预约订单。"""
    service = CourseBookingService()
    try:
        return await service.create_course_booking(user_id, data, db)
    except CourseNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="课程不存在")
    except LessonValidationError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except CouponUnavailableError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except WalletBalanceInsufficientError as exc:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail=str(exc),
        )
    except CourseBookingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))


@router.post(
    "/api/v1/course-bookings/{booking_id}/cancel",
    status_code=status.HTTP_200_OK,
)
async def cancel_course_booking(
    booking_id: int,
    db: AsyncSession = Depends(get_db),
    user_id=Depends(get_current_user_id),
):
    """取消课程预约。"""
    from app.services.booking_service import (
        BookingAlreadyCancelledError,
        BookingCancellationNotAllowedError,
        BookingNotFoundError,
    )

    service = CourseBookingService()
    try:
        return await service.cancel_course_booking(booking_id, user_id, db)
    except BookingNotFoundError:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="预约不存在")
    except BookingAlreadyCancelledError:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="该预约已取消")
    except BookingCancellationNotAllowedError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except CourseBookingError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
