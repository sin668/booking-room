"""Current-user profile business rules."""

from __future__ import annotations

import re
import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserProfileUpdate
from app.services.username_service import UsernameService

PROFILE_COOLDOWN = timedelta(days=30)


@dataclass
class ProfileCooldownError(Exception):
    retry_after_seconds: int
    detail: str = ""


class UserProfileService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._username_service = UsernameService(db)

    async def get_current_user(self, user_id: uuid.UUID) -> User:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        return user

    async def update_profile(self, user_id: uuid.UUID, data: UserProfileUpdate) -> User:
        user = await self.get_current_user(user_id)
        update_data = data.model_dump(exclude_unset=True)

        if "username" in update_data and update_data["username"] != user.username:
            await self.update_username(user, update_data["username"])

        if "email" in update_data:
            self._update_email(user, update_data["email"])

        if "nickname" in update_data:
            user.nickname = update_data["nickname"]
        if "avatar" in update_data:
            user.avatar = update_data["avatar"]
        if "gender" in update_data:
            user.gender = update_data["gender"]
        if "birthday" in update_data:
            user.birthday = update_data["birthday"]
        if "signature" in update_data:
            user.signature = update_data["signature"]

        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def update_username(self, user: User, username: str) -> None:
        self._username_service.validate_editable_username(username)
        self.enforce_cooldown(user.username_updated_at, "用户名修改后 30 天内不可再次修改")

        if await self._username_service.username_exists(username, exclude_user_id=user.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该用户名已存在",
            )

        user.username = username
        user.username_updated_at = datetime.now()

    async def update_phone(self, user: User, new_phone: str) -> None:
        self.enforce_cooldown(user.phone_updated_at, "手机号修改后 30 天内不可再次修改")

        existing = await self._db.execute(
            select(User).where(User.phone == new_phone, User.id != user.id)
        )
        if existing.scalar_one_or_none():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该手机号已被其他账号使用",
            )

        user.phone = new_phone
        user.phone_updated_at = datetime.now()

    def _update_email(self, user: User, email: str | None) -> None:
        if email is not None and email != user.email:
            if email and not re.match(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", email):
                raise HTTPException(
                    status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                    detail="邮箱格式不正确",
                )
        user.email = email

    async def change_phone(self, user_id: uuid.UUID, new_phone: str) -> User:
        user = await self.get_current_user(user_id)
        await self.update_phone(user, new_phone)
        await self._db.flush()
        await self._db.refresh(user)
        return user

    def enforce_cooldown(self, updated_at: datetime | None, detail: str) -> None:
        if updated_at is None:
            return

        elapsed = datetime.now() - updated_at
        if elapsed >= PROFILE_COOLDOWN:
            return

        retry_after = max(1, int((PROFILE_COOLDOWN - elapsed).total_seconds()))
        raise ProfileCooldownError(retry_after_seconds=retry_after, detail=detail)
