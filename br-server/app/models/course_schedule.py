from datetime import datetime, date

from sqlalchemy import Date, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column

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
    time_slots: Mapped[str | None] = mapped_column(
        Text, nullable=True,
        comment="上课时间段，JSON 数组格式，如 [{\"weekday\":1,\"start\":\"09:00\",\"end\":\"11:00\"}]",
    )
    price: Mapped[float] = mapped_column(Numeric(10, 2), nullable=False)
    custom_price: Mapped[float] = mapped_column(Numeric(10, 2), default=0, nullable=False)
    full_package_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    full_custom_price: Mapped[float | None] = mapped_column(Numeric(10, 2), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=func.now(), onupdate=func.now(), nullable=False
    )
