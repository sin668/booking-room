from __future__ import annotations

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, model_validator

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
    phone: str | None = Field(None, max_length=11)
    username: str | None = Field(None, max_length=50)
    password: str

    @model_validator(mode="after")
    def validate_login_fields(self) -> "UserLogin":
        if not self.phone and not self.username:
            raise ValueError("手机号或用户名至少需要提供一个")
        return self


class SendCodeRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    captcha_token: str | None = None


class WechatLoginRequest(BaseModel):
    code: str = Field(min_length=1)


class WechatPhoneBindRequest(BaseModel):
    code: str = Field(min_length=1)


class WechatSMSBindRequest(BaseModel):
    phone: str = Field(pattern=r"^1[3-9]\d{9}$")
    sms_code: str = Field(min_length=6, max_length=6)


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str | None = None
    token_type: str = "bearer"
    expires_in: int


class RefreshRequest(BaseModel):
    refresh_token: str | None = None


class UserResponse(BaseModel):
    id: UUID
    phone: str | None = None
    nickname: str
    status: str
    user_type: str
    username: str | None = None
    username_updated_at: datetime | None = None
    email: str | None = None
    mobile: str | None = None
    avatar: str | None = None
    balance: int = 0
    membership_level: str = "none"
    is_super_admin: bool = False
    roles: list[AdminRoleSummary] = []
    wechat_openid: str | None = None
    invite_code: str | None = None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileResponse(BaseModel):
    id: UUID
    phone: str | None = None
    username: str
    username_updated_at: datetime | None = None
    nickname: str | None = None
    avatar: str | None = None
    status: str
    user_type: str
    membership_level: str = "none"
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserProfileUpdate(BaseModel):
    username: str | None = Field(None, min_length=6, max_length=32)
    nickname: str | None = Field(None, max_length=50)
    avatar: str | None = Field(None, max_length=512)

    model_config = ConfigDict(extra="forbid")


class DeactivationRiskReason(BaseModel):
    code: str
    message: str
    count: int = 0
    amount: str | None = None


class AccountSecuritySummary(BaseModel):
    phone_bound: bool
    phone_masked: str | None = None
    wechat_bound: bool
    identity_status: str
    identity_masked: str | None = None
    account_status: str
    deactivation_blocked: bool
    deactivation_risks: list[DeactivationRiskReason] = []


class ChangePasswordRequest(BaseModel):
    old_password: str = Field(min_length=1, max_length=72)
    new_password: str = Field(min_length=6, max_length=20)
    confirm_password: str = Field(min_length=6, max_length=20)


class ChangePasswordResponse(BaseModel):
    message: str


class IdentityVerificationRequest(BaseModel):
    real_name: str = Field(min_length=2, max_length=50)
    id_card_number: str = Field(min_length=18, max_length=18)


class IdentityVerificationResponse(BaseModel):
    status: str
    real_name: str
    id_card_masked: str


class AccountDeactivationResponse(BaseModel):
    status: str
    message: str
    blocked: bool = False
    risks: list[DeactivationRiskReason] = []
