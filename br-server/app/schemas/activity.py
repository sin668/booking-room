from pydantic import BaseModel, ConfigDict


class ActivityResponse(BaseModel):
    id: int
    title: str
    description: str | None
    cover_image: str | None
    participant_count: int

    model_config = ConfigDict(from_attributes=True)
