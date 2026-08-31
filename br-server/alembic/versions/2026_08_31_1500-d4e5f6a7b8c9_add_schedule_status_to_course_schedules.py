"""add_schedule_status_to_course_schedules

Revision ID: d4e5f6a7b8c9
Revises: b9c0d1e2f3a4
Create Date: 2026-08-31 15:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4e5f6a7b8c9'
down_revision: Union[str, None] = 'b9c0d1e2f3a4'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        'course_schedules',
        sa.Column(
            'schedule_status',
            sa.String(20),
            nullable=False,
            server_default='in_progress',
            comment='课程状态: in_progress=进行中, completed=已完成',
        ),
    )
    # 回填存量数据：当前日期(Asia/Shanghai) > 结课日期 → completed
    op.execute(
        "UPDATE course_schedules "
        "SET schedule_status = 'completed' "
        "WHERE end_date IS NOT NULL "
        "AND end_date < (NOW() AT TIME ZONE 'Asia/Shanghai')::date"
    )


def downgrade() -> None:
    op.drop_column('course_schedules', 'schedule_status')
