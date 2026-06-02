"""add room follows

Revision ID: c9d0e1f2a3b4
Revises: b8c9d0e1f2a3
Create Date: 2026-06-02 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "c9d0e1f2a3b4"
down_revision: Union[str, None] = "b8c9d0e1f2a3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "room_follows",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("room_id", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["room_id"], ["study_rooms.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "room_id", name="uq_room_follows_user_room"),
    )
    op.create_index(op.f("ix_room_follows_room_id"), "room_follows", ["room_id"], unique=False)
    op.create_index(op.f("ix_room_follows_user_id"), "room_follows", ["user_id"], unique=False)
    op.create_index(
        "ix_room_follows_user_id_created_at",
        "room_follows",
        ["user_id", "created_at"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index("ix_room_follows_user_id_created_at", table_name="room_follows")
    op.drop_index(op.f("ix_room_follows_user_id"), table_name="room_follows")
    op.drop_index(op.f("ix_room_follows_room_id"), table_name="room_follows")
    op.drop_table("room_follows")
