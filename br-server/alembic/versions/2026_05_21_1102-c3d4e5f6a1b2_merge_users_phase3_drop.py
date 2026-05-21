"""merge_users_phase3_drop

Drop admin_users table now that data has been merged into users.

Revision ID: c3d4e5f6a1b2
Revises: b2c3d4e5f6a1
Create Date: 2026-05-21 11:02:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "c3d4e5f6a1b2"
down_revision: Union[str, None] = "b2c3d4e5f6a1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.drop_index("ix_admin_users_username", table_name="admin_users")
    op.drop_table("admin_users")


def downgrade() -> None:
    # Recreate admin_users table
    op.create_table(
        "admin_users",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("username", sa.String(length=50), nullable=False),
        sa.Column("password_hash", sa.String(length=512), nullable=False),
        sa.Column("nickname", sa.String(length=50), nullable=True),
        sa.Column("email", sa.String(length=255), nullable=True),
        sa.Column("mobile", sa.String(length=20), nullable=True),
        sa.Column("avatar", sa.String(length=512), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("is_super_admin", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_admin_users_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_users_username", "admin_users", ["username"], unique=True)

    # Re-populate admin_users from users table
    op.execute("""
        INSERT INTO admin_users (
            id, username, password_hash, nickname, email, mobile,
            avatar, status, is_super_admin, created_at, updated_at
        )
        SELECT id, username, password_hash, nickname, email, mobile,
               avatar, status, is_super_admin, created_at, updated_at
        FROM users
        WHERE user_type = 'admin'
    """)

    # Restore admin_user_roles FK to reference admin_users
    op.drop_constraint("admin_user_roles_user_id_fkey", "admin_user_roles", type_="foreignkey")
    op.drop_constraint("uq_admin_user_roles", "admin_user_roles", type_="unique")
    op.alter_column("admin_user_roles", "user_id", new_column_name="admin_user_id")
    op.create_unique_constraint("uq_admin_user_roles", "admin_user_roles", ["admin_user_id", "admin_role_id"])
    op.create_foreign_key(
        "admin_user_roles_admin_user_id_fkey",
        "admin_user_roles",
        "admin_users",
        ["admin_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
