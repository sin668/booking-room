import uuid
from datetime import datetime
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdminLoginRequest(BaseModel):
    username: str = Field(..., min_length=1, max_length=50)
    password: str = Field(..., min_length=1, max_length=128)


class AdminTokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    expires_in: int


class AdminRoleSummary(BaseModel):
    id: int
    name: str
    code: str

    model_config = ConfigDict(from_attributes=True)


class AdminPermissionItem(BaseModel):
    label: str
    value: str


class AdminCurrentResponse(BaseModel):
    id: uuid.UUID
    username: str
    nickname: str | None = None
    email: str | None = None
    mobile: str | None = None
    avatar: str | None = None
    is_super_admin: bool
    roles: list[AdminRoleSummary]
    permissions: list[AdminPermissionItem]
    created_at: datetime | None = None
    updated_at: datetime | None = None


class AdminProfileUpdate(BaseModel):
    nickname: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    mobile: str | None = Field(None, max_length=20)
    avatar: str | None = Field(None, max_length=512)

    model_config = ConfigDict(extra="forbid")


class AdminPasswordUpdate(BaseModel):
    old_password: str = Field(..., min_length=1, max_length=128)
    new_password: str = Field(..., min_length=6, max_length=128)
    confirm_password: str = Field(..., min_length=6, max_length=128)

    @model_validator(mode="after")
    def passwords_match(self) -> "AdminPasswordUpdate":
        if self.new_password != self.confirm_password:
            raise ValueError("确认密码与新密码不一致")
        return self


class AdminMessageResponse(BaseModel):
    message: str


def admin_profile_from_model(admin: Any) -> dict[str, Any]:
    return {
        "id": admin.id,
        "username": admin.username,
        "nickname": admin.nickname,
        "email": admin.email,
        "mobile": admin.mobile,
        "avatar": admin.avatar,
        "is_super_admin": admin.is_super_admin,
        "created_at": admin.created_at,
        "updated_at": admin.updated_at,
    }
