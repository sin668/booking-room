import uuid
from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, JSON, Numeric, String, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class WalletTransaction(Base):
    __tablename__ = "wallet_transactions"
    __table_args__ = (
        Index("ix_wallet_transactions_user_id_type", "user_id", "type"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[str] = mapped_column(
        String(36),
        nullable=False,
        index=True,
    )
    type: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="recharge",
    )
    amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        nullable=False,
    )
    bonus_amount: Mapped[float] = mapped_column(
        Numeric(10, 2),
        default=0,
        nullable=False,
    )
    balance_after: Mapped[float | None] = mapped_column(
        Numeric(10, 2),
        nullable=True,
    )
    order_id: Mapped[str] = mapped_column(
        String(36),
        unique=True,
        index=True,
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )
    promo_code_id: Mapped[int | None] = mapped_column(
        Integer,
        ForeignKey("coupons.id"),
        nullable=True,
    )
    payment_method: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )
    payment_provider: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="wechat",
    )
    payment_status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
        index=True,
    )
    prepay_id: Mapped[str | None] = mapped_column(
        String(128),
        nullable=True,
        index=True,
    )
    transaction_id: Mapped[str | None] = mapped_column(
        String(64),
        nullable=True,
        unique=True,
        index=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    notify_payload: Mapped[dict | None] = mapped_column(
        JSON,
        nullable=True,
    )
    notify_processed_at: Mapped[datetime | None] = mapped_column(
        DateTime,
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=func.now(),
        nullable=False,
    )
