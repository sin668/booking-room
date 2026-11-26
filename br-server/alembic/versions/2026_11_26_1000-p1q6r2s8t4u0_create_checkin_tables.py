"""create checkin tables

Revision ID: p1q6r2s8t4u0
Revises: n9p5q1r7s3t9
Create Date: 2026-11-26 10:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "p1q6r2s8t4u0"
down_revision: Union[str, None] = "n9p5q1r7s3t9"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "checkin_records",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("checkin_date", sa.Date(), nullable=False),
        sa.Column("source", sa.String(length=10), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "source IN ('daily', 'makeup')",
            name="ck_checkin_records_source",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", "checkin_date", name="uq_checkin_records_user_date"),
    )
    op.create_index(
        "ix_checkin_records_user_date",
        "checkin_records",
        ["user_id", "checkin_date"],
        unique=False,
    )

    op.create_table(
        "user_checkin_stats",
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("points", sa.Integer(), nullable=False),
        sa.Column("makeup_cards", sa.Integer(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("points >= 0", name="ck_user_checkin_stats_points"),
        sa.CheckConstraint(
            "makeup_cards >= 0",
            name="ck_user_checkin_stats_makeup_cards",
        ),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("user_id"),
    )


def downgrade() -> None:
    op.drop_table("user_checkin_stats")
    op.drop_index("ix_checkin_records_user_date", table_name="checkin_records")
    op.drop_table("checkin_records")
