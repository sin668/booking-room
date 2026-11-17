"""add created_by to admin content tables

Revision ID: l7m3n9p5q1r6
Revises: k6l2m8n4p0q5
Create Date: 2026-11-17 17:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'l7m3n9p5q1r6'
down_revision = 'k6l2m8n4p0q5'
branch_labels = None
depends_on = None

_TABLES = ('courses', 'activities', 'study_rooms', 'coupons', 'teachers')


def upgrade() -> None:
    for table in _TABLES:
        op.add_column(table, sa.Column('created_by', sa.Uuid(), nullable=True))
        op.create_index(f'ix_{table}_created_by', table, ['created_by'])


def downgrade() -> None:
    for table in _TABLES:
        op.drop_index(f'ix_{table}_created_by', table_name=table)
        op.drop_column(table, 'created_by')