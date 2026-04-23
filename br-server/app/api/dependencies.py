"""Shared API dependencies."""

import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.redis import get_redis
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


from fastapi import Header


async def get_current_admin(x_admin_token: str | None = Header(None)) -> None:
    """Validate admin token from X-Admin-Token header."""
    if not settings.ADMIN_TOKEN or x_admin_token != settings.ADMIN_TOKEN:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="无效的管理员凭证",
        )
