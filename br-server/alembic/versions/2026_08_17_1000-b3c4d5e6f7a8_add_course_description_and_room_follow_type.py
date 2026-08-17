"""add_course_description_and_room_follow_type

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-08-17 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b3c4d5e6f7a8"
down_revision: Union[str, None] = "a2b3c4d5e6f7"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name

    # 1. Add description column to courses
    op.add_column(
        "courses",
        sa.Column("description", sa.String(1000), nullable=True),
    )

    # 2. Modify room_follows: add follow_type, drop old FK + unique, add new unique
    if dialect_name == "sqlite":
        with op.batch_alter_table("room_follows", recreate="always") as batch_op:
            batch_op.add_column(
                sa.Column("follow_type", sa.String(20), nullable=False, server_default="room")
            )
            batch_op.drop_constraint("uq_room_follows_user_room", type_="unique")
            batch_op.drop_constraint("room_follows_room_id_fkey", type_="foreignkey")
            batch_op.create_unique_constraint(
                "uq_room_follows_user_room_type",
                ["user_id", "room_id", "follow_type"],
            )
    else:
        op.add_column(
            "room_follows",
            sa.Column("follow_type", sa.String(20), nullable=False, server_default="room"),
        )
        op.drop_constraint("uq_room_follows_user_room", "room_follows", type_="unique")
        op.drop_constraint("room_follows_room_id_fkey", "room_follows", type_="foreignkey")
        op.create_unique_constraint(
            "uq_room_follows_user_room_type",
            ["user_id", "room_id", "follow_type"],
            table_name="room_follows",
        )


def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name

    if dialect_name == "sqlite":
        with op.batch_alter_table("room_follows", recreate="always") as batch_op:
            batch_op.drop_constraint("uq_room_follows_user_room_type", type_="unique")
            batch_op.create_foreign_key(
                "room_follows_room_id_fkey",
                "room_follows",
                "study_rooms",
                ["room_id"],
                ["id"],
                ondelete="CASCADE",
            )
            batch_op.create_unique_constraint(
                "uq_room_follows_user_room",
                ["user_id", "room_id"],
            )
            batch_op.drop_column("follow_type")
    else:
        op.drop_constraint("uq_room_follows_user_room_type", "room_follows", type_="unique")
        op.create_foreign_key(
            "room_follows_room_id_fkey",
            "room_follows",
            "study_rooms",
            ["room_id"],
            ["id"],
            ondelete="CASCADE",
        )
        op.create_unique_constraint(
            "uq_room_follows_user_room",
            ["user_id", "room_id"],
            table_name="room_follows",
        )
        op.drop_column("room_follows", "follow_type")

    op.drop_column("courses", "description")
