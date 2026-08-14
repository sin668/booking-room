from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class TeacherBrief(BaseModel):
    """教师简要信息，嵌套在课程响应中"""
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal

    model_config = ConfigDict(from_attributes=True)


class HotCourseItem(BaseModel):
    """热门课程简要信息，嵌套在培训室响应中"""
    id: int
    name: str
    cover_image: str | None = None
    teacher: TeacherBrief | None = None
    price: Decimal
    enrollment_count: int


class TrainingRoomResponse(BaseModel):
    """培训室列表响应中的单个培训室"""
    id: int
    name: str
    description: str | None = None
    cover_image: str | None = None
    address: str
    city_id: int | None = None
    city_name: str | None = None
    business_hours: str | None = None
    status: str
    room_type: str
    min_price: Decimal
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
    rating: Decimal
    enrollment_count: int
    schedule: str | None = None
    tags: list[str] = []
    status: str
    room_id: int
    room_name: str

    model_config = ConfigDict(from_attributes=True)

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        """将逗号分隔字符串解析为列表，None 或空字符串返回空列表"""
        if v is None or v == "":
            return []
        return [tag.strip() for tag in v.split(",") if tag.strip()]


class CourseListResponse(BaseModel):
    items: list[CourseResponse]
    total: int
    page: int
    page_size: int
