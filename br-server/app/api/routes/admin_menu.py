from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import AdminContext, get_current_admin, require_admin_permission
from app.core.database import get_db
from app.schemas.admin_menu import AdminMenuCreate, AdminMenuNode, AdminMenuRoute, AdminMenuUpdate, ComponentOption
from app.services.admin_menu_service import AdminMenuService, component_options

router = APIRouter(prefix="/api/v1/admin/menus", tags=["admin-menus"])


@router.get("", response_model=list[AdminMenuNode], dependencies=[Depends(require_admin_permission("system:menu:view"))])
async def list_menus(db: AsyncSession = Depends(get_db)) -> list[AdminMenuNode]:
    return await AdminMenuService(db).list_tree()


@router.post(
    "",
    response_model=AdminMenuNode,
    status_code=status.HTTP_201_CREATED,
    dependencies=[Depends(require_admin_permission("system:menu:create"))],
)
async def create_menu(data: AdminMenuCreate, db: AsyncSession = Depends(get_db)) -> AdminMenuNode:
    return await AdminMenuService(db).create(data)


@router.get(
    "/component-options",
    response_model=list[ComponentOption],
    dependencies=[Depends(require_admin_permission("system:menu:view"))],
)
async def get_component_options() -> list[ComponentOption]:
    return component_options()


@router.put(
    "/{menu_id}",
    response_model=AdminMenuNode,
    dependencies=[Depends(require_admin_permission("system:menu:update"))],
)
async def update_menu(menu_id: int, data: AdminMenuUpdate, db: AsyncSession = Depends(get_db)) -> AdminMenuNode:
    return await AdminMenuService(db).update(menu_id, data)


@router.delete(
    "/{menu_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    dependencies=[Depends(require_admin_permission("system:menu:delete"))],
)
async def delete_menu(menu_id: int, db: AsyncSession = Depends(get_db)) -> None:
    await AdminMenuService(db).delete(menu_id)


@router.get("/routes", response_model=list[AdminMenuRoute])
async def get_routes(
    context: AdminContext = Depends(get_current_admin),
    db: AsyncSession = Depends(get_db),
) -> list[AdminMenuRoute]:
    if context is None:
        return []
    return await AdminMenuService(db).route_tree(context)
