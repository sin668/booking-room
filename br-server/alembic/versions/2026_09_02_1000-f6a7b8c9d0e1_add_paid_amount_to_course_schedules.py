"""add_paid_amount_to_course_schedules

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-02 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'course_schedules',
        sa.Column(
            'paid_amount',
            sa.Numeric(precision=10, scale=2),
            nullable=True,
            comment='已支付金额：定制订单确认时从订单 total_price 记入，与定制每课时价格区分',
        ),
    )

    # 回填历史数据：由订单确认生成的定制排课，已支付金额取关联订单的 total_price
    op.execute(
        """
        UPDATE course_schedules cs
        SET paid_amount = b.total_price
        FROM bookings b
        WHERE cs.schedule_type = 'custom'
          AND cs.paid_amount IS NULL
          AND b.schedule_id = cs.id
        """
    )

    # 修正历史数据：此前误把订单已支付总额写入"定制每课时价格"，
    # 改为取课程固定班课排课的定制每课时价格（C 端下单时的计价来源）
    op.execute(
        """
        UPDATE course_schedules cs
        SET custom_price = COALESCE(src.custom_price, 0)
        FROM (
            SELECT DISTINCT ON (course_id) course_id, custom_price
            FROM course_schedules
            WHERE schedule_type = 'fixed'
            ORDER BY course_id, created_at ASC
        ) src
        WHERE cs.schedule_type = 'custom'
          AND cs.course_id = src.course_id
          AND EXISTS (SELECT 1 FROM bookings b WHERE b.schedule_id = cs.id)
        """
    )


def downgrade() -> None:
    op.drop_column('course_schedules', 'paid_amount')
