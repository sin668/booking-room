from uuid import UUID

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_permission
from app.core.database import get_db
from app.schemas.admin_auth import AdminRoleSummary
from app.schemas.admin_user_management import (
    AdminAssignRoles,
    AdminResetPassword,
    AdminToggleStatus,
    AdminUserCreate,
    AdminUserDetail,
    AdminUserListResponse,
    AdminUserUpdate,
)
from app.services.admin_user_service import AdminUserService

router = APIRouter(prefix="/api/v1/admin/users", tags=["admin-users"])


@router.get("", response_model=AdminUserListResponse)
async def list_users(
    user_type: str | None = None,
    keyword: str | None = None,
    status_filter: str | None = None,
    page: int = 1,
    page_size: int = 20,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("system:user:view")),
) -> AdminUserListResponse:
    return await AdminUserService(db).list_users(
        user_type=user_type, keyword=keyword, status=status_filter,
        page=page, page_size=page_size,
    )


@router.post("", response_model=AdminUserDetail, status_code=status.HTTP_201_CREATED)
async def create_user(
    data: AdminUserCreate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("system:user:create")),
) -> AdminUserDetail:
    return await AdminUserService(db).create_user(data)


@router.get("/{user_id}", response_model=AdminUserDetail)
async def get_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("system:user:view")),
) -> AdminUserDetail:
    return await AdminUserService(db).get_user(user_id)


@router.put("/{user_id}", response_model=AdminUserDetail)
async def update_user(
    user_id: UUID,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("system:user:update")),
) -> AdminUserDetail:
    return await AdminUserService(db).update_user(user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_user(
    user_id: UUID,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("system:user:delete")),
) -> None:
    await AdminUserService(db).delete_user(user_id)


@router.put("/{user_id}/reset-password", response_model=AdminUserDetail)
async def reset_password(
    user_id: UUID,
    data: AdminResetPassword,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("system:user:reset-password")),
) -> AdminUserDetail:
    return await AdminUserService(db).reset_password(user_id, data.new_password)


@router.put("/{user_id}/status", response_model=AdminUserDetail)
async def toggle_status(
    user_id: UUID,
    data: AdminToggleStatus,
    db: AsyncSession = Depends(get_db),
    _=Depends(require_admin_permission("system:user:status")),
) -> AdminUserDetail:
    return await AdminUserService(db).toggle_status(user_id, data.target_status)