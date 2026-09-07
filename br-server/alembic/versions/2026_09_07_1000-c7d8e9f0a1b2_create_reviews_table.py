"""create_reviews_table

Revision ID: c7d8e9f0a1b2
Revises: b4e7a1c9d3f6
Create Date: 2026-09-07 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c7d8e9f0a1b2'
down_revision: Union[str, None] = 'b4e7a1c9d3f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        'reviews',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('booking_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Uuid(), nullable=False),
        sa.Column('course_id', sa.Integer(), nullable=True),
        sa.Column('teacher_id', sa.Integer(), nullable=True),
        sa.Column('rating', sa.Integer(), nullable=False, comment='综合星级 1-5'),
        sa.Column('content', sa.String(length=500), nullable=False),
        sa.Column('images', sa.JSON(), nullable=True, comment='评价图片 URL 列表，最多 9 张'),
        sa.Column('tags', sa.JSON(), nullable=True, comment='评价标签列表，最多 5 个'),
        sa.Column('is_anonymous', sa.Boolean(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('reject_reason', sa.String(length=200), nullable=True),
        sa.Column('reply_content', sa.String(length=500), nullable=True, comment='机构回复'),
        sa.Column('reply_at', sa.DateTime(), nullable=True),
        sa.Column('reviewed_by', sa.Uuid(), nullable=True),
        sa.Column('reviewed_at', sa.DateTime(), nullable=True),
        sa.Column('created_at', sa.DateTime(), nullable=False),
        sa.Column('updated_at', sa.DateTime(), nullable=False),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['course_id'], ['courses.id'], ondelete='SET NULL'),
        sa.ForeignKeyConstraint(['teacher_id'], ['teachers.id'], ondelete='SET NULL'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('booking_id'),
    )
    op.create_index('ix_reviews_status', 'reviews', ['status'])
    # 复合索引的最左前缀已覆盖单列过滤，故不建冗余单列索引
    op.create_index('ix_reviews_course_id_created_at', 'reviews', ['course_id', 'created_at'])
    op.create_index('ix_reviews_teacher_id_created_at', 'reviews', ['teacher_id', 'created_at'])
    op.create_index('ix_reviews_user_id_created_at', 'reviews', ['user_id', 'created_at'])

    # 评价条数改为写时更新（审核状态变更时全量重算），避免课程/老师列表页的 N 次 COUNT 子查询
    op.add_column(
        'courses',
        sa.Column('review_count', sa.Integer(), nullable=False, server_default='0'),
    )
    op.add_column(
        'teachers',
        sa.Column(
            'review_count',
            sa.Integer(),
            nullable=False,
            server_default='0',
            comment='已通过审核的评价数，与 student_count（学员数）语义不同',
        ),
    )
    # server_default 只为让存量行通过 NOT NULL 校验，随后移除以保持与 ORM 定义一致
    op.alter_column('courses', 'review_count', server_default=None)
    op.alter_column('teachers', 'review_count', server_default=None)


def downgrade() -> None:
    op.drop_column('teachers', 'review_count')
    op.drop_column('courses', 'review_count')
    op.drop_index('ix_reviews_user_id_created_at', table_name='reviews')
    op.drop_index('ix_reviews_teacher_id_created_at', table_name='reviews')
    op.drop_index('ix_reviews_course_id_created_at', table_name='reviews')
    op.drop_index('ix_reviews_status', table_name='reviews')
    op.drop_table('reviews')
