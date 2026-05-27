"""add_booking_payment_fields

Adds payment-related fields to bookings table:
- payment_method: VARCHAR(20), NOT NULL, DEFAULT 'balance'
- payment_status: VARCHAR(20), NOT NULL, DEFAULT 'paid'
- payment_provider: VARCHAR(20), nullable
- prepay_id: VARCHAR(64), nullable
- transaction_id: VARCHAR(64), nullable
- paid_at: TIMESTAMP, nullable

Backfills existing booking records with payment_method='balance' and payment_status='paid'.

Revision ID: a1b2c3d4e5f6
Revises: d4e5f6a1b2c3
Create Date: 2026-05-27 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "e5f6a1b2c3d4"
down_revision: Union[str, None] = "d4e5f6a1b2c3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Add new columns with appropriate defaults
    op.add_column(
        "bookings",
        sa.Column("payment_method", sa.String(length=20), nullable=False, server_default="balance")
    )
    op.add_column(
        "bookings",
        sa.Column("payment_status", sa.String(length=20), nullable=False, server_default="paid")
    )
    op.add_column(
        "bookings",
        sa.Column("payment_provider", sa.String(length=20), nullable=True)
    )
    op.add_column(
        "bookings",
        sa.Column("prepay_id", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "bookings",
        sa.Column("transaction_id", sa.String(length=64), nullable=True)
    )
    op.add_column(
        "bookings",
        sa.Column("paid_at", sa.DateTime(), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("bookings", "paid_at")
    op.drop_column("bookings", "transaction_id")
    op.drop_column("bookings", "prepay_id")
    op.drop_column("bookings", "payment_provider")
    op.drop_column("bookings", "payment_status")
    op.drop_column("bookings", "payment_method")