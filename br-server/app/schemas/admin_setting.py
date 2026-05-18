from pydantic import BaseModel, EmailStr, Field


class BasicSettings(BaseModel):
    site_name: str = ""
    icp_code: str = ""
    contact_phone: str = ""
    contact_address: str = ""
    login_captcha: bool = False
    system_open: bool = True
    close_text: str = ""
    login_desc: str = ""


class EmailSettings(BaseModel):
    smtp_host: str = ""
    smtp_port: int | None = None
    smtp_username: str = ""
    smtp_sender: str = ""
    smtp_tls: bool = True
    smtp_password_set: bool = False


class EmailSettingsUpdate(BaseModel):
    smtp_host: str | None = None
    smtp_port: int | None = Field(None, ge=1, le=65535)
    smtp_username: str | None = None
    smtp_password: str | None = None
    smtp_sender: str | None = None
    smtp_tls: bool | None = None


class SettingsResponse(BaseModel):
    basic: BasicSettings
    email: EmailSettings


class EmailTestRequest(BaseModel):
    to_email: EmailStr


class EmailTestResponse(BaseModel):
    message: str
