from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, get_current_admin_context
from app.core.config import settings
from app.core.database import get_db
from app.schemas.admin_auth import (
    AdminCurrentResponse,
    AdminLoginRequest,
    AdminMessageResponse,
    AdminPasswordUpdate,
    AdminProfileUpdate,
    AdminTokenResponse,
    admin_profile_from_model,
)
from app.models.admin_user import AdminUser
from app.services.admin_auth_service import AdminAuthService

router = APIRouter(prefix="/api/v1/admin/auth", tags=["admin-auth"])


@router.post("/login", response_model=AdminTokenResponse)
async def login(
    data: AdminLoginRequest,
    db: AsyncSession = Depends(get_db),
) -> AdminTokenResponse:
    _admin, token = await AdminAuthService(db, settings).login(data.username, data.password)
    return AdminTokenResponse(
        access_token=token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/me", response_model=AdminCurrentResponse)
async def me(
    context: AdminContext = Depends(get_current_admin_context),
    db: AsyncSession = Depends(get_db),
) -> AdminCurrentResponse:
    service = AdminAuthService(db, settings)
    if context.admin_id.int == 0 and context.is_super_admin:
        admin = AdminUser(
            id=context.admin_id,
            username=context.username,
            password_hash="",
            nickname="超级管理员",
            is_super_admin=True,
        )
        permissions = await service.permissions_for(admin)
    else:
        admin = await service.get_admin_by_id(context.admin_id)
        permissions = await service.permissions_for(admin)
    return AdminCurrentResponse(
        **admin_profile_from_model(admin),
        roles=service.roles_for(admin),
        permissions=permissions,
    )


@router.put("/profile", response_model=AdminCurrentResponse)
async def update_profile(
    data: AdminProfileUpdate,
    context: AdminContext = Depends(get_current_admin_context),
    db: AsyncSession = Depends(get_db),
) -> AdminCurrentResponse:
    service = AdminAuthService(db, settings)
    admin = await service.get_admin_by_id(context.admin_id)
    admin = await service.update_profile(admin, data.model_dump(exclude_unset=True))
    return AdminCurrentResponse(
        **admin_profile_from_model(admin),
        roles=service.roles_for(admin),
        permissions=await service.permissions_for(admin),
    )


@router.put("/password", response_model=AdminMessageResponse, status_code=status.HTTP_200_OK)
async def update_password(
    data: AdminPasswordUpdate,
    context: AdminContext = Depends(get_current_admin_context),
    db: AsyncSession = Depends(get_db),
) -> AdminMessageResponse:
    service = AdminAuthService(db, settings)
    admin = await service.get_admin_by_id(context.admin_id)
    await service.update_password(admin, data.old_password, data.new_password)
    return AdminMessageResponse(message="密码已更新")
