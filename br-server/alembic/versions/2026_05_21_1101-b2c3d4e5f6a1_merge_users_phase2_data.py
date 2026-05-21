"""merge_users_phase2_data

Migrate data from admin_users into users table and update admin_user_roles FK.

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-05-21 11:01:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Make phone nullable so admin users (who have no phone) can be inserted
    op.alter_column("users", "phone", existing_type=sa.String(length=11), nullable=True)

    # Insert admin_users rows into users, handling potential ID conflicts
    # by generating new UUIDs for colliding rows and updating admin_user_roles.
    op.execute("""
        DO $$
        DECLARE
            admin_rec RECORD;
            new_id UUID;
            conflict_ids UUID[] := ARRAY[]::UUID[];
        BEGIN
            FOR admin_rec IN
                SELECT id, username, password_hash, nickname, email, mobile,
                       avatar, status, is_super_admin, created_at, updated_at
                FROM admin_users
            LOOP
                -- Check if this ID already exists in users
                IF EXISTS (SELECT 1 FROM users WHERE id = admin_rec.id) THEN
                    new_id := gen_random_uuid();
                    conflict_ids := array_append(conflict_ids, admin_rec.id);

                    INSERT INTO users (
                        id, user_type, username, password_hash, nickname,
                        email, mobile, avatar, status, is_super_admin,
                        created_at, updated_at
                    ) VALUES (
                        new_id, 'admin', admin_rec.username, admin_rec.password_hash,
                        COALESCE(admin_rec.nickname, ''), admin_rec.email,
                        admin_rec.mobile, admin_rec.avatar, admin_rec.status,
                        admin_rec.is_super_admin, admin_rec.created_at, admin_rec.updated_at
                    );

                    -- Update admin_user_roles to point to the new user ID
                    UPDATE admin_user_roles
                    SET admin_user_id = new_id
                    WHERE admin_user_id = admin_rec.id;
                ELSE
                    INSERT INTO users (
                        id, user_type, username, password_hash, nickname,
                        email, mobile, avatar, status, is_super_admin,
                        created_at, updated_at
                    ) VALUES (
                        admin_rec.id, 'admin', admin_rec.username, admin_rec.password_hash,
                        COALESCE(admin_rec.nickname, ''), admin_rec.email,
                        admin_rec.mobile, admin_rec.avatar, admin_rec.status,
                        admin_rec.is_super_admin, admin_rec.created_at, admin_rec.updated_at
                    );
                END IF;
            END LOOP;

            -- Log conflicted IDs for reference (if any)
            IF array_length(conflict_ids, 1) > 0 THEN
                RAISE NOTICE 'Admin user IDs remapped due to conflicts: %', conflict_ids;
            END IF;
        END;
        $$
    """)

    # --- Now that admin data is in users, update admin_user_roles FK ---
    # Drop old FK referencing admin_users.id
    op.drop_constraint(
        "admin_user_roles_admin_user_id_fkey", "admin_user_roles", type_="foreignkey"
    )
    # Rename column
    op.alter_column("admin_user_roles", "admin_user_id", new_column_name="user_id")
    # Create new FK referencing users.id
    op.create_foreign_key(
        "admin_user_roles_user_id_fkey",
        "admin_user_roles",
        "users",
        ["user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    # Update unique constraint to reference renamed column
    op.drop_constraint("uq_admin_user_roles", "admin_user_roles", type_="unique")
    op.create_unique_constraint("uq_admin_user_roles", "admin_user_roles", ["user_id", "admin_role_id"])


def downgrade() -> None:
    # Revert admin_user_roles FK changes
    op.drop_constraint("uq_admin_user_roles", "admin_user_roles", type_="unique")
    op.create_unique_constraint("uq_admin_user_roles", "admin_user_roles", ["admin_user_id", "admin_role_id"])

    op.drop_constraint("admin_user_roles_user_id_fkey", "admin_user_roles", type_="foreignkey")
    op.create_foreign_key(
        "admin_user_roles_admin_user_id_fkey",
        "admin_user_roles",
        "admin_users",
        ["admin_user_id"],
        ["id"],
        ondelete="CASCADE",
    )
    op.alter_column("admin_user_roles", "user_id", new_column_name="admin_user_id")

    # Remove admin-type rows from users table
    op.execute("DELETE FROM users WHERE user_type = 'admin'")
