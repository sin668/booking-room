"""add_admin_rbac_tables

Revision ID: b7e4a9c1d2f3
Revises: a8c3f1b2d4e5
Create Date: 2026-05-18 18:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b7e4a9c1d2f3"
down_revision: Union[str, None] = "a8c3f1b2d4e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "admin_roles",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("name", sa.String(length=50), nullable=False),
        sa.Column("code", sa.String(length=50), nullable=False),
        sa.Column("description", sa.String(length=255), nullable=True),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("is_default", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("status IN ('active', 'disabled')", name="ck_admin_roles_status"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_roles_code", "admin_roles", ["code"], unique=True)

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

    op.create_table(
        "admin_menus",
        sa.Column("id", sa.Integer(), autoincrement=True, nullable=False),
        sa.Column("parent_id", sa.Integer(), nullable=True),
        sa.Column("type", sa.String(length=20), nullable=False),
        sa.Column("title", sa.String(length=80), nullable=False),
        sa.Column("permission_code", sa.String(length=120), nullable=True),
        sa.Column("path", sa.String(length=255), nullable=True),
        sa.Column("name", sa.String(length=120), nullable=True),
        sa.Column("component", sa.String(length=255), nullable=True),
        sa.Column("redirect", sa.String(length=255), nullable=True),
        sa.Column("icon", sa.String(length=80), nullable=True),
        sa.Column("sort", sa.Integer(), nullable=False),
        sa.Column("hidden", sa.Boolean(), nullable=False),
        sa.Column("keep_alive", sa.Boolean(), nullable=False),
        sa.Column("enabled", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint("type IN ('directory', 'menu', 'button')", name="ck_admin_menus_type"),
        sa.ForeignKeyConstraint(["parent_id"], ["admin_menus.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_admin_menus_parent_id", "admin_menus", ["parent_id"], unique=False)
    op.create_index("ix_admin_menus_permission_code", "admin_menus", ["permission_code"], unique=True)

    op.create_table(
        "system_settings",
        sa.Column("key", sa.String(length=80), nullable=False),
        sa.Column("value", sa.Text(), nullable=True),
        sa.Column("group", sa.String(length=20), nullable=False),
        sa.Column("is_secret", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint('"group" IN (\'basic\', \'email\')', name="ck_system_settings_group"),
        sa.PrimaryKeyConstraint("key"),
    )
    op.create_index("ix_system_settings_group", "system_settings", ["group"], unique=False)

    op.create_table(
        "admin_user_roles",
        sa.Column("admin_user_id", sa.Uuid(), nullable=False),
        sa.Column("admin_role_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["admin_role_id"], ["admin_roles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_user_id"], ["admin_users.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("admin_user_id", "admin_role_id"),
        sa.UniqueConstraint("admin_user_id", "admin_role_id", name="uq_admin_user_roles"),
    )

    op.create_table(
        "admin_role_menus",
        sa.Column("admin_role_id", sa.Integer(), nullable=False),
        sa.Column("admin_menu_id", sa.Integer(), nullable=False),
        sa.ForeignKeyConstraint(["admin_menu_id"], ["admin_menus.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["admin_role_id"], ["admin_roles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("admin_role_id", "admin_menu_id"),
        sa.UniqueConstraint("admin_role_id", "admin_menu_id", name="uq_admin_role_menus"),
    )


def downgrade() -> None:
    op.drop_table("admin_role_menus")
    op.drop_table("admin_user_roles")
    op.drop_index("ix_system_settings_group", table_name="system_settings")
    op.drop_table("system_settings")
    op.drop_index("ix_admin_menus_permission_code", table_name="admin_menus")
    op.drop_index("ix_admin_menus_parent_id", table_name="admin_menus")
    op.drop_table("admin_menus")
    op.drop_index("ix_admin_users_username", table_name="admin_users")
    op.drop_table("admin_users")
    op.drop_index("ix_admin_roles_code", table_name="admin_roles")
    op.drop_table("admin_roles")
