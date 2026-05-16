"""add_wechat_payment_fields

Revision ID: a8c3f1b2d4e5
Revises: 7c9d2e4f6a1b
Create Date: 2026-05-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "a8c3f1b2d4e5"
down_revision: Union[str, None] = "7c9d2e4f6a1b"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    with op.batch_alter_table("wallet_transactions") as batch_op:
        batch_op.add_column(
            sa.Column(
                "payment_provider",
                sa.String(length=20),
                server_default="wechat",
                nullable=False,
            )
        )
        batch_op.add_column(
            sa.Column(
                "payment_status",
                sa.String(length=20),
                server_default="pending",
                nullable=False,
            )
        )
        batch_op.add_column(sa.Column("prepay_id", sa.String(length=128), nullable=True))
        batch_op.add_column(
            sa.Column("transaction_id", sa.String(length=64), nullable=True)
        )
        batch_op.add_column(sa.Column("paid_at", sa.DateTime(), nullable=True))
        batch_op.add_column(sa.Column("notify_payload", sa.JSON(), nullable=True))
        batch_op.add_column(
            sa.Column("notify_processed_at", sa.DateTime(), nullable=True)
        )

    op.execute(
        "UPDATE wallet_transactions "
        "SET payment_provider = 'wechat', "
        "payment_status = CASE "
        "WHEN status = 'completed' THEN 'paid' "
        "WHEN status = 'failed' THEN 'failed' "
        "ELSE 'pending' END"
    )

    op.create_index(
        "ix_wallet_transactions_payment_status",
        "wallet_transactions",
        ["payment_status"],
        unique=False,
    )
    op.create_index(
        "ix_wallet_transactions_prepay_id",
        "wallet_transactions",
        ["prepay_id"],
        unique=False,
    )
    op.create_index(
        "ix_wallet_transactions_transaction_id",
        "wallet_transactions",
        ["transaction_id"],
        unique=True,
    )


def downgrade() -> None:
    op.drop_index(
        "ix_wallet_transactions_transaction_id", table_name="wallet_transactions"
    )
    op.drop_index("ix_wallet_transactions_prepay_id", table_name="wallet_transactions")
    op.drop_index(
        "ix_wallet_transactions_payment_status", table_name="wallet_transactions"
    )

    with op.batch_alter_table("wallet_transactions") as batch_op:
        batch_op.drop_column("notify_processed_at")
        batch_op.drop_column("notify_payload")
        batch_op.drop_column("paid_at")
        batch_op.drop_column("transaction_id")
        batch_op.drop_column("prepay_id")
        batch_op.drop_column("payment_status")
        batch_op.drop_column("payment_provider")
