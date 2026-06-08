"""add_membership_level

Revision ID: df6ae550899a
Revises: f1a2b3c4d5e6
Create Date: 2026-06-08 11:06:31.554928

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'df6ae550899a'
down_revision: Union[str, None] = 'f1a2b3c4d5e6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('users', sa.Column('membership_level', sa.String(length=20), nullable=False, server_default='none'))
    op.create_check_constraint('ck_users_membership_level', 'users', "membership_level IN ('none', 'vip', 'svip')")


def downgrade() -> None:
    op.drop_constraint('ck_users_membership_level', 'users', type_='check')
    op.drop_column('users', 'membership_level')
