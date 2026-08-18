"""create course_schedules table and migrate fields from courses

Revision ID: b1c2d3e4f5a6
Revises: 5d8e53290b12
Create Date: 2026-08-18 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b1c2d3e4f5a6'
down_revision: Union[str, None] = '5d8e53290b12'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 创建 course_schedules 表
    op.create_table(
        "course_schedules",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("course_id", sa.Integer, sa.ForeignKey("courses.id", ondelete="CASCADE"), nullable=False),
        sa.Column("teacher_id", sa.Integer, sa.ForeignKey("teachers.id"), nullable=True),
        sa.Column("start_date", sa.Date, nullable=True),
        sa.Column("time_slots", sa.Text, nullable=True, comment="上课时间段 JSON 数组"),
        sa.Column("price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("custom_price", sa.Numeric(10, 2), nullable=False, server_default="0"),
        sa.Column("full_package_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("full_custom_price", sa.Numeric(10, 2), nullable=True),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_course_schedules_course_id", "course_schedules", ["course_id"])
    op.create_index("ix_course_schedules_teacher_id", "course_schedules", ["teacher_id"])

    # 2. 将 courses 表中的字段迁移到 course_schedules
    # 为每门已有课程创建一条默认排课记录
    op.execute("""
        INSERT INTO course_schedules (course_id, teacher_id, start_date, time_slots, price, custom_price, full_package_price, full_custom_price, created_at, updated_at)
        SELECT id, teacher_id, NULL, schedule, price, custom_price, full_package_price, full_custom_price, NOW(), NOW()
        FROM courses
    """)

    # 3. 删除 courses 表中已迁移的列
    # ix_courses_teacher_id 索引可能在之前的迁移中已被删除，使用 IF EXISTS
    op.execute("DROP INDEX IF EXISTS ix_courses_teacher_id")
    op.drop_column("courses", "teacher_id")
    op.drop_column("courses", "schedule")
    op.drop_column("courses", "price")
    op.drop_column("courses", "custom_price")
    op.drop_column("courses", "full_package_price")
    op.drop_column("courses", "full_custom_price")


def downgrade() -> None:
    # 1. 恢复 courses 表的列
    op.add_column("courses", sa.Column("full_custom_price", sa.Numeric(10, 2), nullable=True))
    op.add_column("courses", sa.Column("full_package_price", sa.Numeric(10, 2), nullable=True))
    op.add_column("courses", sa.Column("custom_price", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("courses", sa.Column("price", sa.Numeric(10, 2), nullable=False, server_default="0"))
    op.add_column("courses", sa.Column("schedule", sa.String(200), nullable=True))
    op.add_column("courses", sa.Column("teacher_id", sa.Integer, sa.ForeignKey("teachers.id"), nullable=True))
    op.create_index("ix_courses_teacher_id", "courses", ["teacher_id"])

    # 2. 从 course_schedules 恢复数据
    op.execute("""
        UPDATE courses SET
            teacher_id = cs.teacher_id,
            schedule = cs.time_slots,
            price = cs.price,
            custom_price = cs.custom_price,
            full_package_price = cs.full_package_price,
            full_custom_price = cs.full_custom_price
        FROM (
            SELECT DISTINCT ON (course_id) *
            FROM course_schedules
            ORDER BY course_id, created_at DESC
        ) cs
        WHERE courses.id = cs.course_id
    """)

    # 3. 删除 course_schedules 表
    op.drop_index("ix_course_schedules_teacher_id", table_name="course_schedules")
    op.drop_index("ix_course_schedules_course_id", table_name="course_schedules")
    op.drop_table("course_schedules")
