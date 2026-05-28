"""add_notification_tables

Revision ID: a7b8c9d0e1f2
Revises: f6a1b2c3d4e5
Create Date: 2026-05-28 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a7b8c9d0e1f2"
down_revision: Union[str, None] = "f6a1b2c3d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=100), nullable=False),
        sa.Column("content", sa.String(length=1000), nullable=False),
        sa.Column("target_url", sa.String(length=512), nullable=True),
        sa.Column("target_type", sa.String(length=50), nullable=True),
        sa.Column("target_id", sa.String(length=64), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("created_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.Column("read_at", sa.DateTime(), nullable=True),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index(
        "ix_notifications_user_id_type",
        "notifications",
        ["user_id", "type"],
    )
    op.create_index(
        "ix_notifications_user_id_is_read",
        "notifications",
        ["user_id", "is_read"],
    )
    op.create_index(
        "ix_notifications_user_id_created_at",
        "notifications",
        ["user_id", "created_at"],
    )

    op.create_table(
        "notification_preferences",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("user_id", sa.Uuid(), nullable=False),
        sa.Column("booking_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("activity_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("report_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("arrival_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("updated_at", sa.DateTime(), nullable=False, server_default=sa.func.now()),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_notification_preferences_user_id",
        "notification_preferences",
        ["user_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_notification_preferences_user_id",
        table_name="notification_preferences",
    )
    op.drop_table("notification_preferences")

    op.drop_index("ix_notifications_user_id_created_at", table_name="notifications")
    op.drop_index("ix_notifications_user_id_is_read", table_name="notifications")
    op.drop_index("ix_notifications_user_id_type", table_name="notifications")
    op.drop_index("ix_notifications_user_id", table_name="notifications")
    op.drop_table("notifications")
