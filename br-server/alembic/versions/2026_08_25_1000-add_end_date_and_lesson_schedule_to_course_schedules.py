"""add end_date and lesson_schedule to course_schedules

Revision ID: e4f5a6b7c8d9
Revises: d3e4f5a6b7c8
Create Date: 2026-08-25 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e4f5a6b7c8d9'
down_revision: str = 'd3e4f5a6b7c8'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('course_schedules', sa.Column('end_date', sa.Date(), nullable=True, comment='课程结束日期'))
    op.add_column('course_schedules', sa.Column('lesson_schedule', sa.Text(), nullable=True, comment='课时安排JSON，存储每个课时的实际上课日期时间'))


def downgrade() -> None:
    op.drop_column('course_schedules', 'lesson_schedule')
    op.drop_column('course_schedules', 'end_date')
