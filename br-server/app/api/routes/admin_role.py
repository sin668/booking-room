from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import require_admin_permission
from app.core.database import get_db
from app.schemas.admin_role import (
    AdminRoleCreate,
    AdminRoleListResponse,
    AdminRoleMenuUpdate,
    AdminRoleMenusResponse,
    AdminRoleResponse,
    AdminRoleUpdate,
)
from app.services.admin_role_service import AdminRoleService

router = APIRouter(prefix="/api/v1/admin/roles", tags=["admin-roles"])


@router.get("", response_model=AdminRoleListResponse, dependencies=[Depends(require_admin_permission("system:role:view"))])
async def list_roles(
    page: int = 1,
    page_size: int = 10,
    keyword: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> AdminRoleListResponse:
    roles, total = await AdminRoleService(db).list_roles(page=page, page_size=page_size, keyword=keyword)
    return AdminRoleListResponse(items=roles, total=total, page=page, page_size=page_size)


@router.post(
    "",
    response_model=AdminRoleResponse,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_permission("system:role:create"))],
)
async def create_role(data: AdminRoleCreate, db: AsyncSession = Depends(get_db)) -> AdminRoleResponse:
    return await AdminRoleService(db).create(data)


@router.put(
    "/{role_id}",
    response_model=AdminRoleResponse,
    dependencies=[Depends(require_admin_permission("system:role:update"))],
)
async def update_role(role_id: int, data: AdminRoleUpdate, db: AsyncSession = Depends(get_db)) -> AdminRoleResponse:
    return await AdminRoleService(db).update(role_id, data)


@router.delete(
    "/{role_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin_permission("system:role:delete"))],
)
async def delete_role(role_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await AdminRoleService(db).delete(role_id)


@router.get(
    "/{role_id}/menus",
    response_model=AdminRoleMenusResponse,
    dependencies=[Depends(require_admin_permission("system:role:view"))],
)
async def get_role_menus(role_id: int, db: AsyncSession = Depends(get_db)) -> AdminRoleMenusResponse:
    menus, checked = await AdminRoleService(db).role_menus(role_id)
    return AdminRoleMenusResponse(menus=menus, checked_menu_ids=checked)


@router.put(
    "/{role_id}/menus",
    response_model=AdminRoleMenusResponse,
    dependencies=[Depends(require_admin_permission("system:role:assign"))],
)
async def update_role_menus(
    role_id: int,
    data: AdminRoleMenuUpdate,
    db: AsyncSession = Depends(get_db),
) -> AdminRoleMenusResponse:
    service = AdminRoleService(db)
    await service.save_role_menus(role_id, data.menu_ids)
    menus, checked = await service.role_menus(role_id)
    return AdminRoleMenusResponse(menus=menus, checked_menu_ids=checked)
