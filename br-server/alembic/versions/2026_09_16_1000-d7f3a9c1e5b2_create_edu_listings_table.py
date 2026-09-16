"""create_edu_listings_table

Revision ID: d7f3a9c1e5b2
Revises: 195bfc67f12a
Create Date: 2026-09-16 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd7f3a9c1e5b2'
down_revision: Union[str, None] = '195bfc67f12a'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'edu_listings',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('listing_type', sa.String(length=20), nullable=False, comment='tutor 家教 / training 培训班 / demand 求教'),
        sa.Column('title', sa.String(length=100), nullable=False),
        sa.Column('subject', sa.String(length=50), nullable=True, comment='科目分类'),
        sa.Column('teaching_mode', sa.String(length=50), nullable=True, comment='授课/求学方式'),
        sa.Column('price', sa.Numeric(precision=10, scale=2), nullable=True),
        sa.Column('price_unit', sa.String(length=20), nullable=True, comment='价格单位'),
        sa.Column('area', sa.String(length=100), nullable=True, comment='服务区域'),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('images', sa.JSON(), nullable=True, comment='图片 URL 列表，最多 3 张'),
        sa.Column('available_times', sa.JSON(), nullable=True, comment='可授课/可求学时间列表'),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reject_reason', sa.String(length=200), nullable=True),
        sa.Column('view_count', sa.Integer(), nullable=False),
        sa.Column('reviewed_by', sa.Uuid(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "listing_type IN ('tutor', 'training', 'demand')",
            name='ck_edu_listings_listing_type',
        ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_edu_listings_status', 'edu_listings', ['status'])
    # 复合索引覆盖广场按类型+状态过滤后按时间排序的主查询路径
    op.create_index(
        'ix_edu_listings_type_status_created',
        'edu_listings',
        ['listing_type', 'status', 'created_at'],
    )


def downgrade() -> None:
    op.drop_index('ix_edu_listings_type_status_created', table_name='edu_listings')
    op.drop_index('ix_edu_listings_status', table_name='edu_listings')
    op.drop_table('edu_listings')
