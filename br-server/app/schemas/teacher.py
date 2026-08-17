from decimal import Decimal

from pydantic import BaseModel, ConfigDict, field_validator


class TeacherResponse(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class TeacherCourseItem(BaseModel):
    """教师详情中的课程项"""
    id: int
    name: str
    cover_image: str | None = None
    category: str
    price: Decimal
    rating: Decimal
    enrollment_count: int
    schedule: str | None = None
    tags: list[str] = []
    status: str
    room_id: int
    room_name: str
    lesson_count: int = 0

    @field_validator("tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [tag.strip() for tag in v.split(",") if tag.strip()]


class TeacherDetailResponse(BaseModel):
    """教师详情响应"""
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0
    courses: list[TeacherCourseItem] = []

    model_config = ConfigDict(from_attributes=True)
