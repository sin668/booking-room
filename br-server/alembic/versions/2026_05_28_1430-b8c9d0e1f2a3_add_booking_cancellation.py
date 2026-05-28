"""add booking cancellation audit fields

Revision ID: b8c9d0e1f2a3
Revises: a7b8c9d0e1f2
Create Date: 2026-05-28 14:30:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b8c9d0e1f2a3"
down_revision: Union[str, None] = "a7b8c9d0e1f2"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("bookings", sa.Column("cancelled_at", sa.DateTime(), nullable=True))
    op.add_column(
        "bookings",
        sa.Column("penalty_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.add_column(
        "bookings",
        sa.Column("refund_amount", sa.Numeric(10, 2), nullable=False, server_default="0"),
    )
    op.add_column("bookings", sa.Column("cancel_policy", sa.String(length=50), nullable=True))
    op.add_column("wallet_transactions", sa.Column("booking_id", sa.Integer(), nullable=True))
    op.create_index(
        "ix_wallet_transactions_booking_id",
        "wallet_transactions",
        ["booking_id"],
        unique=False,
    )
    op.create_index(
        "uq_wallet_transactions_booking_refund_booking",
        "wallet_transactions",
        ["booking_id"],
        unique=True,
        postgresql_where=sa.text("type = 'booking_refund'"),
        sqlite_where=sa.text("type = 'booking_refund'"),
    )
    op.create_foreign_key(
        "fk_wallet_transactions_booking_id_bookings",
        "wallet_transactions",
        "bookings",
        ["booking_id"],
        ["id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "fk_wallet_transactions_booking_id_bookings",
        "wallet_transactions",
        type_="foreignkey",
    )
    op.drop_index(
        "uq_wallet_transactions_booking_refund_booking",
        table_name="wallet_transactions",
    )
    op.drop_index("ix_wallet_transactions_booking_id", table_name="wallet_transactions")
    op.drop_column("wallet_transactions", "booking_id")
    op.drop_column("bookings", "cancel_policy")
    op.drop_column("bookings", "refund_amount")
    op.drop_column("bookings", "penalty_amount")
    op.drop_column("bookings", "cancelled_at")
