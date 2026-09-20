from __future__ import annotations

import uuid
from datetime import datetime
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, CheckConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base

if TYPE_CHECKING:
    from app.models.user import User


class UserIdentityVerification(Base):
    __tablename__ = "user_identity_verifications"
    __table_args__ = (
        Index("ix_user_identity_verifications_user_id_status", "user_id", "status"),
        Index("ix_user_identity_verifications_id_card_hash", "id_card_hash"),
        CheckConstraint(
            "verification_type IN ('real_name', 'education', 'teacher')",
            name="ck_user_identity_verifications_type",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    verification_type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="real_name",
        comment="认证类型：real_name-实名认证，education-学历认证，teacher-教师资格认证",
    )
    real_name: Mapped[str | None] = mapped_column(String(50), nullable=True)
    id_card_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    id_card_masked: Mapped[str | None] = mapped_column(String(32), nullable=True)
    
    # 学历认证字段
    school: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="学校名称")
    education_level: Mapped[str | None] = mapped_column(String(20), nullable=True, comment="学历：本科/硕士/博士")
    major: Mapped[str | None] = mapped_column(String(100), nullable=True, comment="专业")
    graduation_year: Mapped[int | None] = mapped_column(nullable=True, comment="毕业年份")
    diploma_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="学历证书图片URL")
    
    # 教师资格认证字段
    teacher_certificate_number: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="教师资格证号")
    teaching_subject: Mapped[str | None] = mapped_column(String(50), nullable=True, comment="任教科目")
    certificate_image_url: Mapped[str | None] = mapped_column(String(512), nullable=True, comment="教师资格证书图片URL")
    
    status: Mapped[str] = mapped_column(String(20), default="pending", nullable=False, comment="状态：pending-待审核，approved-已通过，rejected-已拒绝")
    rejection_reason: Mapped[str | None] = mapped_column(Text, nullable=True, comment="拒绝原因")
    submitted_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True, comment="审核时间")
    reviewer_id: Mapped[uuid.UUID | None] = mapped_column(ForeignKey("users.id", ondelete="SET NULL"), nullable=True, comment="审核人ID")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="identity_verifications", foreign_keys=[user_id])
