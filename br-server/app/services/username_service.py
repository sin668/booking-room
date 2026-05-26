"""Username validation and generation helpers."""

from __future__ import annotations

import random
import re

from fastapi import HTTPException, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.user import User


EDITABLE_USERNAME_PATTERN = re.compile(r"^[A-Za-z0-9_]{6,32}$")
GENERATED_USERNAME_PATTERN = re.compile(r"^[A-Za-z]+[0-9]{5}$")
DEFAULT_MAX_ATTEMPTS = 20

ENGLISH_NAMES: tuple[str, ...] = (
    "Luna",
    "Mia",
    "Noah",
    "Ava",
    "Leo",
    "Ivy",
    "Eli",
    "Zoe",
    "Nina",
    "Owen",
    "Ruby",
    "Milo",
    "Emma",
    "Liam",
    "Aria",
    "Jack",
)


class UsernameService:
    def __init__(self, db: AsyncSession, max_attempts: int = DEFAULT_MAX_ATTEMPTS) -> None:
        self._db = db
        self._max_attempts = max_attempts

    @staticmethod
    def is_valid_editable_username(username: str) -> bool:
        return bool(EDITABLE_USERNAME_PATTERN.fullmatch(username))

    @staticmethod
    def validate_editable_username(username: str) -> None:
        if not UsernameService.is_valid_editable_username(username):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="用户名仅支持 6-32 位字母、数字或下划线",
            )

    @staticmethod
    def generate_candidate() -> str:
        return f"{random.choice(ENGLISH_NAMES)}{random.randint(10000, 99999)}"

    async def username_exists(self, username: str, exclude_user_id=None) -> bool:
        stmt = select(User.id).where(User.username == username)
        if exclude_user_id is not None:
            stmt = stmt.where(User.id != exclude_user_id)
        result = await self._db.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def generate_unique_username(self) -> str:
        for _ in range(self._max_attempts):
            candidate = self.generate_candidate()
            if not await self.username_exists(candidate):
                return candidate

        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="用户名生成失败，请稍后重试",
        )
