"""add room_type, teachers, courses

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-14 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("study_rooms",
        sa.Column("room_type", sa.String(20), server_default="study", nullable=False))

    op.create_table("teachers",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("name", sa.String(50), nullable=False),
        sa.Column("avatar", sa.String(512), nullable=True),
        sa.Column("title", sa.String(50), nullable=True),
        sa.Column("rating", sa.Numeric(3, 1), server_default="0.0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_table("courses",
        sa.Column("id", sa.Integer, primary_key=True, autoincrement=True),
        sa.Column("room_id", sa.Integer, sa.ForeignKey("study_rooms.id"), nullable=False),
        sa.Column("teacher_id", sa.Integer, sa.ForeignKey("teachers.id"), nullable=True),
        sa.Column("name", sa.String(100), nullable=False),
        sa.Column("cover_image", sa.String(512), nullable=True),
        sa.Column("category", sa.String(30), nullable=False),
        sa.Column("price", sa.Numeric(10, 2), nullable=False),
        sa.Column("rating", sa.Numeric(3, 1), server_default="0.0", nullable=False),
        sa.Column("enrollment_count", sa.Integer, server_default="0", nullable=False),
        sa.Column("schedule", sa.String(200), nullable=True),
        sa.Column("tags", sa.String(200), nullable=True),
        sa.Column("status", sa.String(20), server_default="active", nullable=False),
        sa.Column("is_hot", sa.Boolean, server_default="false", nullable=False),
        sa.Column("sort_order", sa.Integer, server_default="0", nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), nullable=False),
    )

    op.create_index("ix_courses_room_id", "courses", ["room_id"])
    op.create_index("ix_courses_teacher_id", "courses", ["teacher_id"])
    op.create_index("ix_courses_category", "courses", ["category"])


def downgrade() -> None:
    op.drop_index("ix_courses_category", table_name="courses")
    op.drop_index("ix_courses_teacher_id", table_name="courses")
    op.drop_index("ix_courses_room_id", table_name="courses")
    op.drop_table("courses")
    op.drop_table("teachers")
    op.drop_column("study_rooms", "room_type")
