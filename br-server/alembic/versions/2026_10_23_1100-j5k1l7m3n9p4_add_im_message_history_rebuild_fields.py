"""add im message history rebuild fields

Revision ID: j5k1l7m3n9p4
Revises: i4j7k1l5m8n2
Create Date: 2026-10-23 11:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'j5k1l7m3n9p4'
down_revision = 'i4j7k1l5m8n2'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        'im_messages',
        sa.Column('cloud_custom_data', sa.Text(), nullable=True, comment='消息自定义数据 CloudCustomData，引用/回复内容载体'),
    )
    op.add_column(
        'im_messages',
        sa.Column('is_revoked', sa.Boolean(), server_default=sa.text('false'), nullable=False, comment='是否已被撤回，由 C2C.CallbackAfterMsgWithDraw 回写'),
    )
    op.add_column(
        'im_messages',
        sa.Column('revoke_time', sa.BigInteger(), nullable=True, comment='撤回事件时间戳（毫秒，取回调 EventTime）'),
    )


def downgrade() -> None:
    op.drop_column('im_messages', 'revoke_time')
    op.drop_column('im_messages', 'is_revoked')
    op.drop_column('im_messages', 'cloud_custom_data')
