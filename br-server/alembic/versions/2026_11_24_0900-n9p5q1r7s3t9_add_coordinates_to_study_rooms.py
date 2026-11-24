"""add latitude and longitude to study_rooms

Revision ID: n9p5q1r7s3t9
Revises: m8n4p0q6r2s7
Create Date: 2026-11-24 09:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'n9p5q1r7s3t9'
down_revision = 'm8n4p0q6r2s7'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'study_rooms',
        sa.Column('latitude', sa.Numeric(10, 7), nullable=True, comment='GCJ-02 纬度'),
    )
    op.add_column(
        'study_rooms',
        sa.Column('longitude', sa.Numeric(10, 7), nullable=True, comment='GCJ-02 经度'),
    )


def downgrade() -> None:
    op.drop_column('study_rooms', 'longitude')
    op.drop_column('study_rooms', 'latitude')
