from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field, model_validator


class AdminMenuBase(BaseModel):
    parent_id: int | None = None
    type: str = Field(..., pattern="^(directory|menu|button)$")
    title: str = Field(..., min_length=1, max_length=80)
    permission_code: str | None = Field(None, max_length=120)
    path: str | None = Field(None, max_length=255)
    name: str | None = Field(None, max_length=120)
    component: str | None = Field(None, max_length=255)
    redirect: str | None = Field(None, max_length=255)
    icon: str | None = Field(None, max_length=80)
    sort: int = 0
    hidden: bool = False
    keep_alive: bool = False
    enabled: bool = True

    @model_validator(mode="after")
    def validate_by_type(self) -> "AdminMenuBase":
        if self.type in {"directory", "menu"} and not self.component:
            raise ValueError("目录和菜单必须配置 component")
        if self.type == "button" and not self.permission_code:
            raise ValueError("按钮权限必须配置 permission_code")
        return self


class AdminMenuCreate(AdminMenuBase):
    pass


class AdminMenuUpdate(BaseModel):
    parent_id: int | None = None
    type: str | None = Field(None, pattern="^(directory|menu|button)$")
    title: str | None = Field(None, min_length=1, max_length=80)
    permission_code: str | None = Field(None, max_length=120)
    path: str | None = Field(None, max_length=255)
    name: str | None = Field(None, max_length=120)
    component: str | None = Field(None, max_length=255)
    redirect: str | None = Field(None, max_length=255)
    icon: str | None = Field(None, max_length=80)
    sort: int | None = None
    hidden: bool | None = None
    keep_alive: bool | None = None
    enabled: bool | None = None


class AdminMenuNode(BaseModel):
    id: int
    parent_id: int | None = None
    type: str
    title: str
    permission_code: str | None = None
    path: str | None = None
    name: str | None = None
    component: str | None = None
    redirect: str | None = None
    icon: str | None = None
    sort: int
    hidden: bool
    keep_alive: bool
    enabled: bool
    created_at: datetime | None = None
    updated_at: datetime | None = None
    children: list["AdminMenuNode"] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class AdminMenuRouteMeta(BaseModel):
    title: str
    icon: str | None = None
    permissions: list[str]
    hidden: bool
    keepAlive: bool


class AdminMenuRoute(BaseModel):
    path: str
    name: str
    component: str
    redirect: str | None = None
    meta: AdminMenuRouteMeta
    children: list["AdminMenuRoute"] = Field(default_factory=list)


class ComponentOption(BaseModel):
    label: str
    value: str
