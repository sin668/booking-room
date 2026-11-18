"""rename user_type to user_source; convert is_super_admin to user_type enum

Revision ID: m8n4p0q6r2s7
Revises: l7m3n9p5q1r6
Create Date: 2026-11-18 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'm8n4p0q6r2s7'
down_revision = 'l7m3n9p5q1r6'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # 第一步：旧 user_type（用户来源 app/admin）改名为 user_source
    op.drop_constraint('ck_users_user_type', 'users', type_='check')
    op.alter_column('users', 'user_type', new_column_name='user_source')
    op.create_check_constraint('ck_users_user_source', 'users', "user_source IN ('app', 'admin')")

    # 第二步：is_super_admin 布尔转换为 user_type 枚举（super-admin/normal-user）
    op.add_column('users', sa.Column('user_type', sa.String(length=20), nullable=True))
    op.execute(
        "UPDATE users SET user_type = CASE WHEN is_super_admin THEN 'super-admin' ELSE 'normal-user' END"
    )
    op.alter_column('users', 'user_type', nullable=False, server_default='normal-user')
    op.drop_column('users', 'is_super_admin')
    op.create_check_constraint('ck_users_user_type', 'users', "user_type IN ('super-admin', 'normal-user')")


def downgrade() -> None:
    op.drop_constraint('ck_users_user_type', 'users', type_='check')
    op.add_column('users', sa.Column('is_super_admin', sa.Boolean(), nullable=True))
    op.execute("UPDATE users SET is_super_admin = (user_type = 'super-admin')")
    op.alter_column('users', 'is_super_admin', nullable=False, server_default=sa.text('false'))
    op.drop_column('users', 'user_type')

    op.drop_constraint('ck_users_user_source', 'users', type_='check')
    op.alter_column('users', 'user_source', new_column_name='user_type')
    op.create_check_constraint('ck_users_user_type', 'users', "user_type IN ('app', 'admin')")