"""add account security

Revision ID: d0e1f2a3b4c5
Revises: c9d0e1f2a3b4
Create Date: 2026-06-02 16:00:00.000000
"""

from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


revision: str = "d0e1f2a3b4c5"
down_revision: Union[str, None] = "c9d0e1f2a3b4"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_check_constraint(
        "ck_users_status",
        "users",
        "status IN ('active', 'banned', 'disabled', 'deleted')",
    )
    op.create_table(
        "user_identity_verifications",
        sa.Column("id", sa.UUID(), nullable=False),
        sa.Column("user_id", sa.UUID(), nullable=False),
        sa.Column("real_name", sa.String(length=50), nullable=False),
        sa.Column("id_card_hash", sa.String(length=64), nullable=False),
        sa.Column("id_card_masked", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("submitted_at", sa.DateTime(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_user_identity_verifications_user_id"),
        "user_identity_verifications",
        ["user_id"],
        unique=False,
    )
    op.create_index(
        "ix_user_identity_verifications_user_id_status",
        "user_identity_verifications",
        ["user_id", "status"],
        unique=False,
    )
    op.create_index(
        "ix_user_identity_verifications_id_card_hash",
        "user_identity_verifications",
        ["id_card_hash"],
        unique=False,
    )


def downgrade() -> None:
    connection = op.get_bind()
    deleted_count = connection.execute(
        sa.text("SELECT COUNT(*) FROM users WHERE status = 'deleted'")
    ).scalar()
    if deleted_count:
        raise RuntimeError("Cannot downgrade account security while deleted users exist")

    op.drop_index(
        "ix_user_identity_verifications_id_card_hash",
        table_name="user_identity_verifications",
    )
    op.drop_index(
        "ix_user_identity_verifications_user_id_status",
        table_name="user_identity_verifications",
    )
    op.drop_index(
        op.f("ix_user_identity_verifications_user_id"),
        table_name="user_identity_verifications",
    )
    op.drop_table("user_identity_verifications")
    op.drop_constraint("ck_users_status", "users", type_="check")
