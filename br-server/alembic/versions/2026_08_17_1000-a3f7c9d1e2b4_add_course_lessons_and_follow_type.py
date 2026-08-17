"""add course_lessons and follow_type

Revision ID: a3f7c9d1e2b4
Revises: fccf087f0f34
Create Date: 2026-08-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a3f7c9d1e2b4"
down_revision: Union[str, None] = "fccf087f0f34"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. courses 表新增 description 列
    op.add_column("courses", sa.Column("description", sa.String(1000), nullable=True))

    # 2. 新建 course_lessons 表
    op.create_table(
        "course_lessons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("course_id", sa.Integer(), nullable=False),
        sa.Column("title", sa.String(200), nullable=False),
        sa.Column("description", sa.String(500), nullable=True),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("sort_order", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_free_preview", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.PrimaryKeyConstraint("id"),
        sa.ForeignKeyConstraint(["course_id"], ["courses.id"], ondelete="CASCADE"),
    )
    op.create_index("ix_course_lessons_course_id", "course_lessons", ["course_id"])

    # 3. room_follows 表新增 follow_type 列
    op.add_column(
        "room_follows",
        sa.Column("follow_type", sa.String(20), nullable=False, server_default="room"),
    )

    # 4. 删除旧唯一约束，创建新唯一约束
    op.drop_constraint("uq_room_follows_user_room", "room_follows", type_="unique")
    op.create_unique_constraint(
        "uq_room_follows_user_room_type",
        "room_follows",
        ["user_id", "room_id", "follow_type"],
    )

    # 5. 删除 room_follows.room_id 外键约束
    op.drop_constraint("room_follows_room_id_fkey", "room_follows", type_="foreignkey")


def downgrade() -> None:
    # 逆序恢复
    op.create_foreign_key(
        "room_follows_room_id_fkey", "room_follows", "study_rooms",
        ["room_id"], ["id"], ondelete="CASCADE",
    )
    op.drop_constraint("uq_room_follows_user_room_type", "room_follows", type_="unique")
    op.create_unique_constraint(
        "uq_room_follows_user_room", "room_follows", ["user_id", "room_id"]
    )
    op.drop_column("room_follows", "follow_type")
    op.drop_index("ix_course_lessons_course_id", table_name="course_lessons")
    op.drop_table("course_lessons")
    op.drop_column("courses", "description")
