"""Current-user profile business rules."""

from __future__ import annotations

import uuid
from dataclasses import dataclass
from datetime import datetime, timedelta

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User
from app.schemas.user import UserProfileUpdate
from app.services.username_service import UsernameService


USERNAME_COOLDOWN = timedelta(hours=24)
USERNAME_COOLDOWN_DETAIL = "用户名修改后 24 小时内不可再次修改"


@dataclass
class UsernameCooldownError(Exception):
    retry_after_seconds: int
    detail: str = USERNAME_COOLDOWN_DETAIL


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
            await self._update_username(user, update_data["username"])

        if "nickname" in update_data:
            user.nickname = update_data["nickname"]
        if "avatar" in update_data:
            user.avatar = update_data["avatar"]

        await self._db.flush()
        await self._db.refresh(user)
        return user

    async def _update_username(self, user: User, username: str) -> None:
        self._username_service.validate_editable_username(username)
        self._enforce_username_cooldown(user)

        if await self._username_service.username_exists(username, exclude_user_id=user.id):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="该用户名已存在",
            )

        user.username = username
        user.username_updated_at = datetime.now()

    def _enforce_username_cooldown(self, user: User) -> None:
        if user.username_updated_at is None:
            return

        elapsed = datetime.now() - user.username_updated_at
        if elapsed >= USERNAME_COOLDOWN:
            return

        retry_after = max(1, int((USERNAME_COOLDOWN - elapsed).total_seconds()))
        raise UsernameCooldownError(retry_after_seconds=retry_after)
