from __future__ import annotations

from fastapi import HTTPException, status
from sqlalchemy import func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.dependencies import AdminContext
from app.models.admin_menu import AdminMenu
from app.models.admin_role import admin_role_menus
from app.schemas.admin_menu import (
    AdminMenuCreate,
    AdminMenuNode,
    AdminMenuRoute,
    AdminMenuRouteMeta,
    AdminMenuUpdate,
    ComponentOption,
)

COMPONENT_WHITELIST = {
    "LAYOUT",
    "/dashboard/console/console",
    "/system/menu/menu",
    "/system/role/role",
    "/setting/account/account",
    "/setting/system/system",
    "/room/list/index",
    "/room/seats/index",
    "/activity/list/index",
    "/booking/list/index",
}


def component_options() -> list[ComponentOption]:
    return [ComponentOption(label=value, value=value) for value in sorted(COMPONENT_WHITELIST)]


class AdminMenuService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    @staticmethod
    def validate_node(menu_type: str | None, component: str | None, permission_code: str | None) -> None:
        if menu_type in {"directory", "menu"} and component not in COMPONENT_WHITELIST:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="菜单组件不在白名单中")
        if menu_type == "button" and not permission_code:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, detail="按钮权限码不能为空")

    async def list_tree(self) -> list[AdminMenuNode]:
        menus = await self._list_all()
        return self._build_model_tree(menus)

    async def create(self, data: AdminMenuCreate) -> AdminMenu:
        self.validate_node(data.type, data.component, data.permission_code)
        if data.permission_code and await self._permission_code_exists(data.permission_code):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单权限码已存在")
        menu = AdminMenu(**data.model_dump())
        self._db.add(menu)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单权限码已存在") from exc
        await self._db.refresh(menu)
        return menu

    async def update(self, menu_id: int, data: AdminMenuUpdate) -> AdminMenuNode:
        menu = await self._get(menu_id)
        updates = data.model_dump(exclude_unset=True)
        final_type = updates.get("type", menu.type)
        final_component = updates.get("component", menu.component)
        final_permission_code = updates.get("permission_code", menu.permission_code)
        self.validate_node(final_type, final_component, final_permission_code)
        if (
            final_permission_code
            and final_permission_code != menu.permission_code
            and await self._permission_code_exists(final_permission_code)
        ):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单权限码已存在")
        for key, value in updates.items():
            setattr(menu, key, value)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单权限码已存在") from exc
        tree = self._build_model_tree(await self._list_all())
        return self._find_node(tree, menu_id)

    async def delete(self, menu_id: int) -> None:
        menu = await self._get(menu_id)
        child_count = await self._db.scalar(select(func.count()).select_from(AdminMenu).where(AdminMenu.parent_id == menu_id))
        if child_count:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单存在子节点，无法删除")
        role_count = await self._db.scalar(
            select(func.count()).select_from(admin_role_menus).where(admin_role_menus.c.admin_menu_id == menu_id)
        )
        if role_count:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="菜单已被角色授权，无法删除")
        await self._db.delete(menu)
        await self._db.flush()

    async def route_tree(self, context: AdminContext) -> list[AdminMenuRoute]:
        menus = [
            menu
            for menu in await self._list_all()
            if menu.enabled and menu.type in {"directory", "menu"}
        ]
        if context.is_super_admin:
            allowed_ids = {menu.id for menu in menus}
        else:
            allowed_ids = {menu.id for menu in menus if menu.permission_code in context.permission_codes}
            allowed_ids.update(menu.id for menu in menus if menu.id in context.menu_ids)

        return self._build_route_tree(menus, allowed_ids, context.is_super_admin)

    async def _get(self, menu_id: int) -> AdminMenu:
        menu = await self._db.get(AdminMenu, menu_id)
        if menu is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="菜单不存在")
        return menu

    async def _list_all(self) -> list[AdminMenu]:
        stmt = select(AdminMenu).options(selectinload(AdminMenu.roles)).order_by(AdminMenu.sort, AdminMenu.id)
        return list((await self._db.execute(stmt)).scalars().unique().all())

    async def _permission_code_exists(self, permission_code: str) -> bool:
        existing_id = await self._db.scalar(
            select(AdminMenu.id).where(AdminMenu.permission_code == permission_code)
        )
        return existing_id is not None

    def _build_model_tree(self, menus: list[AdminMenu]) -> list[AdminMenuNode]:
        by_parent: dict[int | None, list[AdminMenu]] = {}
        for menu in menus:
            by_parent.setdefault(menu.parent_id, []).append(menu)

        def build(menu: AdminMenu) -> AdminMenuNode:
            return AdminMenuNode(
                id=menu.id,
                parent_id=menu.parent_id,
                type=menu.type,
                title=menu.title,
                permission_code=menu.permission_code,
                path=menu.path,
                name=menu.name,
                component=menu.component,
                redirect=menu.redirect,
                icon=menu.icon,
                sort=menu.sort,
                hidden=menu.hidden,
                keep_alive=menu.keep_alive,
                enabled=menu.enabled,
                created_at=menu.created_at,
                updated_at=menu.updated_at,
                children=[build(child) for child in by_parent.get(menu.id, [])],
            )

        return [build(menu) for menu in by_parent.get(None, [])]

    def _find_node(self, tree: list[AdminMenuNode], menu_id: int) -> AdminMenuNode | None:
        for node in tree:
            if node.id == menu_id:
                return node
            found = self._find_node(node.children, menu_id)
            if found:
                return found
        return None

    def _build_route_tree(
        self,
        menus: list[AdminMenu],
        allowed_ids: set[int],
        is_super_admin: bool,
    ) -> list[AdminMenuRoute]:
        by_parent: dict[int | None, list[AdminMenu]] = {}
        for menu in menus:
            by_parent.setdefault(menu.parent_id, []).append(menu)

        def build(parent_id: int | None) -> list[AdminMenuRoute]:
            routes: list[AdminMenuRoute] = []
            for menu in by_parent.get(parent_id, []):
                children = build(menu.id)
                allowed = is_super_admin or menu.id in allowed_ids or bool(children)
                if not allowed:
                    continue
                routes.append(
                    AdminMenuRoute(
                        path=menu.path or "",
                        name=menu.name or f"AdminMenu{menu.id}",
                        component=menu.component or "LAYOUT",
                        redirect=menu.redirect,
                        meta=AdminMenuRouteMeta(
                            title=menu.title,
                            icon=menu.icon,
                            permissions=[menu.permission_code] if menu.permission_code else [],
                            hidden=menu.hidden,
                            keepAlive=menu.keep_alive,
                        ),
                        children=children,
                    )
                )
            return routes

        return build(None)
