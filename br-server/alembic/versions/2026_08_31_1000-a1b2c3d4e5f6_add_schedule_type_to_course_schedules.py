"""add_schedule_type_to_course_schedules

Revision ID: e8f9a0b1c2d3
Revises: 97bc597327c1
Create Date: 2026-08-31 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e8f9a0b1c2d3'
down_revision: Union[str, None] = '97bc597327c1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'course_schedules',
        sa.Column(
            'schedule_type',
            sa.String(20),
            nullable=False,
            server_default='fixed',
            comment='排课类型: fixed=固定班课, custom=定制课时',
        ),
    )


def downgrade() -> None:
    op.drop_column('course_schedules', 'schedule_type')
