"""add gender birthday signature to users

Revision ID: f9b5c3d7e8a4
Revises: e8a4b2d6f7c3
Create Date: 2026-09-18 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'f9b5c3d7e8a4'
down_revision = 'e8a4b2d6f7c3'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column('users', sa.Column('gender', sa.String(10), nullable=True))
    op.add_column('users', sa.Column('birthday', sa.Date(), nullable=True))
    op.add_column('users', sa.Column('signature', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('users', 'signature')
    op.drop_column('users', 'birthday')
    op.drop_column('users', 'gender')
