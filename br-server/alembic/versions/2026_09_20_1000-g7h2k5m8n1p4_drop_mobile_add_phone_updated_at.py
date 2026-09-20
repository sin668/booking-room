"""drop mobile and add phone_updated_at to users

Revision ID: g7h2k5m8n1p4
Revises: f9b5c3d7e8a4
Create Date: 2026-09-20 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'g7h2k5m8n1p4'
down_revision = 'f9b5c3d7e8a4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.drop_column('users', 'mobile')
    op.add_column('users', sa.Column('phone_updated_at', sa.DateTime(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'phone_updated_at')
    op.add_column('users', sa.Column('mobile', sa.String(length=20), nullable=True))
