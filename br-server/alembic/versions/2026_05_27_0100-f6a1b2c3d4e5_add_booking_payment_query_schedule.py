"""add_booking_payment_query_schedule

Revision ID: f6a1b2c3d4e5
Revises: e5f6a1b2c3d4
Create Date: 2026-05-27 01:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f6a1b2c3d4e5"
down_revision: Union[str, None] = "e5f6a1b2c3d4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "bookings",
        sa.Column(
            "payment_check_count",
            sa.Integer(),
            nullable=False,
            server_default="0",
        ),
    )
    op.add_column(
        "bookings",
        sa.Column("next_payment_check_at", sa.DateTime(), nullable=True),
    )


def downgrade() -> None:
    op.drop_column("bookings", "next_payment_check_at")
    op.drop_column("bookings", "payment_check_count")
