from pydantic import BaseModel, ConfigDict


class BannerResponse(BaseModel):
    id: int
    image_url: str
    title: str
    subtitle: str | None
    cta_text: str | None
    link_type: str
    link_value: str | None
    sort_order: int

    model_config = ConfigDict(from_attributes=True)
