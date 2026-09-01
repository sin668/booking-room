"""add_schedule_id_to_bookings

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-09-01 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'bookings',
        sa.Column(
            'schedule_id',
            sa.Integer(),
            nullable=True,
            comment='订单关联的排课记录（固定班课排课 / 定制订单确认后创建的定制排课）',
        ),
    )
    op.create_foreign_key(
        'fk_bookings_schedule_id_course_schedules',
        'bookings', 'course_schedules',
        ['schedule_id'], ['id'],
    )

    # 回填固定班课订单：关联课程的 fixed 排课（最早创建的一条）
    op.execute(
        """
        UPDATE bookings b
        SET schedule_id = s.id
        FROM course_schedules s
        WHERE b.booking_type = 'course'
          AND b.schedule_type = 'fixed'
          AND b.course_id IS NOT NULL
          AND b.schedule_id IS NULL
          AND s.course_id = b.course_id
          AND s.schedule_type = 'fixed'
          AND s.id = (
              SELECT MIN(s2.id) FROM course_schedules s2
              WHERE s2.course_id = b.course_id AND s2.schedule_type = 'fixed'
          )
        """
    )

    # 回填定制订单：关联同课程、开课日期等于订单预约日期的 custom 排课（最近创建的一条）
    op.execute(
        """
        UPDATE bookings b
        SET schedule_id = s.id
        FROM course_schedules s
        WHERE b.booking_type = 'course'
          AND b.schedule_type = 'custom'
          AND b.course_id IS NOT NULL
          AND b.schedule_id IS NULL
          AND s.course_id = b.course_id
          AND s.schedule_type = 'custom'
          AND s.start_date = b.date
          AND s.id = (
              SELECT MAX(s2.id) FROM course_schedules s2
              WHERE s2.course_id = b.course_id
                AND s2.schedule_type = 'custom'
                AND s2.start_date = b.date
          )
        """
    )


def downgrade() -> None:
    op.drop_constraint('fk_bookings_schedule_id_course_schedules', 'bookings', type_='foreignkey')
    op.drop_column('bookings', 'schedule_id')
