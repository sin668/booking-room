from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Index, Integer, UniqueConstraint, func
from sqlalchemy.orm import Mapped, mapped_column

from app.core.database import Base


class TeacherRoom(Base):
    """老师与培训室/综合室的多对多关联表。

    room_id 仅允许关联 study_rooms 中 room_type 为 training 或 comprehensive 的房间，
    由服务层校验。
    """

    __tablename__ = "teacher_rooms"
    __table_args__ = (
        UniqueConstraint("teacher_id", "room_id", name="uq_teacher_rooms_teacher_room"),
        Index("ix_teacher_rooms_teacher_id", "teacher_id"),
        Index("ix_teacher_rooms_room_id", "room_id"),
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    teacher_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("teachers.id", ondelete="CASCADE"), nullable=False
    )
    room_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("study_rooms.id", ondelete="CASCADE"), nullable=False
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
