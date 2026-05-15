from pydantic import BaseModel, ConfigDict


class CityResponse(BaseModel):
    id: int
    name: str
    province: str

    model_config = ConfigDict(from_attributes=True)
