from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.admin_menu import AdminMenuNode


class AdminRoleBase(BaseModel):
    name: str = Field(..., min_length=1, max_length=50)
    code: str = Field(..., min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)
    status: str = Field(default="active", pattern="^(active|disabled)$")
    is_default: bool = False


class AdminRoleCreate(AdminRoleBase):
    pass


class AdminRoleUpdate(BaseModel):
    name: str | None = Field(None, min_length=1, max_length=50)
    code: str | None = Field(None, min_length=1, max_length=50)
    description: str | None = Field(None, max_length=255)
    status: str | None = Field(None, pattern="^(active|disabled)$")
    is_default: bool | None = None


class AdminRoleResponse(BaseModel):
    id: int
    name: str
    code: str
    description: str | None = None
    status: str
    is_default: bool
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class AdminRoleListResponse(BaseModel):
    items: list[AdminRoleResponse]
    total: int
    page: int
    page_size: int


class AdminRoleMenusResponse(BaseModel):
    menus: list[AdminMenuNode]
    checked_menu_ids: list[int]


class AdminRoleMenuUpdate(BaseModel):
    menu_ids: list[int]
