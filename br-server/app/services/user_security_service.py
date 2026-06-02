"""Current-user account security business rules."""

from __future__ import annotations

import hashlib
import re
import uuid
from dataclasses import dataclass
from datetime import datetime
from decimal import Decimal

import bcrypt
import redis.asyncio as aioredis
from fastapi import HTTPException, status
from sqlalchemy import and_, exists, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import Settings
from app.models.booking import Booking
from app.models.coupon import Coupon, UserCoupon
from app.models.user import User
from app.models.user_identity_verification import UserIdentityVerification
from app.models.wallet import WalletTransaction
from app.schemas.user import (
    AccountDeactivationResponse,
    AccountSecuritySummary,
    ChangePasswordRequest,
    ChangePasswordResponse,
    DeactivationRiskReason,
    IdentityVerificationRequest,
    IdentityVerificationResponse,
)
from app.services.jwt_service import JWTService


ID_CARD_PATTERN = re.compile(r"^\d{17}[\dXx]$")
REAL_NAME_PATTERN = re.compile(r"^[\u4e00-\u9fa5A-Za-z·\s]{2,50}$")


@dataclass(frozen=True)
class IdentitySnapshot:
    status: str = "unverified"
    id_card_masked: str | None = None


class UserSecurityService:
    def __init__(self, db: AsyncSession, redis: aioredis.Redis, config: Settings) -> None:
        self._db = db
        self._jwt = JWTService(config, redis)

    async def get_security_summary(self, user_id: uuid.UUID) -> AccountSecuritySummary:
        user = await self._get_user(user_id)
        identity = await self._get_verified_identity_snapshot(user_id)
        risks = await self._get_deactivation_risks(user)
        return AccountSecuritySummary(
            phone_bound=bool(user.phone),
            phone_masked=mask_phone(user.phone),
            wechat_bound=bool(user.wechat_openid),
            identity_status=identity.status,
            identity_masked=identity.id_card_masked,
            account_status=user.status,
            deactivation_blocked=bool(risks),
            deactivation_risks=risks,
        )

    async def change_password(
        self,
        user_id: uuid.UUID,
        data: ChangePasswordRequest,
    ) -> ChangePasswordResponse:
        user = await self._get_active_user(user_id)
        if data.new_password != data.confirm_password:
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="两次输入的新密码不一致",
            )
        if not bcrypt.checkpw(
            data.old_password.encode("utf-8"),
            user.password_hash.encode("utf-8"),
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="旧密码不正确",
            )

        user.password_hash = bcrypt.hashpw(
            data.new_password.encode("utf-8"),
            bcrypt.gensalt(),
        ).decode("utf-8")
        await self._jwt.revoke_all_refresh_tokens(user.id)
        await self._db.flush()
        return ChangePasswordResponse(message="密码已更新")

    async def submit_identity(
        self,
        user_id: uuid.UUID,
        data: IdentityVerificationRequest,
    ) -> IdentityVerificationResponse:
        await self._get_active_user(user_id)
        real_name = data.real_name.strip()
        id_card_number = data.id_card_number.strip().upper()
        if not REAL_NAME_PATTERN.match(real_name):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="真实姓名格式不正确",
            )
        if not is_valid_id_card(id_card_number):
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail="身份证号格式不正确",
            )

        id_hash = hash_id_card(id_card_number)
        existing = await self._get_latest_verified_identity(user_id)
        if existing is not None:
            if existing.real_name == real_name and existing.id_card_hash == id_hash:
                return IdentityVerificationResponse(
                    status=existing.status,
                    real_name=existing.real_name,
                    id_card_masked=existing.id_card_masked,
                )
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="已完成实名认证，不能覆盖为不同实名资料",
            )

        now = datetime.now()
        verification = UserIdentityVerification(
            user_id=user_id,
            real_name=real_name,
            id_card_hash=id_hash,
            id_card_masked=mask_id_card(id_card_number),
            status="verified",
            submitted_at=now,
            reviewed_at=now,
        )
        self._db.add(verification)
        await self._db.flush()
        return IdentityVerificationResponse(
            status="verified",
            real_name=real_name,
            id_card_masked=verification.id_card_masked,
        )

    async def deactivate_account(self, user_id: uuid.UUID) -> AccountDeactivationResponse:
        user = await self._get_active_user(user_id)
        risks = await self._get_deactivation_risks(user)
        if risks:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={
                    "message": "账号存在未处理事项，暂不能注销",
                    "risks": [risk.model_dump() for risk in risks],
                },
            )

        user.status = "deleted"
        await self._jwt.revoke_all_refresh_tokens(user.id)
        await self._db.flush()
        return AccountDeactivationResponse(
            status="deleted",
            message="账号已注销",
        )

    async def _get_user(self, user_id: uuid.UUID) -> User:
        result = await self._db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="用户不存在",
            )
        return user

    async def _get_active_user(self, user_id: uuid.UUID) -> User:
        user = await self._get_user(user_id)
        if user.status == "deleted":
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="账号已注销",
            )
        return user

    async def _get_verified_identity_snapshot(self, user_id: uuid.UUID) -> IdentitySnapshot:
        verification = await self._get_latest_verified_identity(user_id)
        if verification is None:
            return IdentitySnapshot()
        return IdentitySnapshot(
            status=verification.status,
            id_card_masked=verification.id_card_masked,
        )

    async def _get_latest_verified_identity(
        self,
        user_id: uuid.UUID,
    ) -> UserIdentityVerification | None:
        result = await self._db.execute(
            select(UserIdentityVerification)
            .where(
                UserIdentityVerification.user_id == user_id,
                UserIdentityVerification.status == "verified",
            )
            .order_by(UserIdentityVerification.created_at.desc())
            .limit(1)
        )
        return result.scalar_one_or_none()

    async def _get_deactivation_risks(self, user: User) -> list[DeactivationRiskReason]:
        risks: list[DeactivationRiskReason] = []
        user_id = str(user.id)
        balance = Decimal(str(user.balance or 0))
        if balance > Decimal("0"):
            risks.append(
                DeactivationRiskReason(
                    code="wallet_balance",
                    message="钱包余额需清零后才能注销",
                    amount=f"{balance:.2f}",
                )
            )

        if await self._exists(
            Booking,
            Booking.user_id == user_id,
            Booking.status.in_(["pending", "confirmed"]),
        ):
            risks.append(
                DeactivationRiskReason(
                    code="unfinished_booking",
                    message="存在未完成预约",
                )
            )

        if await self._exists(
            Booking,
            Booking.user_id == user_id,
            Booking.payment_status == "pending",
        ):
            risks.append(
                DeactivationRiskReason(
                    code="pending_booking_payment",
                    message="存在待处理预约支付",
                )
            )

        if await self._exists(
            WalletTransaction,
            WalletTransaction.user_id == user_id,
            WalletTransaction.status == "pending",
        ) or await self._exists(
            WalletTransaction,
            WalletTransaction.user_id == user_id,
            WalletTransaction.payment_status == "pending",
        ):
            risks.append(
                DeactivationRiskReason(
                    code="pending_wallet_transaction",
                    message="存在待处理支付或退款",
                )
            )

        now = datetime.now()
        stmt = select(
            exists().where(
                and_(
                    UserCoupon.user_id == user_id,
                    UserCoupon.status == "available",
                    UserCoupon.coupon_id == Coupon.id,
                    Coupon.is_active.is_(True),
                    Coupon.valid_from <= now,
                    Coupon.expires_at >= now,
                )
            )
        )
        result = await self._db.execute(stmt)
        if result.scalar():
            risks.append(
                DeactivationRiskReason(
                    code="available_coupon",
                    message="存在未使用卡券",
                )
            )

        return risks

    async def _exists(self, model, *conditions) -> bool:
        result = await self._db.execute(select(exists().where(*conditions)))
        return bool(result.scalar())


def mask_phone(phone: str | None) -> str | None:
    if not phone:
        return None
    if len(phone) < 7:
        return phone
    return f"{phone[:3]}****{phone[-4:]}"


def mask_id_card(id_card_number: str) -> str:
    value = id_card_number.strip().upper()
    if len(value) != 18:
        return value
    return f"{value[:6]}********{value[-4:]}"


def hash_id_card(id_card_number: str) -> str:
    return hashlib.sha256(id_card_number.strip().upper().encode("utf-8")).hexdigest()


def is_valid_id_card(id_card_number: str) -> bool:
    value = id_card_number.strip().upper()
    if not ID_CARD_PATTERN.match(value):
        return False
    factors = [7, 9, 10, 5, 8, 4, 2, 1, 6, 3, 7, 9, 10, 5, 8, 4, 2]
    checks = "10X98765432"
    total = sum(int(value[index]) * factors[index] for index in range(17))
    return checks[total % 11] == value[-1]
