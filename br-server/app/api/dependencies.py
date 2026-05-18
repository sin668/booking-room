"""Shared API dependencies."""

import uuid
from dataclasses import dataclass

from fastapi import Depends, Header, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
from app.services.admin_auth_service import AdminAuthService
from app.services.jwt_service import JWTService

security = HTTPBearer(auto_error=False)


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> uuid.UUID:
    """Extract and validate the current user ID from the access token."""
    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供认证凭证",
        )

    jwt_svc = JWTService(config=settings, redis=redis)
    user_id = await jwt_svc.get_current_user_id(credentials.credentials)
    return user_id


@dataclass(frozen=True)
class AdminContext:
    admin_id: uuid.UUID
    username: str
    is_super_admin: bool
    permission_codes: set[str]
    menu_ids: set[int]


async def get_current_admin_context(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    x_admin_token: str | None = Header(None),
    db: AsyncSession = Depends(get_db),
    redis=Depends(get_redis),
) -> AdminContext:
    """Resolve the current administrator from Bearer or legacy admin token."""
    if x_admin_token is not None:
        if settings.ADMIN_TOKEN and x_admin_token == settings.ADMIN_TOKEN:
            return AdminContext(
                admin_id=uuid.UUID(int=0),
                username="legacy-admin",
                is_super_admin=True,
                permission_codes=set(),
                menu_ids=set(),
            )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员凭证",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="未提供管理员认证凭证",
        )

    admin_id = AdminAuthService.verify_access_token(credentials.credentials, settings)
    service = AdminAuthService(db, settings)
    admin = await service.get_admin_by_id(admin_id)
    menu_ids = {
        menu.id
        for role in admin.roles
        if role.status == "active"
        for menu in role.menus
        if menu.enabled
    }
    return AdminContext(
        admin_id=admin.id,
        username=admin.username,
        is_super_admin=admin.is_super_admin,
        permission_codes=await service.permission_codes_for(admin),
        menu_ids=menu_ids,
    )


async def get_current_admin(
    context: AdminContext = Depends(get_current_admin_context),
) -> AdminContext:
    """Compatibility entrypoint for legacy admin route dependencies."""
    return context


def require_admin_permission(permission_code: str):
    async def checker(
        context: AdminContext | None = Depends(get_current_admin),
    ) -> AdminContext | None:
        if context is None:
            return None
        if context.is_super_admin or permission_code in context.permission_codes:
            return context
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="无权执行该操作",
        )

    return checker
