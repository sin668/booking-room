"""add video thumbnail oss url

Revision ID: k6l2m8n4p0q5
Revises: j5k1l7m3n9p4
Create Date: 2026-11-06 10:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'k6l2m8n4p0q5'
down_revision = 'j5k1l7m3n9p4'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'im_messages',
        sa.Column('thumbnail_oss_url', sa.String(1024), nullable=True, comment='视频缩略图转存后的 OSS 地址'),
    )


def downgrade() -> None:
    op.drop_column('im_messages', 'thumbnail_oss_url')
