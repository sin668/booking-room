from datetime import datetime

from sqlalchemy import Boolean, CheckConstraint, DateTime, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class SystemSetting(Base):
    __tablename__ = "system_settings"
    __table_args__ = (
        CheckConstraint('"group" IN (\'basic\', \'email\')', name="ck_system_settings_group"),
    )

    key: Mapped[str] = mapped_column(String(80), primary_key=True)
    value: Mapped[str | None] = mapped_column(Text, nullable=True)
    group: Mapped[str] = mapped_column(String(20), nullable=False, index=True)
    is_secret: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
