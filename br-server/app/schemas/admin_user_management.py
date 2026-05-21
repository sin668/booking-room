from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.admin_auth import AdminRoleSummary


# ---------------------------------------------------------------------------
# Filters / list params
# ---------------------------------------------------------------------------

class AdminUserListParams(BaseModel):
    user_type: str | None = None
    keyword: str | None = Field(None, max_length=100)
    status: str | None = None
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)


# ---------------------------------------------------------------------------
# List item & response
# ---------------------------------------------------------------------------

class AdminUserListItem(BaseModel):
    id: UUID
    phone: str
    nickname: str | None = None
    user_type: str
    status: str
    avatar: str | None = None
    created_at: datetime
    roles: list[AdminRoleSummary] = []
    booking_count: int = 0
    coupon_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    items: list[AdminUserListItem]
    total: int
    page: int
    page_size: int

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Create / Update
# ---------------------------------------------------------------------------

class AdminUserCreate(BaseModel):
    user_type: str = Field(..., min_length=1, max_length=20)
    phone: str | None = Field(None, pattern=r"^1[3-9]\d{9}$")
    username: str | None = Field(None, min_length=1, max_length=50)
    password: str = Field(..., min_length=6, max_length=128)
    nickname: str | None = Field(None, max_length=50)

    @classmethod
    def get_contact_field(cls, data: dict) -> str:
        """Return whichever contact field (phone/username) was provided."""
        return data["phone"] or data["username"]


class AdminUserUpdate(BaseModel):
    nickname: str | None = Field(None, max_length=50)
    email: str | None = Field(None, max_length=255)
    mobile: str | None = Field(None, max_length=20)
    avatar: str | None = Field(None, max_length=512)
    balance: Decimal | None = None
    role_ids: list[int] | None = None


# ---------------------------------------------------------------------------
# Detail
# ---------------------------------------------------------------------------

class AdminUserDetail(BaseModel):
    id: UUID
    phone: str
    nickname: str | None = None
    user_type: str
    username: str | None = None
    email: str | None = None
    mobile: str | None = None
    avatar: str | None = None
    status: str
    balance: int = 0
    is_super_admin: bool = False
    wechat_openid: str | None = None
    invite_code: str | None = None
    created_at: datetime
    updated_at: datetime | None = None
    roles: list[AdminRoleSummary] = []
    booking_count: int = 0
    coupon_count: int = 0

    model_config = ConfigDict(from_attributes=True)


# ---------------------------------------------------------------------------
# Actions
# ---------------------------------------------------------------------------

class AdminResetPassword(BaseModel):
    new_password: str = Field(..., min_length=6, max_length=128)


class AdminToggleStatus(BaseModel):
    target_status: str = Field(..., min_length=1, max_length=20)


class AdminAssignRoles(BaseModel):
    role_ids: list[int]
