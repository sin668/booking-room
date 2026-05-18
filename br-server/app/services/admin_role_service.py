from fastapi import HTTPException, status
from sqlalchemy import func, or_, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.schemas.admin_role import AdminRoleCreate, AdminRoleUpdate
from app.services.admin_menu_service import AdminMenuService


class AdminRoleService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_roles(
        self,
        page: int = 1,
        page_size: int = 10,
        keyword: str | None = None,
    ) -> tuple[list[AdminRole], int]:
        stmt = select(AdminRole)
        count_stmt = select(func.count()).select_from(AdminRole)
        if keyword:
            condition = or_(AdminRole.name.ilike(f"%{keyword}%"), AdminRole.code.ilike(f"%{keyword}%"))
            stmt = stmt.where(condition)
            count_stmt = count_stmt.where(condition)
        total = await self._db.scalar(count_stmt) or 0
        stmt = stmt.order_by(AdminRole.id).offset((page - 1) * page_size).limit(page_size)
        roles = list((await self._db.execute(stmt)).scalars().all())
        return roles, total

    async def create(self, data: AdminRoleCreate) -> AdminRole:
        if await self._code_exists(data.code):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色编码已存在")
        role = AdminRole(**data.model_dump())
        self._db.add(role)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色编码已存在") from exc
        await self._db.refresh(role)
        return role

    async def update(self, role_id: int, data: AdminRoleUpdate) -> AdminRole:
        role = await self._get(role_id)
        if data.code and data.code != role.code and await self._code_exists(data.code):
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色编码已存在")
        for key, value in data.model_dump(exclude_unset=True).items():
            setattr(role, key, value)
        try:
            await self._db.flush()
        except IntegrityError as exc:
            await self._db.rollback()
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色编码已存在") from exc
        await self._db.refresh(role)
        return role

    async def delete(self, role_id: int) -> None:
        role = await self._get(role_id, with_relationships=True)
        if role.users:
            raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="角色已分配给管理员，无法删除")
        await self._db.delete(role)
        await self._db.flush()

    async def role_menus(self, role_id: int):
        role = await self._get(role_id, with_relationships=True)
        menus = await AdminMenuService(self._db).list_tree()
        checked = [menu.id for menu in role.menus]
        return menus, checked

    async def save_role_menus(self, role_id: int, menu_ids: list[int]) -> None:
        role = await self._get(role_id, with_relationships=True)
        if menu_ids:
            stmt = select(AdminMenu).where(AdminMenu.id.in_(menu_ids))
            menus = list((await self._db.execute(stmt)).scalars().all())
            if len(menus) != len(set(menu_ids)):
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="权限节点不存在")
            role.menus = menus
        else:
            role.menus = []
        await self._db.flush()

    async def _get(self, role_id: int, with_relationships: bool = False) -> AdminRole:
        stmt = select(AdminRole).where(AdminRole.id == role_id)
        if with_relationships:
            stmt = stmt.options(selectinload(AdminRole.users), selectinload(AdminRole.menus))
        role = (await self._db.execute(stmt)).scalar_one_or_none()
        if role is None:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="角色不存在")
        return role

    async def _code_exists(self, code: str) -> bool:
        existing_id = await self._db.scalar(select(AdminRole.id).where(AdminRole.code == code))
        return existing_id is not None
