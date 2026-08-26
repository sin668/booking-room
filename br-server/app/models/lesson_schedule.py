"""课时安排中间表模型。"""

from sqlalchemy import Date, ForeignKey, Integer, String
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class LessonSchedule(Base):
    """课时安排表。

    存储每个课时的实际上课日期和时间段，是 course_schedules 和 course_lessons 的中间表。
    """

    __tablename__ = "lesson_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    schedule_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course_schedules.id", ondelete="CASCADE"),
        nullable=False,
        comment="排课记录ID",
    )
    lesson_id: Mapped[int] = mapped_column(
        Integer,
        ForeignKey("course_lessons.id", ondelete="CASCADE"),
        nullable=False,
        comment="课时ID",
    )
    lesson_date: Mapped[str] = mapped_column(Date, nullable=False, comment="上课日期")
    lesson_time_slot: Mapped[str] = mapped_column(
        String(50), nullable=False, comment="上课时间段，如 08:00-10:00"
    )
    sort_order: Mapped[int] = mapped_column(Integer, nullable=False, default=0, comment="排序序号")

    # Relationships
    schedule = relationship("CourseSchedule", back_populates="lesson_schedules")
