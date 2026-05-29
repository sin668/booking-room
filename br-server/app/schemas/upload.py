from pydantic import BaseModel


class UploadResponse(BaseModel):
    url: str
    object_key: str
    size: int
    content_type: str
