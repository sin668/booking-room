from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field


class UserCreate(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    password: str = Field(min_length=6, max_length=20)
    nickname: str | None = None
    sms_code: str = Field(min_length=6, max_length=6)
    captcha_token: str | None = None
    agree_terms: bool = True
    invite_code: str | None = None


class UserLogin(BaseModel):
    phone: str
    password: str


class SendCodeRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    captcha_token: str | None = None


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class UserResponse(BaseModel):
    id: UUID
    phone: str
    nickname: str
    status: str
    wechat_openid: str | None
    invite_code: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
