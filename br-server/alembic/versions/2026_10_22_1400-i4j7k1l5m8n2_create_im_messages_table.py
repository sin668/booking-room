"""create im_messages table

Revision ID: i4j7k1l5m8n2
Revises: h8i3j6k9l2m5
Create Date: 2026-10-22 14:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'i4j7k1l5m8n2'
down_revision = 'h8i3j6k9l2m5'
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        'im_messages',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('msg_key', sa.String(length=128), nullable=False, comment='腾讯云 IM MsgKey，消息唯一标识'),
        sa.Column('im_from_account', sa.String(length=64), nullable=False),
        sa.Column('im_to_account', sa.String(length=64), nullable=False),
        sa.Column('from_user_id', sa.Uuid(), nullable=True),
        sa.Column('to_user_id', sa.Uuid(), nullable=True),
        sa.Column('msg_seq', sa.BigInteger(), nullable=True),
        sa.Column('msg_time', sa.BigInteger(), nullable=False, comment='消息发送时间戳（秒，取 IM MsgTime）'),
        sa.Column('element_type', sa.String(length=32), nullable=False, comment='text / image / sound / custom / other'),
        sa.Column('content', sa.Text(), nullable=True, comment='文本内容或媒体描述摘要'),
        sa.Column('media_url', sa.String(length=1024), nullable=True, comment='IM/COS 原始媒体地址'),
        sa.Column('oss_url', sa.String(length=1024), nullable=True, comment='服务端转存后的 OSS 地址'),
        sa.Column('is_read', sa.Boolean(), nullable=False),
        sa.Column('read_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('raw_payload', sa.JSON(), nullable=True, comment='回调原始 MsgBody'),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.ForeignKeyConstraint(['from_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['to_user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('msg_key'),
    )
    op.create_index('ix_im_messages_pair_time', 'im_messages', ['im_from_account', 'im_to_account', 'msg_time'])
    op.create_index('ix_im_messages_read_state', 'im_messages', ['im_to_account', 'is_read'])


def downgrade() -> None:
    op.drop_index('ix_im_messages_read_state', table_name='im_messages')
    op.drop_index('ix_im_messages_pair_time', table_name='im_messages')
    op.drop_table('im_messages')
