"""管理端老师管理 Pydantic schemas。"""

from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator


class QualificationItem(BaseModel):
    """资质认证条目。"""

    name: str = Field(..., max_length=100)
    sub: str | None = Field(None, max_length=100)


class AdminTeacherCreate(BaseModel):
    name: str = Field(..., max_length=50)
    avatar: str | None = Field(None, max_length=512)
    title: str | None = Field(None, max_length=50)
    specialty: str | None = Field(None, max_length=50)
    teaching_years: int = Field(0, ge=0, le=100)
    education: str | None = Field(None, pattern="^(本科|硕士|博士)$")
    school: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=1000)
    teaching_tags: list[str] = []
    qualifications: list[QualificationItem] = []
    room_ids: list[int] = []
    status: str = Field("active", pattern="^(active|inactive)$")


class AdminTeacherUpdate(BaseModel):
    name: str | None = Field(None, max_length=50)
    avatar: str | None = Field(None, max_length=512)
    title: str | None = Field(None, max_length=50)
    specialty: str | None = Field(None, max_length=50)
    teaching_years: int | None = Field(None, ge=0, le=100)
    education: str | None = Field(None, pattern="^(本科|硕士|博士)$")
    school: str | None = Field(None, max_length=100)
    bio: str | None = Field(None, max_length=1000)
    teaching_tags: list[str] | None = None
    qualifications: list[QualificationItem] | None = None
    room_ids: list[int] | None = None
    status: str | None = Field(None, pattern="^(active|inactive)$")


class AdminTeacherStatusUpdate(BaseModel):
    status: str = Field(..., pattern="^(active|inactive)$")


class TeacherAvailableTimeSlotsUpdate(BaseModel):
    """老师可排课时间段更新。"""
    available_time_slots: list[dict[str, Any]] | None = None


class AdminTeacherListItem(BaseModel):
    """老师列表项，兼容排课老师下拉（id/name/avatar/title）。"""

    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    specialty: str | None = None
    teaching_years: int = 0
    education: str | None = None
    school: str | None = None
    rating: Decimal
    student_count: int = 0
    course_count: int = 0
    status: str = "active"
    available_time_slots: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminTeacherListResponse(BaseModel):
    items: list[AdminTeacherListItem]
    total: int
    page: int
    page_size: int


class TeacherRoomBrief(BaseModel):
    id: int
    name: str
    room_type: str


class AdminTeacherDetail(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    specialty: str | None = None
    teaching_years: int = 0
    education: str | None = None
    school: str | None = None
    rating: Decimal
    bio: str | None = None
    student_count: int = 0
    course_count: int = 0
    status: str = "active"
    teaching_tags: list[str] = []
    qualifications: list[dict[str, Any]] = []
    room_ids: list[int] = []
    rooms: list[TeacherRoomBrief] = []
    created_at: datetime
    updated_at: datetime

    @field_validator("teaching_tags", mode="before")
    @classmethod
    def parse_tags(cls, v):
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
