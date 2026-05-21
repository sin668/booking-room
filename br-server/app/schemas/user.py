from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.admin_auth import AdminRoleSummary


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
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class UserResponse(BaseModel):
    id: UUID
    phone: str
    nickname: str
    status: str
    user_type: str
    username: str | None = None
    email: str | None = None
    mobile: str | None = None
    avatar: str | None = None
    balance: int = 0
    is_super_admin: bool = False
    roles: list[AdminRoleSummary] = []
    wechat_openid: str | None = None
    invite_code: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)
