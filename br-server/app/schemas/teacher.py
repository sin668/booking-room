from decimal import Decimal

from pydantic import BaseModel, ConfigDict


class TeacherResponse(BaseModel):
    id: int
    name: str
    avatar: str | None = None
    title: str | None = None
    rating: Decimal

    model_config = ConfigDict(from_attributes=True)
