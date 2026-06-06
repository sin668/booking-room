"""add_activity_coupon_campaign

Revision ID: f1a2b3c4d5e6
Revises: d0e1f2a3b4c5
Create Date: 2026-06-06 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "f1a2b3c4d5e6"
down_revision: Union[str, None] = "d0e1f2a3b4c5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    dialect_name = op.get_bind().dialect.name

    op.add_column(
        "activities",
        sa.Column("content_html", sa.Text(), server_default="", nullable=False),
    )

    op.create_table(
        "activity_coupons",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("activity_id", sa.Integer(), sa.ForeignKey("activities.id"), nullable=False),
        sa.Column("coupon_id", sa.Integer(), sa.ForeignKey("coupons.id"), nullable=False),
        sa.Column("total_quantity", sa.Integer(), nullable=False),
        sa.Column("claimed_quantity", sa.Integer(), server_default="0", nullable=False),
        sa.Column("per_user_limit", sa.Integer(), server_default="1", nullable=False),
        sa.Column("claim_starts_at", sa.DateTime(), nullable=True),
        sa.Column("claim_ends_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.true(), nullable=False),
        sa.Column("sort_order", sa.Integer(), server_default="0", nullable=False),
        sa.Column("display_title", sa.String(length=100), nullable=True),
        sa.Column("display_description", sa.String(length=255), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("total_quantity >= 0", name="ck_activity_coupons_total_quantity_non_negative"),
        sa.CheckConstraint("claimed_quantity >= 0", name="ck_activity_coupons_claimed_quantity_non_negative"),
        sa.CheckConstraint("claimed_quantity <= total_quantity", name="ck_activity_coupons_claimed_not_over_total"),
        sa.CheckConstraint("per_user_limit > 0", name="ck_activity_coupons_per_user_limit_positive"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_activity_coupons_activity_id", "activity_coupons", ["activity_id"])
    op.create_index("ix_activity_coupons_coupon_id", "activity_coupons", ["coupon_id"])
    op.create_index("ix_activity_coupons_activity_sort", "activity_coupons", ["activity_id", "sort_order"])

    if dialect_name == "sqlite":
        with op.batch_alter_table("user_coupons", recreate="always") as batch_op:
            batch_op.add_column(sa.Column("source_type", sa.String(length=30), nullable=True))
            batch_op.add_column(sa.Column("source_activity_id", sa.Integer(), nullable=True))
            batch_op.add_column(sa.Column("source_activity_coupon_id", sa.Integer(), nullable=True))
    else:
        op.add_column("user_coupons", sa.Column("source_type", sa.String(length=30), nullable=True))
        op.add_column("user_coupons", sa.Column("source_activity_id", sa.Integer(), nullable=True))
        op.add_column("user_coupons", sa.Column("source_activity_coupon_id", sa.Integer(), nullable=True))
        op.create_foreign_key(
            "fk_user_coupons_source_activity_id",
            "user_coupons",
            "activities",
            ["source_activity_id"],
            ["id"],
        )
        op.create_foreign_key(
            "fk_user_coupons_source_activity_coupon_id",
            "user_coupons",
            "activity_coupons",
            ["source_activity_coupon_id"],
            ["id"],
        )

    op.create_index("ix_user_coupons_source_activity", "user_coupons", ["source_activity_id"])
    op.create_index("ix_user_coupons_source_activity_coupon", "user_coupons", ["source_activity_coupon_id"])


def downgrade() -> None:
    dialect_name = op.get_bind().dialect.name

    op.drop_index("ix_user_coupons_source_activity_coupon", table_name="user_coupons")
    op.drop_index("ix_user_coupons_source_activity", table_name="user_coupons")

    if dialect_name == "sqlite":
        with op.batch_alter_table("user_coupons", recreate="always") as batch_op:
            batch_op.drop_column("source_activity_coupon_id")
            batch_op.drop_column("source_activity_id")
            batch_op.drop_column("source_type")
    else:
        op.drop_constraint("fk_user_coupons_source_activity_coupon_id", "user_coupons", type_="foreignkey")
        op.drop_constraint("fk_user_coupons_source_activity_id", "user_coupons", type_="foreignkey")
        op.drop_column("user_coupons", "source_activity_coupon_id")
        op.drop_column("user_coupons", "source_activity_id")
        op.drop_column("user_coupons", "source_type")

    op.drop_index("ix_activity_coupons_activity_sort", table_name="activity_coupons")
    op.drop_index("ix_activity_coupons_coupon_id", table_name="activity_coupons")
    op.drop_index("ix_activity_coupons_activity_id", table_name="activity_coupons")
    op.drop_table("activity_coupons")
    op.drop_column("activities", "content_html")
