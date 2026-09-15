from decimal import Decimal

from pydantic import BaseModel


class SearchRoomItem(BaseModel):
    id: int
    name: str
    address: str
    cover_image: str | None = None
    room_type: str
    min_price: Decimal


class SearchCourseItem(BaseModel):
    id: int
    name: str
    cover_image: str | None = None
    room_name: str = ""
    teacher_name: str | None = None
    price: Decimal = 0
    category: str | None = None


class SearchTeacherItem(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    specialty: str | None = None


class SearchResponse(BaseModel):
    rooms: list[SearchRoomItem] = []
    courses: list[SearchCourseItem] = []
    teachers: list[SearchTeacherItem] = []
