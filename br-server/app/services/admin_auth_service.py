import uuid
from datetime import UTC, datetime, timedelta

import bcrypt
from fastapi import HTTPException, status
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import Settings, settings
from app.models.admin_menu import AdminMenu
from app.models.admin_role import AdminRole
from app.models.admin_user import AdminUser
from app.schemas.admin_auth import AdminPermissionItem, AdminRoleSummary


class AdminAuthService:
    def __init__(self, db: AsyncSession, config: Settings = settings) -> None:
        self._db = db
        self._config = config

    @staticmethod
    def hash_password(password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    @staticmethod
    def verify_password(password: str, password_hash: str) -> bool:
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))

    @staticmethod
    def create_access_token(
        admin_id: uuid.UUID,
        config: Settings = settings,
    ) -> str:
        now = datetime.now(UTC)
        payload = {
            "sub": str(admin_id),
            "type": "admin_access",
            "scope": "admin",
            "exp": now + timedelta(minutes=config.ACCESS_TOKEN_EXPIRE_MINUTES),
        }
        return jwt.encode(payload, config.JWT_SECRET_KEY, algorithm=config.JWT_ALGORITHM)

    @staticmethod
    def verify_access_token(token: str, config: Settings = settings) -> uuid.UUID:
        try:
            payload = jwt.decode(token, config.JWT_SECRET_KEY, algorithms=[config.JWT_ALGORITHM])
        except JWTError as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="无效或过期的管理员令牌",
            ) from exc

        if payload.get("type") != "admin_access" or payload.get("scope") != "admin":
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="管理员令牌类型无效",
            )
        try:
            return uuid.UUID(payload["sub"])
        except (KeyError, ValueError) as exc:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="管理员令牌无效",
            ) from exc

    async def get_admin_by_id(self, admin_id: uuid.UUID) -> AdminUser:
        stmt = (
            select(AdminUser)
            .options(selectinload(AdminUser.roles).selectinload(AdminRole.menus))
            .where(AdminUser.id == admin_id)
        )
        admin = (await self._db.execute(stmt)).scalar_one_or_none()
        if admin is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="管理员不存在")
        if admin.status == "disabled":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员已禁用")
        return admin

    async def login(self, username: str, password: str) -> tuple[AdminUser, str]:
        stmt = (
            select(AdminUser)
            .options(selectinload(AdminUser.roles).selectinload(AdminRole.menus))
            .where(AdminUser.username == username)
        )
        admin = (await self._db.execute(stmt)).scalar_one_or_none()
        if admin is None or not self.verify_password(password, admin.password_hash):
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="用户名或密码错误")
        if admin.status == "disabled":
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="管理员已禁用")
        return admin, self.create_access_token(admin.id, self._config)

    async def permissions_for(self, admin: AdminUser) -> list[AdminPermissionItem]:
        if admin.is_super_admin:
            stmt = (
                select(AdminMenu)
                .where(AdminMenu.enabled.is_(True), AdminMenu.permission_code.is_not(None))
                .order_by(AdminMenu.sort, AdminMenu.id)
            )
            menus = list((await self._db.execute(stmt)).scalars().all())
        else:
            menus = []
            seen_ids: set[int] = set()
            for role in admin.roles:
                if role.status != "active":
                    continue
                for menu in role.menus:
                    if menu.enabled and menu.permission_code and menu.id not in seen_ids:
                        menus.append(menu)
                        seen_ids.add(menu.id)

        return [
            AdminPermissionItem(label=menu.title, value=menu.permission_code)
            for menu in sorted(menus, key=lambda item: (item.sort, item.id))
            if menu.permission_code
        ]

    @staticmethod
    def roles_for(admin: AdminUser) -> list[AdminRoleSummary]:
        return [
            AdminRoleSummary(id=role.id, name=role.name, code=role.code)
            for role in admin.roles
            if role.status == "active"
        ]

    async def permission_codes_for(self, admin: AdminUser) -> set[str]:
        return {item.value for item in await self.permissions_for(admin)}

    async def update_profile(self, admin: AdminUser, values: dict) -> AdminUser:
        for key, value in values.items():
            setattr(admin, key, value)
        await self._db.flush()
        await self._db.refresh(admin)
        return admin

    async def update_password(self, admin: AdminUser, old_password: str, new_password: str) -> None:
        if not self.verify_password(old_password, admin.password_hash):
            raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="旧密码错误")
        admin.password_hash = self.hash_password(new_password)
        await self._db.flush()
