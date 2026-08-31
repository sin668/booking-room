"""add time_slots and teacher_id to bookings

Revision ID: b9c0d1e2f3a4
Revises: e8f9a0b1c2d3
Create Date: 2026-08-31 11:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b9c0d1e2f3a4'
down_revision: Union[str, None] = 'e8f9a0b1c2d3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bookings',
        sa.Column(
            'time_slots',
            sa.Text(),
            nullable=True,
            comment='1V1私人定制上课时间段，JSON 数组格式，对应 course_schedules.time_slots',
        ),
    )
    op.add_column(
        'bookings',
        sa.Column(
            'teacher_id',
            sa.Integer(),
            nullable=True,
            comment='授课老师，对应 course_schedules.teacher_id',
        ),
    )
    op.create_foreign_key(
        'fk_bookings_teacher_id',
        'bookings', 'teachers',
        ['teacher_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_bookings_teacher_id', 'bookings', type_='foreignkey')
    op.drop_column('bookings', 'teacher_id')
    op.drop_column('bookings', 'time_slots')
