"""add course booking fields

Revision ID: a1b2c3d4e5f7
Revises: e7f8a9b0c1d2
Create Date: 2026-08-17 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import ARRAY


# revision identifiers, used by Alembic.
revision: str = 'a1b2c3d4e5f7'
down_revision: Union[str, None] = 'e7f8a9b0c1d2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # courses 表新增字段
    op.add_column('courses', sa.Column('custom_price', sa.Numeric(10, 2), server_default='0', nullable=False))
    op.add_column('courses', sa.Column('full_package_price', sa.Numeric(10, 2), nullable=True))

    # bookings 表新增字段
    op.add_column('bookings', sa.Column('booking_type', sa.String(20), server_default='seat', nullable=False))
    op.add_column('bookings', sa.Column('course_id', sa.Integer(), nullable=True))
    op.add_column('bookings', sa.Column('lesson_ids', ARRAY(sa.Integer()), nullable=True))
    op.add_column('bookings', sa.Column('schedule_type', sa.String(20), nullable=True))

    # bookings.seat_id 改为 nullable
    op.alter_column(
        'bookings', 'seat_id',
        existing_type=sa.Integer(),
        nullable=True,
        existing_nullable=False,
    )

    # bookings 表添加 booking_type 索引
    op.create_index(op.f('ix_bookings_booking_type'), 'bookings', ['booking_type'])

    # bookings 表添加 course_id 外键
    op.create_foreign_key(
        'fk_bookings_course_id',
        'bookings', 'courses',
        ['course_id'], ['id'],
    )


def downgrade() -> None:
    op.drop_constraint('fk_bookings_course_id', 'bookings', type_='foreignkey')
    op.drop_index(op.f('ix_bookings_booking_type'), table_name='bookings')

    op.alter_column(
        'bookings', 'seat_id',
        existing_type=sa.Integer(),
        nullable=False,
        existing_nullable=True,
    )

    op.drop_column('bookings', 'schedule_type')
    op.drop_column('bookings', 'lesson_ids')
    op.drop_column('bookings', 'course_id')
    op.drop_column('bookings', 'booking_type')

    op.drop_column('courses', 'full_package_price')
    op.drop_column('courses', 'custom_price')
