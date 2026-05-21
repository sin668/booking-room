"""merge_users_phase1_extend

Extend users table with admin-user fields and rename admin_user_roles FK.

Revision ID: a1b2c3d4e5f6
Revises: b7e4a9c1d2f3
Create Date: 2026-05-21 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, None] = "b7e4a9c1d2f3"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # --- Add new columns to users table ---
    op.add_column("users", sa.Column("user_type", sa.String(length=10), nullable=False, server_default="app"))
    op.add_column("users", sa.Column("username", sa.String(length=50), nullable=True))
    op.add_column("users", sa.Column("email", sa.String(length=255), nullable=True))
    op.add_column("users", sa.Column("mobile", sa.String(length=20), nullable=True))
    op.add_column("users", sa.Column("avatar", sa.String(length=512), nullable=True))
    op.add_column("users", sa.Column("is_super_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")))

    # Add CHECK constraint on user_type
    op.create_check_constraint("ck_users_user_type", "users", "user_type IN ('app', 'admin')")

    # Replace the existing ix_users_phone unique index with a partial unique index
    op.drop_index("ix_users_phone", table_name="users")
    op.execute(
        "CREATE UNIQUE INDEX ix_users_phone ON users (phone) WHERE phone IS NOT NULL"
    )

    # Create partial unique index on username
    op.execute(
        "CREATE UNIQUE INDEX ix_users_username ON users (username) WHERE username IS NOT NULL"
    )

    # NOTE: admin_user_roles FK changes are deferred to Phase 2,
    # after admin_users data has been migrated into the users table.


def downgrade() -> None:
    # Drop partial indexes and restore original ix_users_phone
    op.drop_index("ix_users_username", table_name="users")
    op.execute("DROP INDEX ix_users_phone")
    op.create_index("ix_users_phone", "users", ["phone"], unique=True)

    # Drop CHECK constraint
    op.drop_constraint("ck_users_user_type", "users", type_="check")

    # Drop new columns
    op.drop_column("users", "is_super_admin")
    op.drop_column("users", "avatar")
    op.drop_column("users", "mobile")
    op.drop_column("users", "email")
    op.drop_column("users", "username")
    op.drop_column("users", "user_type")
