"""drop lesson_schedule column and create lesson_schedules table

Revision ID: f5a6b7c8d9e0
Revises: e4f5a6b7c8d9
Create Date: 2026-08-26 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f5a6b7c8d9e0'
down_revision: str = 'e4f5a6b7c8d9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. 删除 course_schedules.lesson_schedule 列
    op.drop_column('course_schedules', 'lesson_schedule')

    # 2. 创建 lesson_schedules 中间表
    op.create_table(
        'lesson_schedules',
        sa.Column('id', sa.Integer(), autoincrement=True, nullable=False),
        sa.Column('schedule_id', sa.Integer(), nullable=False, comment='排课记录ID'),
        sa.Column('lesson_id', sa.Integer(), nullable=False, comment='课时ID'),
        sa.Column('lesson_date', sa.Date(), nullable=False, comment='上课日期'),
        sa.Column('lesson_time_slot', sa.String(50), nullable=False, comment='上课时间段，如 08:00-10:00'),
        sa.Column('sort_order', sa.Integer(), nullable=False, server_default='0', comment='排序序号'),
        sa.ForeignKeyConstraint(['schedule_id'], ['course_schedules.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['lesson_id'], ['course_lessons.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index('ix_lesson_schedules_schedule_id', 'lesson_schedules', ['schedule_id'])
    op.create_index('ix_lesson_schedules_lesson_id', 'lesson_schedules', ['lesson_id'])


def downgrade() -> None:
    op.drop_index('ix_lesson_schedules_lesson_id', table_name='lesson_schedules')
    op.drop_index('ix_lesson_schedules_schedule_id', table_name='lesson_schedules')
    op.drop_table('lesson_schedules')
    op.add_column(
        'course_schedules',
        sa.Column('lesson_schedule', sa.Text(), nullable=True, comment='课时安排JSON，存储每个课时的实际上课日期时间'),
    )
