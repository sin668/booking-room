"""add city_id to edu_listings

Revision ID: e8a4b2d6f7c3
Revises: d7f3a9c1e5b2
Create Date: 2026-09-16 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'e8a4b2d6f7c3'
down_revision = 'd7f3a9c1e5b2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Add city_id column with index
    op.add_column('edu_listings', sa.Column('city_id', sa.Integer(), nullable=True))
    op.create_index(op.f('ix_edu_listings_city_id'), 'edu_listings', ['city_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_edu_listings_city_id'), table_name='edu_listings')
    op.drop_column('edu_listings', 'city_id')
