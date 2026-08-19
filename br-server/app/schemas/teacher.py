from decimal import Decimal
from typing import Any

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


class TeacherRoomItem(BaseModel):
    """教师所属培训室/综合室简要信息"""
    id: int
    name: str
    room_type: str


class TeacherDetailResponse(BaseModel):
    """教师详情响应"""
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0
    specialty: str | None = None
    teaching_years: int = 0
    education: str | None = None
    school: str | None = None
    status: str = "active"
    teaching_tags: list[str] = []
    qualifications: list[dict[str, Any]] = []
    rooms: list[TeacherRoomItem] = []
    courses: list[TeacherCourseItem] = []

    @field_validator("teaching_tags", mode="before")
    @classmethod
    def parse_teaching_tags(cls, v):
        if v is None or v == "":
            return []
        if isinstance(v, list):
            return v
        return [tag.strip() for tag in v.split(",") if tag.strip()]

    @field_validator("qualifications", mode="before")
    @classmethod
    def parse_qualifications(cls, v):
        # 库表 qualifications 为 NULL 时容忍为空列表，避免 model_validate 报错
        if v is None:
            return []
        if isinstance(v, list):
            return v
        return []

    model_config = ConfigDict(from_attributes=True)
