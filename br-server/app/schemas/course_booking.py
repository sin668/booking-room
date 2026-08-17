"""课程预约相关 Schema。"""

from pydantic import BaseModel, ConfigDict, Field


class CourseLessonItem(BaseModel):
    """课时信息，嵌套在课程预约响应中。"""

    id: int
    title: str
    description: str | None = None
    duration_minutes: int | None = None
    sort_order: int
    is_free_preview: bool = False

    model_config = ConfigDict(from_attributes=True)


class CourseBookingCreate(BaseModel):
    """课程预约创建请求。"""

    course_id: int
    booking_type: str = Field(..., pattern="^(fixed|custom)$")
    lesson_ids: list[int] = Field(..., min_length=1)
    schedule_type: str = Field(..., pattern="^(fixed|custom)$")
    payment_method: str = Field(..., pattern="^(balance|wechat)$")
    coupon_id: int | None = None


class CourseBookingResponse(BaseModel):
    """课程预约创建响应。"""

    booking_id: int
    course_name: str
    lesson_count: int
    lesson_titles: list[str]
    original_price: float
    discount_amount: float
    total_price: float
    payment_status: str
    payment_method: str
    booking_type: str
    schedule_type: str | None = None
    payment_params: dict | None = None
