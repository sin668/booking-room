from datetime import datetime, date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base


class CourseSchedule(Base):
    """课程排课表。

    存储课程的排课信息，包括授课老师、开课日期、上课时间段和价格。
    从 courses 表迁移出的字段：teacher_id, schedule, price, custom_price,
    full_package_price, full_custom_price。
    """

    __tablename__ = "course_schedules"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    course_id: Mapped[int] = mapped_column(
        Integer, ForeignKey("courses.id", ondelete="CASCADE"), nullable=False
    )
    teacher_id: Mapped[int | None] = mapped_column(
        Integer, ForeignKey("teachers.id"), nullable=True
    )
    start_date: Mapped[date | None] = mapped_column(Date, nullable=True)
    end_date: Mapped[date | None] = mapped_column(Date, nullable=True, comment="课程结束日期")
    time_slots: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="上课时间段，JSON 数组格式，如 [{\"weekday\":1,\"start\":\"09:00\",\"end\":\"11:00\"}]",
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    custom_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    full_package_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    full_custom_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    schedule_type: Mapped[str] = mapped_column(
        String(20), default="fixed", nullable=False,
        comment="排课类型: fixed=固定班课, custom=定制课时",
    )
    schedule_status: Mapped[str] = mapped_column(
        String(20), default="in_progress", nullable=False,
        comment="课程状态: in_progress=进行中, completed=已完成",
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    lesson_schedules = relationship(
        "LessonSchedule", back_populates="schedule", cascade="all, delete-orphan"
    )
