"""add_wallet_membership_result

Revision ID: a2b3c4d5e6f7
Revises: df6ae550899a
Create Date: 2026-06-08 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a2b3c4d5e6f7"
down_revision: Union[str, None] = "df6ae550899a"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "sqlite":
        with op.batch_alter_table("wallet_transactions", recreate="always") as batch_op:
            batch_op.add_column(
                sa.Column("membership_upgraded", sa.Boolean(), nullable=False, server_default=sa.false())
            )
            batch_op.add_column(sa.Column("vip_coupon_id", sa.Integer(), nullable=True))
    else:
        op.add_column(
            "wallet_transactions",
            sa.Column("membership_upgraded", sa.Boolean(), nullable=False, server_default=sa.false()),
        )
        op.add_column("wallet_transactions", sa.Column("vip_coupon_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_wallet_transactions_vip_coupon_id",
            "wallet_transactions",
            "user_coupons",
            ["vip_coupon_id"],
            ["id"],
        )


def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name
    if dialect_name == "sqlite":
        with op.batch_alter_table("wallet_transactions", recreate="always") as batch_op:
            batch_op.drop_column("vip_coupon_id")
            batch_op.drop_column("membership_upgraded")
    else:
        op.drop_constraint("fk_wallet_transactions_vip_coupon_id", "wallet_transactions", type_="foreignkey")
        op.drop_column("wallet_transactions", "vip_coupon_id")
        op.drop_column("wallet_transactions", "membership_upgraded")
