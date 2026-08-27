from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class TeacherBrief(BaseModel):
    """教师简要信息，嵌套在课程响应中"""
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class HotCourseItem(BaseModel):
    """热门课程简要信息，嵌套在培训室响应中"""
    id: int
    name: str
    cover_image: str | None = None
    teacher: TeacherBrief | None = None
    price: Decimal
    enrollment_count: int
    schedule: str | None = None
    start_date: str | None = None
    tags: list[str] = []

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [tag.strip() for tag in v.split(",") if tag.strip()]


class TrainingRoomResponse(BaseModel):
    """培训室列表响应中的单个培训室"""
    id: int
    name: str
    description: str | None = None
    cover_image: str | None = None
    environment_images: list[str] | None = None
    address: str
    city_id: int | None = None
    city_name: str | None = None
    business_hours: str | None = None
    status: str
    room_type: str
    min_price: Decimal
    rating: Decimal
    hot_courses: list[HotCourseItem] = []

    model_config = ConfigDict(from_attributes=True)


class TrainingRoomListResponse(BaseModel):
    items: list[TrainingRoomResponse]
    total: int
    page: int
    page_size: int


class CourseResponse(BaseModel):
    """课程列表响应中的单个课程"""
    id: int
    name: str
    cover_image: str | None = None
    teacher: TeacherBrief | None = None
    category: str
    price: Decimal
    custom_price: Decimal = Decimal("0")
    full_package_price: Decimal | None = None
    rating: Decimal
    enrollment_count: int
    schedule: str | None = None
    start_date: str | None = None
    tags: list[str] = []
    status: str
    is_hot: bool = False
    room_id: int
    room_name: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """将逗号分隔字符串解析为列表，None 或空字符串返回空列表"""
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [tag.strip() for tag in v.split(",") if tag.strip()]


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int


class TrainingRoomDetailResponse(BaseModel):
    """培训室详情响应"""

    # 房间基本信息
    id: int
    name: str
    description: str | None = None
    cover_image: str | None = None
    environment_images: list[str] | None = None
    address: str
    business_hours: str | None = None
    status: str
    room_type: str
    min_price: Decimal
    city_id: int | None = None
    city_name: str | None = None
    rating: Decimal

    # 教室概况统计
    classroom_count: int
    class_capacity: str
    teacher_count: int
    total_students: int

    # 名师团队（使用 TeacherBrief 与 CourseResponse 保持一致）
    teachers: list[TeacherBrief] = []

    # 课程列表（复用现有 CourseResponse）
    courses: list[CourseResponse] = []

    model_config = ConfigDict(from_attributes=True)


class LessonResponse(BaseModel):
    """课时响应 Schema"""
    id: int
    title: str
    description: str | None = None
    duration_minutes: int | None = None
    sort_order: int
    is_free_preview: bool = False
    model_config = ConfigDict(from_attributes=True)


class RoomBrief(BaseModel):
    """轻量教室信息，嵌套在课程详情中"""
    id: int
    name: str
    address: str
    cover_image: str | None = None
    model_config = ConfigDict(from_attributes=True)


class RelatedCourseItem(BaseModel):
    """相关课程推荐项"""
    id: int
    name: str
    cover_image: str | None = None
    price: Decimal
    model_config = ConfigDict(from_attributes=True)


class CourseDetailResponse(BaseModel):
    """课程详情响应"""
    id: int
    name: str
    cover_image: str | None = None
    category: str
    price: Decimal
    custom_price: Decimal = Decimal("0")
    full_package_price: Decimal | None = None
    rating: Decimal
    enrollment_count: int
    schedule: str | None = None
    start_date: str | None = None
    tags: list[str] = []
    status: str
    is_hot: bool = False
    description: str | None = None
    teacher: TeacherBrief | None = None
    room: RoomBrief | None = None
    lessons: list[LessonResponse] = []
    related_courses: list[RelatedCourseItem] = []

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [tag.strip() for tag in v.split(",") if tag.strip()]
