import uuid
from decimal import Decimal

import bcrypt
from fastapi import HTTPException, status
from sqlalchemy import delete, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.admin_role import AdminRole, admin_user_roles
from app.models.booking import Booking
from app.models.coupon import UserCoupon
from app.models.user import User
from app.schemas.admin_auth import AdminRoleSummary
from app.schemas.admin_user_management import (
    AdminUserCreate,
    AdminUserDetail,
    AdminUserListItem,
    AdminUserListResponse,
    AdminUserUpdate,
)


class AdminUserService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db

    async def list_users(
        self,
        user_type: str | None = None,
        keyword: str | None = None,
        status: str | None = None,
        page: int = 1,
        page_size: int = 20,
    ) -> AdminUserListResponse:
        # Build base query with filters
        stmt = select(User).options(selectinload(User.roles))
        if user_type:
            stmt = stmt.where(User.user_type == user_type)
        if status:
            stmt = stmt.where(User.status == status)
        if keyword:
            stmt = stmt.where(
                or_(
                    User.phone.contains(keyword),
                    User.nickname.contains(keyword),
                    User.username.contains(keyword),
                )
            )

        # Count total
        count_stmt = select(func.count()).select_from(stmt.subquery())
        total = (await self._db.execute(count_stmt)).scalar() or 0

        # Paginate
        stmt = stmt.order_by(User.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
        users = list((await self._db.execute(stmt)).scalars().all())

        # Build items with booking/coupon counts
        items = []
        for user in users:
            booking_count = await self._count_bookings(user.id)
            coupon_count = await self._count_coupons(user.id)
            items.append(AdminUserListItem(
                id=user.id,
                phone=user.phone,
                nickname=user.nickname,
                user_type=user.user_type,
                status=user.status,
                avatar=user.avatar,
                created_at=user.created_at,
                roles=[AdminRoleSummary(id=r.id, name=r.name, code=r.code) for r in user.roles],
                booking_count=booking_count,
                coupon_count=coupon_count,
            ))

        return AdminUserListResponse(items=items, total=total, page=page, page_size=page_size)

    async def get_user(self, user_id: uuid.UUID) -> AdminUserDetail:
        user = await self._get_user_by_id(user_id)
        return self._to_detail(user)

    async def create_user(self, data: AdminUserCreate) -> AdminUserDetail:
        # Validate: app users need phone, admin users need username
        if data.user_type == "app" and not data.phone:
            raise HTTPException(status_code=400, detail="app用户需要手机号")
        if data.user_type == "admin" and not data.username:
            raise HTTPException(status_code=400, detail="admin用户需要用户名")

        # Check uniqueness
        if data.phone:
            existing = await self._db.scalar(
                select(User).where(User.phone == data.phone, User.user_type == 'app')
            )
            if existing:
                raise HTTPException(status_code=409, detail="该手机号已注册")
        if data.username:
            existing = await self._db.scalar(
                select(User).where(User.username == data.username, User.user_type == 'admin')
            )
            if existing:
                raise HTTPException(status_code=409, detail="该用户名已存在")

        password_hash = bcrypt.hashpw(data.password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        user = User(
            user_type=data.user_type,
            phone=data.phone,
            username=data.username,
            nickname=data.nickname or data.username or data.phone or "",
            password_hash=password_hash,
        )
        self._db.add(user)
        await self._db.flush()

        # Auto-assign app_register_user role for app users
        if data.user_type == "app":
            app_role = await self._db.scalar(
                select(AdminRole).where(AdminRole.code == "app_register_user", AdminRole.status == "active")
            )
            if app_role:
                await self._db.execute(
                    admin_user_roles.insert().values(user_id=user.id, admin_role_id=app_role.id)
                )

        await self._db.refresh(user, attribute_names=["roles"])
        return self._to_detail(user)

    async def update_user(self, user_id: uuid.UUID, data: AdminUserUpdate) -> AdminUserDetail:
        user = await self._get_user_by_id(user_id)
        update_data = data.model_dump(exclude_unset=True)
        role_ids = update_data.pop("role_ids", None)

        for key, value in update_data.items():
            setattr(user, key, value)

        if role_ids is not None:
            await self._assign_roles(user_id, role_ids)

        await self._db.flush()
        await self._db.refresh(user)
        return self._to_detail(user)

    async def delete_user(self, user_id: uuid.UUID) -> None:
        user = await self._get_user_by_id(user_id)
        # Delete role associations first
        await self._db.execute(
            delete(admin_user_roles).where(admin_user_roles.c.user_id == user_id)
        )
        await self._db.delete(user)
        await self._db.flush()

    async def reset_password(self, user_id: uuid.UUID, new_password: str) -> AdminUserDetail:
        user = await self._get_user_by_id(user_id)
        user.password_hash = bcrypt.hashpw(new_password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")
        await self._db.flush()
        await self._db.refresh(user)
        return self._to_detail(user)

    async def toggle_status(self, user_id: uuid.UUID, target_status: str) -> AdminUserDetail:
        if target_status not in ("active", "banned", "disabled"):
            raise HTTPException(status_code=400, detail="无效的状态值")
        user = await self._get_user_by_id(user_id)
        user.status = target_status
        await self._db.flush()
        await self._db.refresh(user)
        return self._to_detail(user)

    # -- Helpers --

    async def _get_user_by_id(self, user_id: uuid.UUID) -> User:
        stmt = select(User).options(selectinload(User.roles)).where(User.id == user_id)
        user = (await self._db.execute(stmt)).scalar_one_or_none()
        if user is None:
            raise HTTPException(status_code=404, detail="用户不存在")
        return user

    async def _count_bookings(self, user_id: uuid.UUID) -> int:
        return (await self._db.scalar(
            select(func.count()).select_from(Booking).where(Booking.user_id == str(user_id))
        )) or 0

    async def _count_coupons(self, user_id: uuid.UUID) -> int:
        return (await self._db.scalar(
            select(func.count()).select_from(UserCoupon).where(UserCoupon.user_id == str(user_id))
        )) or 0

    async def _assign_roles(self, user_id: uuid.UUID, role_ids: list[int]) -> None:
        await self._db.execute(
            delete(admin_user_roles).where(admin_user_roles.c.user_id == user_id)
        )
        for role_id in role_ids:
            await self._db.execute(
                admin_user_roles.insert().values(user_id=user_id, admin_role_id=role_id)
            )

    def _to_detail(self, user: User) -> AdminUserDetail:
        return AdminUserDetail(
            id=user.id,
            phone=user.phone,
            nickname=user.nickname,
            user_type=user.user_type,
            username=user.username,
            email=user.email,
            mobile=user.mobile,
            avatar=user.avatar,
            status=user.status,
            balance=int(user.balance) if user.balance else 0,
            is_super_admin=user.is_super_admin,
            wechat_openid=user.wechat_openid,
            invite_code=user.invite_code,
            created_at=user.created_at,
            updated_at=user.updated_at,
            roles=[AdminRoleSummary(id=r.id, name=r.name, code=r.code) for r in user.roles],
            booking_count=0,  # populated separately in list
            coupon_count=0,
        )