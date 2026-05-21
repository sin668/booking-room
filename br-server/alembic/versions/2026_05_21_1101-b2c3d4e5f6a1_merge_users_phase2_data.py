"""merge_users_phase2_data

Migrate data from admin_users into users table.

Revision ID: b2c3d4e5f6a1
Revises: a1b2c3d4e5f6
Create Date: 2026-05-21 11:01:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b2c3d4e5f6a1"
down_revision: Union[str, None] = "a1b2c3d4e5f6"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
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
                    SET user_id = new_id
                    WHERE user_id = admin_rec.id;
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


def downgrade() -> None:
    # Remove admin-type rows from users table
    op.execute("DELETE FROM users WHERE user_type = 'admin'")
