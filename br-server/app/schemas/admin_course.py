"""Admin course management schemas."""

from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field


class CourseScheduleItem(BaseModel):
    """排课记录项"""
    id: int | None = None
    teacher_id: int | None = None
    start_date: str | None = None
    time_slots: str | None = None
    price: Decimal
    custom_price: Decimal = Decimal("0")
    full_package_price: Decimal | None = None
    full_custom_price: Decimal | None = None


class AdminLessonItem(BaseModel):
    """Admin 课时项"""
    id: int
    title: str
    description: str | None = None
    duration_minutes: int | None = None
    sort_order: int
    is_free_preview: bool = False

    model_config = ConfigDict(from_attributes=True)


class AdminLessonCreate(BaseModel):
    """创建课时请求"""
    title: str = Field(..., min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    duration_minutes: int | None = None
    sort_order: int = 0
    is_free_preview: bool = False


class AdminLessonUpdate(BaseModel):
    """更新课时请求"""
    title: str | None = Field(None, min_length=1, max_length=200)
    description: str | None = Field(None, max_length=500)
    duration_minutes: int | None = None
    sort_order: int | None = None
    is_free_preview: bool | None = None


class AdminCourseItem(BaseModel):
    """Admin 课程列表项"""
    id: int
    name: str
    cover_image: str | None = None
    category: str
    rating: Decimal
    enrollment_count: int
    tags: list[str] = []
    status: str
    is_hot: bool = False
    sort_order: int
    room_id: int
    room_name: str | None = None
    schedules: list[CourseScheduleItem] = []
    created_at: str
    updated_at: str

    model_config = ConfigDict(from_attributes=True)

    @staticmethod
    def parse_tags(v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [tag.strip() for tag in v.split(",") if tag.strip()]


class AdminCourseListResponse(BaseModel):
    items: list[AdminCourseItem]
    total: int
    page: int
    page_size: int


class AdminCourseCreate(BaseModel):
    """创建课程请求"""
    name: str = Field(..., min_length=1, max_length=100)
    cover_image: str | None = None
    category: str = Field(..., max_length=30)
    room_id: int
    tags: str | None = None
    description: str | None = None
    is_hot: bool = False
    sort_order: int = 0
    status: str = "active"
    schedules: list[CourseScheduleItem] = Field(default_factory=list)


class AdminCourseUpdate(BaseModel):
    """更新课程请求"""
    name: str | None = None
    cover_image: str | None = None
    category: str | None = None
    room_id: int | None = None
    tags: str | None = None
    description: str | None = None
    is_hot: bool | None = None
    sort_order: int | None = None
    status: str | None = None
    schedules: list[CourseScheduleItem] | None = None


class AdminTeacherBrief(BaseModel):
    """Admin 教师简要信息"""
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminCourseDetailResponse(AdminCourseItem):
    """Admin 课程详情响应"""
    teacher: AdminTeacherBrief | None = None
    description: str | None = None
    lessons: list[AdminLessonItem] = []


# ── 排课独立 CRUD Schema ──────────────────────────────────────


class CourseScheduleCreate(BaseModel):
    """创建排课记录"""
    teacher_id: int | None = None
    start_date: str | None = None
    time_slots: str | None = None
    price: float = 0
    custom_price: float = 0
    full_package_price: float | None = None
    full_custom_price: float | None = None


class CourseScheduleUpdate(BaseModel):
    """更新排课记录"""
    teacher_id: int | None = None
    start_date: str | None = None
    time_slots: str | None = None
    price: float | None = None
    custom_price: float | None = None
    full_package_price: float | None = None
    full_custom_price: float | None = None


class CourseScheduleResponse(BaseModel):
    """排课记录响应"""
    id: int
    course_id: int
    teacher_id: int | None = None
    start_date: str | None = None
    time_slots: str | None = None
    price: float
    custom_price: float
    full_package_price: float | None = None
    full_custom_price: float | None = None

    model_config = ConfigDict(from_attributes=True)
