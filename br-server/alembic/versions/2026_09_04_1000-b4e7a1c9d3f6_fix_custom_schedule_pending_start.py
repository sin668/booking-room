"""fix custom schedule pending_start

Revision ID: b4e7a1c9d3f6
Revises: a33171f2c2fb
Create Date: 2026-09-04 10:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b4e7a1c9d3f6'
down_revision: Union[str, None] = 'a33171f2c2fb'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 修复历史数据：定制排课（custom）此前恒存 in_progress，未区分「待开始」。
    # 现将开课日期(start_date)在未来的定制排课回填为 pending_start，与新逻辑
    # （_compute_schedule_status / schedule_status_scheduler 复用 resolve_course_* 公用方法）一致。
    # 仅触碰 custom：固定班课(fixed)必须恒为 in_progress，保证 C 端「仅 fixed+in_progress
    # 可预约/展示」的口径不被未开课课程破坏（见 _effective_start_date 的 fixed→None 设计）。
    # 幂等：WHERE 只命中 in_progress 且 start_date 在未来的定制排课，重跑无副作用。
    # 方言：日期比较沿用 add_schedule_status 迁移的 PostgreSQL（生产）语法。
    op.execute(
        "UPDATE course_schedules "
        "SET schedule_status = 'pending_start' "
        "WHERE schedule_type = 'custom' "
        "AND schedule_status = 'in_progress' "
        "AND start_date IS NOT NULL "
        "AND start_date > (NOW() AT TIME ZONE 'Asia/Shanghai')::date"
    )


def downgrade() -> None:
    # 反向：定制排课 pending_start 回退为 in_progress（本特性前定制排课从不为 pending_start）。
    op.execute(
        "UPDATE course_schedules "
        "SET schedule_status = 'in_progress' "
        "WHERE schedule_type = 'custom' "
        "AND schedule_status = 'pending_start'"
    )
